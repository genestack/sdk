#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2018 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

from odm_sdk import Application, FilesUtil, SpecialFolders, get_connection, make_connection_parser


class GeneDictionaryLoaderApplication(Application):
    APPLICATION_ID = "genestack/gene-dictionary-loader-inception"

    def create_file(self, target_folder_accession, overwrite=False):
        return self.invoke('createGeneDictionaries', target_folder_accession, overwrite)


def main():
    args = get_args()
    connection = get_connection(args)
    loader = GeneDictionaryLoaderApplication(connection)
    fu = FilesUtil(connection)

    target_folder = fu.get_folder(
        fu.get_special_folder(SpecialFolders.CREATED),
        'Data samples',
        'Dictionaries',
        'Gene Dictionary Data',
        create=True)

    accession = loader.create_file(target_folder, overwrite=args.overwrite)
    print("Import started! (%s) Result folder: %s" % (accession, target_folder))


def get_args():
    parser = make_connection_parser()
    parser.add_argument('--target-folder', metavar='<accession>',
                        help=('Accession of the folder in which to perform the update.'
                              ' If not provided, a new folder `Gene Dictionary Data`'
                              ' will be created inside `Created Files`.'))

    parser.add_argument('--overwrite', action='store_true',
                        help='If this flag is set, '
                             'existing experiments in the target folder will be updated')

    return parser.parse_args()


if __name__ == "__main__":
    main()
