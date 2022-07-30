from flask import Blueprint, url_for, request, render_template, g, flash
import json
import math
from bson.objectid import ObjectId
from bson.json_util import dumps
from blueprints.helper.common import db

from blueprints.helper.common import sanitize, Response, get_input_func, get_input, render_entry, inject_field_functions

from blueprints.auth import auth_required

entry_blueprint = Blueprint('entry', __name__, url_prefix='/entries')


def get_doc_and_page_count(model_name, query, items_per_page=10):
    count = db().get_count(model_name, query)
    return count, math.ceil(count / items_per_page)


@entry_blueprint.route('/edit/<model_name>', methods=['GET'])
@entry_blueprint.route('/edit/<model_name>/<entry_id>', methods=['GET'])
@auth_required
def edit(model_name, entry_id=None):
    model = db().read_model(model_name)
    entry = db().read(model_name, entry_id) if entry_id else False
    model = inject_field_functions(model)
    model, entry = resolve_related(model, entry)
    render_context = {'model_name': model['name'], 'model': model, 'entry': entry, 'entry_id': entry_id if entry_id else str(ObjectId())}
    return render_template('entry/edit.html', **render_context)


@entry_blueprint.route('/save/<model_name>/<entry_id>', methods=['POST'])
@auth_required
def save(model_name, entry_id):
    input_func = get_input_func(model_name=model_name, entry_id=entry_id)
    res = Response(input_func, save_db_func)
    res.redirect = url_for('entry.browse', model_name=model_name)
    return res.execute()


def save_db_func(input_data):
    model_name = input_data['model_name']
    entry_id = input_data['entry_id']
    database = db()
    model = database.read_model(model_name)
    model = inject_field_functions(model)
    sanitized_data = sanitize(model, input_data)
    return database.save(model_name, entry_id, sanitized_data)


@entry_blueprint.route('/read/<model_name>/<entry_id>', methods=['GET'])
@auth_required
def read(model_name, entry_id):
    input_func = get_input_func(model_name=model_name, entry_id=entry_id)
    res = Response(input_func, read_db_func, read_view_data)
    res.template = 'entry/read.html'
    return res.execute()


def read_db_func(input_data):
    return {'entry': db().read(input_data['model_name'], input_data['entry_id'])}


def read_view_data(input_data):
    model_name = input_data['model_name']
    entry_id = input_data['entry_id']
    entry = input_data['entry']
    model = db().read_model(model_name)
    model = inject_field_functions(model)
    model, entry = resolve_related(model, entry)
    related_entries = resolve_foreign_relations(model, entry_id)
    view_data = {'model_name': model_name, 'model': model, 'entry': entry, 'related_entries': related_entries}
    return view_data


@entry_blueprint.route('/delete/<model_name>/<entry_id>', methods=['GET'])
@auth_required
def delete(model_name, entry_id):
    input_func = get_input_func(model_name=model_name, entry_id=entry_id)
    res = Response(input_func, delete_db_func)
    res.redirect = url_for('entry.browse', model_name=model_name)
    res.success_message = 'Deleted %s/%s' % (model_name, entry_id)
    return res.execute()


def delete_db_func(input_data):
    #print('delete_db_func: ', input_data)
    return db().delete(input_data['model_name'], input_data['entry_id'])


@entry_blueprint.route('/browse/<model_name>', methods=['GET'])
@entry_blueprint.route('/browse/<model_name>/<int:page_number>', methods=['GET'])
@auth_required
def browse(model_name, page_number=1):
    input_func = get_input_func(
        model_name=model_name,
        page_number=page_number,
        filter_args=request.args.get('f', '{}')
    )
    res = Response(input_func, browse_db_func, browse_view_data)
    res.template = 'entry/browse.html'
    return res.execute()


def browse_view_data(input_data):
    model = db().read_model(input_data['model_name'])
    model = inject_field_functions(model)
    return {'model': model}


def browse_db_func(input_data):
    #print('browse_db_func: ', input_data)
    sort_doc = {}
    try:
        filter_expression = json.loads(input_data['filter_args'])
        #print('filter_expression: ', filter_expression)
        if 'sort' in filter_expression:
            sort_doc = filter_expression['sort']
            del filter_expression['sort']
    except json.decoder.JSONDecodeError as e:
        filter_expression = {}
        flash(str(e))
        #print('browse_db_func: ', str(e))

    entries = db().browse(input_data['model_name'], filter_expression, sort_doc, input_data['page_number'])
    doc_count, page_count = get_doc_and_page_count(input_data['model_name'], filter_expression)
    return {'filter_expression': input_data['filter_args'], 'doc_count': doc_count, 'entries': entries, 'page_count': page_count, 'current_page': input_data['page_number'], 'model_name': input_data['model_name']}


def execute_search(model_name, search_function):
    entries = []
    limit = request.args.get('limit', 10)
    search_fields, display_fields = db().get_search_and_display_fields(model_name)
    search_term = request.args.get('q', False)
    if search_term:
        model = db().read_model(model_name)
        entries = search_function(model_name, search_fields, display_fields, search_term, limit)
        entries = map(lambda entry: entry | {'_to_string': render_entry(model, entry)}, entries)
    return dumps({'success': True, 'entries': entries})


@entry_blueprint.route('/search/full-text/<model_name>', methods=['GET'])
@auth_required
def full_text_search(model_name):
    return execute_search(model_name, db().full_text_search)


@entry_blueprint.route('/search/prefix/<model_name>', methods=['GET'])
@auth_required
def prefix_search(model_name):
    return execute_search(model_name, db().prefix_search)


@entry_blueprint.route('/search/regex/<model_name>', methods=['GET'])
@auth_required
def regex_search(model_name):
    return execute_search(model_name, db().regex_search)


def resolve_foreign_relations(model, entry_id):
    if 'foreign_relations' not in model:
        return {}
    compound_id = model['name'] + '/' + str(entry_id)
    foreign_relations = model['foreign_relations']
    results = []
    # TODO: optimize this by grouping the calls by model_name
    for foreign_relation in foreign_relations:
        name = foreign_relation['name']
        database = db()
        related_entries = list(database.find_relations(foreign_relation['related_model'], foreign_relation['related_field'], compound_id))
        if len(related_entries) > 0:
            related_model = database.read_model(foreign_relation['related_model'])
            related_model = inject_field_functions(related_model)
            results.append({
                'name': name,
                'related_model': related_model,
                'entries': related_entries
            })
    return results


def resolve_related_models(model):
    related_models_to_field_map = {field['related_model']: idx for idx, field in enumerate(model['fields']) if field['type'] == 'related' and field['related_model']}
    related_models = db().read_models(list(related_models_to_field_map.keys()))
    for related_model in related_models:
        related_model_name = related_model['name']
        field_index = related_models_to_field_map[related_model_name]
        model['fields'][field_index]['related_model'] = related_model
    return model


def resolve_related(model, entry=None):
    model = resolve_related_models(model)
    if not entry:
        return model, entry
    related_fields = [field for field in model['fields'] if field['type'] == 'related']
    info_map = {}
    related_entries_by_field = {}
    related_models_by_field = {}
    query_ids_per_model = {}
    models_by_name = {}
    for field in related_fields:
        if entry and entry[field['name']] and len(entry[field['name']]) > 0:
            related_model = field['related_model']
            models_by_name[related_model['name']] = related_model
            model_ids = [compound_id.split('/')[1] for compound_id in entry[field['name']]]
            info_map |= {compound_id: source_field for compound_id, source_field in map(lambda x: (x, field['name']), entry[field['name']])}
            if related_model['name'] not in query_ids_per_model:
                query_ids_per_model[related_model['name']] = []
            query_ids_per_model[related_model['name']] += model_ids
    # query the database for the related entries
    for model_name, ids in query_ids_per_model.items():
        related_model = models_by_name[model_name]
        entry_cursor = db().find_all_ids(model_name, ids)
        for related_entry in entry_cursor:
            entry_id = str(related_entry['_id'])
            related_entry['_id'] = entry_id
            compound_id = model_name + '/' + entry_id
            source_field = info_map[compound_id]
            related_models_by_field[source_field] = related_model
            if source_field not in related_entries_by_field:
                related_entries_by_field[source_field] = []
            related_entries_by_field[source_field].append(related_entry)
    for field in model['fields']:
        if field['type'] == 'related':
            entry[field['name']] = related_entries_by_field[field['name']] if field['name'] in related_entries_by_field else []
    return model, entry