from pymongo import MongoClient
from bson.objectid import ObjectId


class Storage:
    def __init__(self, connection_string):
        print('Connecting to MongoDB...:', connection_string)
        self.client = MongoClient(connection_string)
        self.db = self.client.crude
        self.models = self.db['_models']

    def create(self, model_name, data):
        collection = self.db[model_name]
        entry_id = collection.insert_one(data).inserted_id
        return str(entry_id)

    def read(self, model_name, entry_id):
        collection = self.db[model_name]
        entry = collection.find_one({'_id': ObjectId(entry_id)})
        return entry

    def update(self, model_name, entry_id, data):
        collection = self.db[model_name]
        result = collection.update_one({'_id': ObjectId(entry_id)}, {'$set': data})
        return {'affected': result.modified_count}

    def save(self, model_name, entry_id, data):
        collection = self.db[model_name]
        result = collection.replace_one({'_id': ObjectId(entry_id)}, data, upsert=True)
        return result.raw_result

    def delete(self, model_name, entry_id):
        collection = self.db[model_name]
        result = collection.delete_one({'_id': ObjectId(entry_id)})
        return {'affected': result.deleted_count}

    def find_relations(self, related_model_name, related_model_field, compound_id, limit=10):
        collection = self.db[related_model_name]
        query_expression = {related_model_field: compound_id}
        cursor = collection.find(query_expression).limit(limit)
        return cursor

    def find_all_ids(self, model_name, list_of_ids):
        collection = self.db[model_name]
        ids = [ObjectId(string_id) for string_id in list_of_ids]
        cursor = collection.find({'_id': {'$in': ids}})
        return cursor

    def browse(self, model_name, filter_expression, sort_doc, page_number=1, items_per_page=10):
        collection = self.db[model_name]
        skips = items_per_page * (page_number - 1)
        cursor = collection.find(filter_expression)
        if len(sort_doc) > 0:
            sort_list = [(field, direction) for field, direction in sort_doc.items()]
            cursor.sort(sort_list)
        cursor.skip(skips).limit(items_per_page)
        return cursor

    def get_count(self, model_name, query_expression):
        collection = self.db[model_name]
        return collection.count_documents(query_expression)

    def save_model(self, model_name, data):
        self.models.replace_one({'name': model_name}, data, upsert=True)

    def read_model(self, model_name):
        model = self.models.find_one({'name': model_name})
        return model

    def read_models(self, model_names):
        model = self.models.find({'name': {'$in': model_names}})
        return model

    def delete_model(self, model_name):
        self.models.delete_one({'name': model_name})
        return True

    def list_models(self):
        models = self.models.find()
        return models

    def get_all_model_names(self):
        models = self.models.find({}, {'name': 1})
        return [model['name'] for model in models]

    def get_search_and_display_fields(self, model_name):
        model = self.models.find_one({'name': model_name})
        search_fields = []
        display_fields = []
        if model and 'search_fields' in model:
            search_fields = model['search_fields']
        else:
            search_fields = [field['name'] for field in model['fields'] if field['type'] == 'text']

        if model and 'display_fields' in model:
            display_fields = model['display_fields']
        else:
            display_fields = [field['name'] for field in model['fields'] if 'hidden' not in field]

        return search_fields, display_fields

    def full_text_search(self, model_name, search_fields, projection_fields, search_term, limit):
        collection = self.db[model_name]
        search_expression = {'$text': {'$search': search_term}}
        projection = {field: 1 for field in projection_fields}
        projection['score'] = {'$meta': 'textScore'}
        cursor = collection.find(search_expression, projection).sort([('score', {'$meta': 'textScore'})]).limit(limit)
        return cursor

    def prefix_search(self, model_name, search_fields, projection_fields, search_term, limit):
        collection = self.db[model_name]
        # use regex to match search_term as a prefix
        if len(search_fields) > 1:
            search_expression = {'$or': [{field: {'$regex': '^' + search_term, '$options': 'i'}} for field in search_fields]}
        else:
            search_expression = {search_fields[0]: {'$regex': '^' + search_term, '$options': 'i'}}
        projection = {field: 1 for field in projection_fields}
        cursor = collection.find(search_expression, projection).limit(limit)
        return cursor

    def regex_search(self, model_name, search_fields, projection_fields, search_term, limit):
        collection = self.db[model_name]
        # use regex to match search_term anywhere in the field
        search_expression = {'$or': [{field: {'$regex':  search_term, '$options': 'i'}} for field in search_fields]}
        projection = {field: 1 for field in projection_fields}
        cursor = collection.find(search_expression, projection).limit(limit)
        return cursor

    def drop_indexes(self, model_name):
        collection = self.db[model_name]
        collection.drop_indexes()
        return True

    def set_wildcard_text_index(self, model_name):
        collection = self.db[model_name]
        collection.create_index([('$**', 'text')])
        return True

    def set_text_index(self, model_name, field_names):
        collection = self.db[model_name]
        index_map = [(field_name, 'text') for field_name in field_names]
        collection.create_index(index_map)
        return True

    def create_index(self, model_name, keys, options):
        collection = self.db[model_name]
        collection.create_index(keys, **options)

    def get_collection(self, model_name):
        return self.db[model_name]

    def create_collection(self, model_name):
        # check if collection already exists
        if model_name not in self.db.list_collection_names():
            self.db.create_collection(model_name)
        return True

    def set_required_fields(self, model_name, required_fields):
        field_rules = {'not': {'type': 'null'}, 'description': 'field "%s" is required'}
        properties = {field_name: field_rules for field_name in required_fields}
        validator_doc = {
            '$jsonSchema': {
                'required': required_fields,
                'properties': properties
            }
        }
        command = {
            'collMod': model_name,
            'validator': validator_doc,
            'validationLevel': 'strict',
            'validationAction': 'error'
        }
        print(command)
        result = self.db.command(command)
        print(result)
        return True

    def close(self):
        return self.client.close()