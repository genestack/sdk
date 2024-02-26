#!/usr/bin/env python3
# coding=utf-8

"""
Local script used to perform automated curation.
"""
from __future__ import print_function

import json
import sys

from odm_sdk import Application, FilesUtil, make_connection_parser, get_connection
from jsonschema import validate, ValidationError

RULES_SCHEMA = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'object_type': {'type': 'string',
                            'enum': ['sample', 'study',
                                     'library', 'preparation',
                                     'expression', 'variant', 'flow_cytometry']},
            'genestack_key': {
                'type': ['string', 'array'],
                # if `genestack_key` contains an array, it must be an array of 2 strings
                # (value key + unit key) for use in KeyWithUnitMapper
                'minItems': 2,
                'maxItems': 2,
                'items': {'type': 'string'}
            },
            'raw_keys': {
                'type': 'array',
                'items': {'type': 'string'}
            },
            'dictionary': {'type': 'string'},
            'rules': {
                'type': 'object',
                'additionalProperties': {
                    'type': ['array', 'string', 'null']
                }
            },
            'type': {
                'type': 'string'
            }
        },
        'additionalProperties': False,
        'required': ['genestack_key', 'object_type', 'raw_keys']
    }
}

DEFAULT_VERSION_MESSAGE = "Edited using curation script"


class CurationApplication(Application):
    APPLICATION_ID = "genestack/curation"

    def create_files(self, target_studies_accessions, overwrite=False,
                     dry_run=False, rules=None, new_version_message=None, publish_new_version=True):
        return self.invoke('createCurationFiles', target_studies_accessions,
                           overwrite, dry_run, rules, new_version_message, publish_new_version)


def main():
    parser = make_connection_parser()
    parser.add_argument('accessions', metavar='<accessions>', nargs='*',
                        help='Accession(s) of the study (or studies) to curate')
    parser.add_argument('--dry-run', action='store_true', help='Do not write any metainfo')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing curated keys')
    parser.add_argument('--rules', metavar='<rules_file>',
                        help='A JSON-formatted curation rules file')
    # make `publish_new_version = True` a default, allow overriding
    version_args = parser.add_mutually_exclusive_group()
    version_args.add_argument('--do-not-publish', action='store_false', dest='publish_new_version',
                              help='Do not publish any version, save changes to the draft version.')
    version_args.add_argument('--version-message', dest='new_version_message',
                              metavar='<new_version_message>', default=DEFAULT_VERSION_MESSAGE,
                              help='Set a version message to explain the reason for update. If not '
                                   'specified, the default message "{}" will be used.'.format(
                                  DEFAULT_VERSION_MESSAGE))

    arguments = parser.parse_args()

    if not arguments.accessions:
        print("You must specify a target accession(s) for curation")
        sys.exit(1)

    if arguments.rules is None:
        print("You must specify a path to curation rules file")
        sys.exit(1)

    if not arguments.new_version_message:
        print("New version message must not be blank if specified")
        sys.exit(1)

    print("Connecting to Genestack...")
    connection = get_connection(arguments)
    curation_app = CurationApplication(connection)
    files_util = FilesUtil(connection)

    with open(arguments.rules, 'r') as rules_file:
        rules = json.load(rules_file)
    try:
        validate(rules, RULES_SCHEMA)
    except ValidationError as e:
        print("Invalid JSON curation file: " + e.message)
        sys.exit(1)

    print("Creating and initializing automated curation file...")

    accessions = curation_app.create_files(arguments.accessions,
                                           arguments.overwrite,
                                           arguments.dry_run,
                                           rules,
                                           arguments.new_version_message,
                                           arguments.publish_new_version
                                           )

    for accession in accessions:
        print("Automated curation task started! (%s)" % accession)


if __name__ == "__main__":
    main()
