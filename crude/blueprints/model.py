from flask import Blueprint, flash, url_for
import json
from flask import render_template

from werkzeug.utils import redirect

from blueprints.helper.common import get_input, VALID_FIELD_TYPES, db, clean_string

from blueprints.auth import auth_required

model_blueprint = Blueprint('model', __name__, url_prefix='/models')


@model_blueprint.route('/edit', methods=['GET'])
@model_blueprint.route('/edit/<model_name>', methods=['GET'])
@auth_required
def edit(model_name=None):
    model = db().read_model(model_name)
    if model and '_id' in model:
        del model['_id']
    render_context = {'model_name': model_name, 'model': json.dumps(model, indent=4)}
    return render_template('model/edit.html', **render_context)


@model_blueprint.route('/delete/<model_name>', methods=['GET'])
@auth_required
def delete(model_name):
    db().delete_model(model_name)
    flash('Model deleted: ' + model_name)
    return redirect(url_for('model.browse'))


@model_blueprint.route('/save', methods=['POST'])
@auth_required
def save():
    is_json, data = get_input()
    try:
        model_input = json.loads(data['model'])
    except json.decoder.JSONDecodeError as e:
        flash('Error: ' + str(e))
        return redirect(url_for('model.browse'))

    # check if the model is an array
    models = model_input
    if not isinstance(model_input, list):
        models = [model_input]

    for model in models:
        model_name = clean_string(model['name'])
        model['name'] = model_name
        for field in model['fields']:
            field['name'] = clean_string(field['name'])
            if 'type' not in field:
                field['type'] = 'text'
            elif field['type'] not in VALID_FIELD_TYPES:
                flash('Changed invalid field type (%s) to text: %s' % (field['type'], field['name']))
                field['type'] = 'text'
            elif field['type'] == 'related' and 'related_model' not in field:
                flash('ERROR: Missing "related_model" for field: %s' % field['name'])
                return redirect(url_for('model.browse'))
        if 'display_fields' not in model:
            model['display_fields'] = [field['name'] for field in model['fields']]
        required_fields = [field['name'] for field in model['fields'] if 'required' in field and field['required']]
        old_model = db().read_model(model_name)
        indexes_changed = old_model and old_model.get('indexes', []) != model.get('indexes', [])
        fts_indexes_changed = old_model and set(old_model.get('fts_index_fields', [])) != set(model.get('fts_index_fields', []))
        db().save_model(model_name, model)
        db().create_collection(model_name)
        if indexes_changed or fts_indexes_changed:
            flash('Indexes re-created for model: %s' % model_name)
            db().drop_indexes(model_name)
        else:
            flash('Indexes unchanged for model: %s' % model_name)
        if len(required_fields) > 0:
            db().set_required_fields(model_name, required_fields)
            flash('Required fields set for model: %s' % required_fields)
        index_fields = []
        text_index_fields = []
        use_wildcard_text_index = False
        if 'indexes' in model and indexes_changed:
            for index in model['indexes']:
                keys = index['keys'].items()
                options = index['options'] if 'options' in index else {}
                db().create_index(model_name, keys, options)
                index_fields += index['keys'].keys()
        if 'fts_index_fields' in model and fts_indexes_changed:
            text_index_fields = model['fts_index_fields']
            db().set_text_index(model_name, text_index_fields)
        elif fts_indexes_changed:
            use_wildcard_text_index = True
            db().set_wildcard_text_index(model_name)
        index_message = ' (idx: ' + ', '.join(index_fields) + ')' if len(index_fields) > 0 else ' (no index!)' if indexes_changed else ''
        text_index_message = ' (wildcard fts index)' if use_wildcard_text_index else ' (fts-idx: ' + ', '.join(text_index_fields) + ')' if fts_indexes_changed else ''
        flash('Model saved: ' + model_name + index_message + text_index_message)
    return redirect(url_for('model.browse'))


@model_blueprint.route('/browse', methods=['GET'])
@auth_required
def browse():
    models = db().list_models()
    render_context = {'models': models}
    return render_template('model/browse.html', **render_context)

