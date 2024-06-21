#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script deletes files using wipeStudy method.
# Provide an accession of a study/template which needs to be deleted.

from __future__ import print_function, unicode_literals

import re

from odm_sdk import GenestackServerException
from odm_sdk.utils import make_connection_parser, get_connection

from odm_sdk.scripts.utils import colored, GREEN, RED


def main():
    parser = make_connection_parser()
    group = parser.add_argument_group('required arguments')
    group.add_argument('--accession', metavar='<accession>',
                       help='accession of a study/template to delete', required=True)
    args = parser.parse_args()
    connection = get_connection(args)

    accession = args.accession
    try:
        connection.application('genestack/study-metainfo-editor').invoke('wipeStudy', accession)
        print(colored("Success", GREEN))
    except GenestackServerException as e:
        p = re.compile('File .* not found')
        result = p.search(e.message)
        if result is not None:
            print(colored("Study/template with accession %s does not exist" % accession,
                          RED))
        else:
            print(colored(e, RED))


if __name__ == "__main__":
    main()
