#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This script deletes files using wipeStudy method.
# Provide an accession of a study/template which needs to be deleted.

from __future__ import print_function, unicode_literals

import re
import sys

from odm_sdk import GenestackServerException
from odm_sdk.scripts.utils import colored, GREEN, RED
from odm_sdk.utils import make_connection_parser, get_connection


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
        message = e
        if e.stack_trace is not None:
            p = re.compile(r"GenestackRestApiException: (.*?)(?=\n)")
            result = p.search(e.stack_trace)
            if result:
                message = result.group(1)
        print(colored(message, RED), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
