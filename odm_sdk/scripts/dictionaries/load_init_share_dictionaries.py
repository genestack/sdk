#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script loads, inits and shares dictionaries which locations are supplied in a separate file.
# Example file with a list with dictionaries can be found in example-data directory.
# Those dictionaries which are supplied from the local machine should have a full path to their
# location in 'url' parameter or they should be present in the same directory as the script.
# The same works for the json file with dictionaries paths.
# See the full instruction at:
# https://genestack.atlassian.net/wiki/spaces/ODMP/pages/945094729/How+to+load+init+and+share+a+dictionary+on+a+remote+host+by+executing+a+script+on+your+machine+CUT+prepared+for+outer+clients
import json

from odm_sdk import (DataImporter, FilesUtil,
                              GenestackException, GenestackServerException,
                              Metainfo, ShareUtil, SpecialFolders)
from odm_sdk.utils import get_connection, make_connection_parser

from odm_sdk.scripts.utils import colored, GREEN, BLUE, RED


def load_dictionary(connection, data, parent_dictionary=None, replace=True,
                    reuse_old_version=False, metainfo=None):

    if metainfo:
        metainfo.add_string(Metainfo.DESCRIPTION, data.get('description'))
    else:
        metainfo = data.get('metainfo', Metainfo())
        metainfo.add_string(Metainfo.DESCRIPTION, data.get('description'))

    name = data['name']
    url = data['url']
    term_type = data.get('term_type')

    fu = FilesUtil(connection)
    parent = fu.get_folder(
        fu.get_special_folder(SpecialFolders.CREATED),
        'Data samples',
        'Dictionaries',
        create=True)

    di = DataImporter(connection)
    old_dictionary_version = fu.find_file_by_name(name, parent=parent)
    if old_dictionary_version:
        if replace:
            print('Old version of dictionary %s / %s is removed'
                  % (colored(old_dictionary_version, GREEN), colored(name, BLUE)))
            fu.mark_obsolete(old_dictionary_version)
            fu.unlink_file(old_dictionary_version, parent)
        else:
            if reuse_old_version:
                print('Dictionary %s / %s already exists and will be reused'
                      % (colored(old_dictionary_version, GREEN), colored(name, BLUE)))
                return old_dictionary_version
            raise GenestackException(
                "Dictionary %s / %s already exists, set replace=True to replace it"
                % (colored(old_dictionary_version, GREEN), colored(name, BLUE)))

    accession = di.create_dictionary(
        parent=parent,
        name=name,
        url=url,
        term_type=term_type,
        metainfo=metainfo,
        parent_dictionary=parent_dictionary
        )
    print_result(accession, name, 'Dictionary')
    return accession


def print_result(accession, name, type_name, started=False):
    print('%s %s %s / %s' % (
        'Created and started' if started else 'Created',
        type_name,
        colored(accession, GREEN), colored(name, BLUE)
    ))


def initialization(connection, accessions):
    try:
        FilesUtil(connection).initialize(accessions)
        print('Initialization of %s dictionaries started.' % len(accessions))
    except GenestackServerException:
        print(colored("Created dictionaries have not been initialized. "
                      "Re-run this script as public@genestack.com "
                      "in order to share them with everyone", RED))


def sharing(connection, accessions):
    try:
        all_users_group_accession = 'GSG000001'
        ShareUtil(connection).share_files_for_view(accessions, all_users_group_accession,
                                                   'public')
    except GenestackServerException:
        print(colored("Created dictionaries have not been shared. "
                      "Re-run this script as public@genestack.com "
                      "in order to share them with everyone", RED))


def main():
    try:
        # load
        args = get_arguments()
        connection = get_connection(args)
        with open(args.file_with_dictionaries, 'r') as data_file:
            dictionaries = json.load(data_file)
        accessions = [load_dictionary(connection, data) for data in dictionaries]
        initialization(connection, accessions)
        sharing(connection, accessions)

    except Exception as e:
        print(colored(e, RED))


def get_arguments():
    parser = make_connection_parser()
    group = parser.add_argument_group('required arguments')
    group.add_argument('--file_with_dictionaries', metavar='<file_with_dictionaries>',
                       default="dictionaries.json",
                       help='dictionaries to load', required=True)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
