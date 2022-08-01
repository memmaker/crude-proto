import importlib
import json
import os

from bson.json_util import dumps
from flask import render_template, request, flash, g, current_app
from jinja2 import Environment, BaseLoader
from werkzeug.utils import redirect

from persistence.storage import Storage


def get_extended_field_types():
    extended_field_types = []
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    python_path = os.path.abspath(os.path.join(current_script_dir, '../../fields'))
    template_path = os.path.abspath(os.path.join(current_script_dir, '../../templates/fields'))
    for filename in os.listdir(template_path):
        filename_without_extension = filename.split('.')[0]
        python_file_name = filename_without_extension + '.py'
        python_file = os.path.join(python_path, python_file_name)
        if os.path.isfile(python_file) and os.path.exists(python_file):
            extended_field_types.append(filename_without_extension)
    return extended_field_types


MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://crude:by_example@127.0.0.1:27017')
EXTENDED_FIELD_TYPES = get_extended_field_types()
VALID_FIELD_TYPES = EXTENDED_FIELD_TYPES + ['related', 'checkbox', 'color', 'date', 'datetime-local', 'email', 'file', 'hidden', 'image', 'month', 'number', 'password', 'range', 'tel', 'text', 'time', 'url', 'week']


def db():
    if not hasattr(g, 'db') or not isinstance(g.db, Storage):
        g.db = Storage(MONGODB_URI)
    return g.db


def render_tag(model, entry):
    compound_id = model['name'] + '/' + str(entry['_id'])
    label = render_entry(model, entry)
    return json.dumps({'searchBy': label, 'value': compound_id})


def render_entry(model, entry):
    field_names = model['display_fields']
    # map the names to the fields
    display_fields = [field for field in model['fields'] if field['name'] in field_names]
    render_context = {}
    if 'display_template' in model:
        display_template = model['display_template']
    else:
        display_template = ' '.join(['{{' + name + '}}' for name in field_names])

    for field in display_fields:
        field_name = field['name']
        if field_name in entry:
            if 'funcs' in field:
                render_context[field_name] = field['funcs'].json_to_short_string(field, entry)
            else:
                render_context[field_name] = str(entry[field_name])
    return render_template_from_string(display_template, render_context)


def render_template_from_string(template_string, render_context):
    rtemplate = Environment().from_string(template_string)
    return rtemplate.render(**render_context)


def is_api_call():
    return request.content_type and request.content_type.startswith('application/json')


def get_input(url_params=None):
    if is_api_call():
        return True, request.get_json() if not url_params else request.get_json() | url_params
    else:
        return False, request.form.to_dict() if not url_params else request.form.to_dict() | url_params


def get_input_func(**kwargs):
    return lambda: get_input(kwargs)


def sanitize_field(param, field_type):
    if param == '':
        return None
    try:
        if field_type == 'number':
            return float(param)
        elif field_type == 'checkbox':
            return bool(param)
        elif field_type == 'related':
            return list(map(lambda search_entry: search_entry['value'], json.loads(param)))
        else:
            return str(param)
    except:
        return None


def inject_field_functions(model):
    for field in model['fields']:
        field_type = field['type']
        if field_type in EXTENDED_FIELD_TYPES:
            class_name = field_type.capitalize()
            field_module = importlib.import_module('fields.' + field_type)
            if hasattr(field_module, class_name):
                class_object = getattr(field_module, class_name)
                field['funcs'] = class_object
    return model


def clean_string(input_string):
    cleaned_string = input_string.strip().lower()
    cleaned_string = cleaned_string.replace(' ', '_')
    cleaned_string = ''.join(filter(lambda x: x.isalnum() or x in '-_', cleaned_string))
    return cleaned_string


def sanitize(model, input_for_entry):
    # sanitize the input for the entry
    sanitized_input = {}
    for field in model['fields']:
        field_name = field['name']
        if field_name in input_for_entry:
            if 'funcs' in field:
                sanitized_input[field_name] = field['funcs'].input_to_json_value(field, input_for_entry)
            else:
                field_type = field['type']
                sanitized_input[field_name] = sanitize_field(input_for_entry[field_name], field_type)
    return sanitized_input


class Response:
    def __init__(self, input_func, db_func, db_view_func=None):
        self.success = False
        self.messages = []
        self.success_message = False
        self.redirect = ''
        self.template = ''
        self.input_func = input_func
        self.db_func = db_func
        self.db_view_func = db_view_func

    def execute(self):
        view_output_data = {}
        is_json, input_data = self.input_func()
        db_output_data = self.execute_db_call(input_data, self.db_func)
        if self.db_view_func:
            view_output_data = self.db_view_func(input_data | db_output_data)
        return self.send_response(is_json, db_output_data | view_output_data)

    def execute_db_call(self, input_data, db_func):
        try:
            db_response = db_func(input_data)
            self.success = True
            if self.success_message:
                self.messages.append(self.success_message)
            return db_response
        except Exception as e:
            print('DB Error: ' + str(e))
            self.success = False
            self.messages.append(str(e))
            return {}

    def send_response(self, is_json, output_data):
        if is_json:
            return dumps({'success': self.success, 'error': self.messages, 'data': output_data})
        for message in self.messages:
            flash(message)
        if self.redirect:
            return redirect(self.redirect)
        if self.template:
            return render_template(self.template, **output_data)
        return 'No page here', 404