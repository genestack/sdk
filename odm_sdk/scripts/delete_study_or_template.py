#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  Copyright (c) 2011-2025 Genestack Limited
#  All Rights Reserved
#  THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
#  The copyright notice above does not evidence any
#  actual or intended publication of such source code.

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
        message = e
        if e.stack_trace is not None:
            p = re.compile(r"GenestackRestApiException: (.*?)(?=\n)")
            result = p.search(e.stack_trace)
            if result:
                message = result.group(1)
        print(colored(message, RED))


if __name__ == "__main__":
    main()
