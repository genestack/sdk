#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

from odm_sdk import get_connection, make_connection_parser, FilesUtil, SpecialFolders


def get_template_by_name(args):
    connection = get_connection(args)
    files_util = FilesUtil(connection)

    def find(name, parent):
        return files_util.find_application_page_file_by_name(name, parent)

    folders_to_search = [files_util.get_public_folder(),
                         files_util.get_special_folder(SpecialFolders.CREATED)
                         ]
    for folder in folders_to_search:
        accession = find(args.template_name, folder)
        if accession:
            return accession
    return None


def main():
    parser = make_connection_parser()
    parser.add_argument('--template-name', dest='template_name',
                        default='Default Template',
                        help='template_name')
    args = parser.parse_args()
    accession = get_template_by_name(args)
    print('Template with name "%s" has accession: %s' % (args.template_name, accession))


if __name__ == '__main__':
    main()
