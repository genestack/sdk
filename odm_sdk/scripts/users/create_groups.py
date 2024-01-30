#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script creates new groups. It requires tsv file groups.tsv to be laying in the same directory
# as this script.
# groups.tsv should contain one group name per line, for example:
# group1
# group2

# See the full instruction at:
# https://genestack.atlassian.net/wiki/spaces/ODMP/pages/1143242753/How+to+create+groups+and+add+existing+users+to+them+via+python+scripts
from __future__ import print_function, unicode_literals


import sys

from odm_sdk.utils import make_connection_parser, get_connection

from utils import colored, TsvReader, GREEN, RED


def get_groups(connection):
    return connection.application('genestack/groupsadmin-api').invoke('getData')['groups']


def create_group(name, connection):
    return connection.application('genestack/groupsadmin-api').invoke('createGroup', name)


def check_group_exists(groupname, groups):
    for group in groups:
        if group['name'] == groupname:
            return group['accession']
    return None


def create_groups(groups_to_create, existing_groups, connection):
    for groupname in groups_to_create:
        accession = check_group_exists(groupname, existing_groups)
        if accession:
            print(colored("Group %s already exists with accession %s"
                          % (groupname, accession),
                          RED))
        else:
            group_properties = create_group(groupname, connection)
            print(colored("Group %s was created with accession %s"
                          % (groupname, group_properties['accession']), GREEN))


def read_groups(args):
    groups_to_create = []
    with TsvReader(args.file_with_groups) as groupsfile:
        for row in groupsfile:
            try:
                group = row[0].strip()
                if len(group) == 0:
                    raise IndexError
                groups_to_create.append(group)
            except IndexError:
                continue
        if len(groups_to_create) == 0:
            print(colored('Error: At least one group should present in the file groups.tsv',
                          RED))
            sys.exit()
        return groups_to_create


def main():
    parser = make_connection_parser()
    parser.add_argument('--file_with_groups', metavar='<file_with_groups>', default="groups.tsv",
                        help='create groups')
    connection = get_connection()
    args = parser.parse_args()

    existing_groups = get_groups(connection)
    groups_to_create = read_groups(args)
    create_groups(groups_to_create, existing_groups, connection)


if __name__ == "__main__":
    main()
