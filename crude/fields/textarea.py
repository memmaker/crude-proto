class Textarea:
    @staticmethod
    def input_to_json_value(field_definition, input_data):
        input_value = input_data[field_definition['name']]
        return str(input_value)

    @staticmethod
    def json_to_short_string(field_definition, entry, max_length=20):
        json_value = entry[field_definition['name']]
        max_length -= 3
        if len(json_value) > max_length:
            return json_value[0:max_length] + '(…)'
