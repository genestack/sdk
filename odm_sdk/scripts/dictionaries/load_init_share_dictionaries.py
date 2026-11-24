#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script loads dictionaries which locations are supplied in a separate file.
# ODM shares each new dictionary with all users and starts its initialization.
# Example file with a list with dictionaries can be found in example-data directory.
# Those dictionaries which are supplied from the local machine should have a full path to their
# location in 'url' parameter or they should be present in the same directory as the script.
# The same works for the json file with dictionaries paths.
# Log in with an API token or an access token: the ODM REST API does not accept an email and a password.
# See the full instruction at:
# https://genestack.atlassian.net/wiki/spaces/ODMP/pages/945094729/How+to+load+init+and+share+a+dictionary+on+a+remote+host+by+executing+a+script+on+your+machine+CUT+prepared+for+outer+clients
import json

from odm_sdk import DictionaryUtil, FilesUtil, GenestackException
from odm_sdk.utils import get_connection, make_connection_parser

from odm_sdk.scripts.utils import colored, GREEN, BLUE, RED


def load_dictionary(connection, data, parent_dictionary=None, replace=False, metainfo=None):
    name = data['name']

    search_dictionaries = FilesUtil(connection).search_files(
        search_string=name,
        parameters={'type': FilesUtil.DICTIONARY_FILE, 'name': name, 'obsolete': 'false'})
    existing_accessions = [accession
                           for dictionary_file in search_dictionaries['files']
                           for accession in dictionary_file['accessions']]
    if existing_accessions and not replace:
        raise GenestackException(
            "Dictionary %s already exists with accessions: %s. Use --replace flag to overwrite it"
            % (colored(name, BLUE), ', '.join([colored(acc, GREEN) for acc in existing_accessions])))

    accession = DictionaryUtil(connection).create_dictionary(
        name=name,
        url=data['url'],
        term_type=data.get('term_type'),
        description=data.get('description'),
        metainfo=metainfo,
        parent_dictionary=parent_dictionary,
        replaces=existing_accessions,
    )
    print_result(accession, name, 'Dictionary')
    for old_accession in existing_accessions:
        print('Old version of dictionary %s / %s is marked as obsolete'
              % (colored(old_accession, GREEN), colored(name, BLUE)))
    return accession


def print_result(accession, name, type_name):
    print('Created %s %s / %s' % (type_name, colored(accession, GREEN), colored(name, BLUE)))


def main():
    try:
        args = get_arguments()
        connection = get_connection(args)
        with open(args.file_with_dictionaries, 'r') as data_file:
            dictionaries = json.load(data_file)
        for data in dictionaries:
            load_dictionary(connection, data, replace=args.replace)

    except Exception as e:
        print(colored(e, RED))


def get_arguments():
    parser = make_connection_parser()
    group = parser.add_argument_group('required arguments')
    group.add_argument('--file_with_dictionaries', metavar='<file_with_dictionaries>',
                       default="dictionaries.json",
                       help='dictionaries to load', required=True)
    parser.add_argument('--replace', action='store_true', default=False,
                        help='replace existing dictionaries')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
