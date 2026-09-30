#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This script deletes files using DELETE manageData/data endpoint.
# Provide an accession of a study/template which needs to be deleted.

from __future__ import print_function, unicode_literals

import sys

import requests

from odm_sdk import GenestackBaseException
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
        response = connection.rest_request(
            'DELETE', '/manageData/default-released/data', params={'accessions': accession})
    except GenestackBaseException as e:
        print(colored(e, RED), file=sys.stderr)
        sys.exit(1)

    if response.status_code != requests.codes.accepted:
        print(colored("Deletion failed: HTTP {} {}".format(response.status_code, response.text),
                      RED), file=sys.stderr)
        sys.exit(1)
    print(colored("Success", GREEN))


if __name__ == "__main__":
    main()
