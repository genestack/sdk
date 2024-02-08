# coding=utf-8

from __future__ import print_function

import json
import os
import sys

import jsonschema


SCHEMAS_DIR = 'schemas'

VALIDATION_ERR_MSG = '''Template validation failed

 Offending instance:
{instance}

 Error message:
{message}
'''


def load_json(file_path, schema_name):
    """
    Loads the JSON specified by the given path and validates it against a JSON schema.

    JSON schema must be located in the `schemas` directory of the current module.

    :param file_path: path to the JSON file
    :type file_path: str
    :param schema_name: name of the JSON schema file
    :type schema_name: str
    :return: decoded JSON instance
    :rtype: dict
    """
    base_dir = os.path.dirname(__file__)
    schema_path = os.path.join(base_dir, SCHEMAS_DIR, schema_name)
    with open(file_path) as data_file, open(schema_path) as schema_file:
        data = json.load(data_file)
        schema = json.load(schema_file)
        try:
            jsonschema.validate(data, schema)
        except jsonschema.exceptions.ValidationError as exc:
            print(VALIDATION_ERR_MSG.format(**exc.__dict__), file=sys.stderr)
            sys.exit(1)
        return data
