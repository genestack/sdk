#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This script deletes files using DELETE manageData/data endpoint.
# Provide an accession of a study/template which needs to be deleted.

from __future__ import print_function, unicode_literals

import argparse
import sys

import requests

from odm_sdk.scripts.token_auth import Headers, add_host_argument, add_token_arguments
from odm_sdk.scripts.utils import colored, GREEN, RED

MANAGE_DATA_PATH = 'api/v1/manage-data/data'


def main():
    parser = argparse.ArgumentParser(
        description='Delete a study or a template with all its content. '
                    'Authentication by either an API token or an access token is required.')
    add_host_argument(parser, 'URL of the instance a study/template is deleted from')
    add_token_arguments(parser, nargs=None)
    group = parser.add_argument_group('required arguments')
    group.add_argument('--accession', metavar='<accession>',
                       help='accession of a study/template to delete', required=True)
    args = parser.parse_args()
    headers = Headers(args)

    try:
        response = requests.delete(
            '{}/{}'.format(args.SERVER, MANAGE_DATA_PATH),
            headers=headers, params={'accessions': args.accession})
    except requests.exceptions.RequestException as e:
        print(colored(e, RED), file=sys.stderr)
        sys.exit(1)

    if response.status_code != requests.codes.accepted:
        print(colored("Deletion failed: HTTP {} {}".format(response.status_code, response.text),
                      RED), file=sys.stderr)
        sys.exit(1)
    print(colored("Success", GREEN))


if __name__ == "__main__":
    main()
