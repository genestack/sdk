#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script adds token to the current user.

from __future__ import print_function, unicode_literals
from odm_sdk import make_connection_parser, get_connection


def create_token(connection, token_name, token_content):
    return connection.application('genestack/profile-api').invoke('createApiTokenDirectly', token_name, token_content)


def get_args():
    parser = make_connection_parser()
    parser.add_argument('--token-name', default="Token", help='Token name for creation')
    parser.add_argument('--token-content', required=True, help='Exact token to be created')
    return parser.parse_args()


def main():
    args = get_args()
    connection = get_connection(args)
    create_token(connection, args.token_name, args.token_content)


if __name__ == "__main__":
    main()
