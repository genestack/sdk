#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script adds permissions to existing users.
# It requires tsv file groups_and_users.tsv to be present in the same directory as this script.
# groups_and_users.tsv should contain lines of the next format: groups, separated by commas,
# and users, separated by commas.
# Groups and users should be separated by tabs.

# Same groups may be repeated several times on different lines.

# For example:
# MANAGE_ORGANIZATION,MANAGE_GROUPS,MANAGE_TEMPLATES,MANAGE_FACETS alice@alphacorp.com,suzy@alphacorp.com
# MANAGE_ORGANIZATION  bob@alphacorp.com

# See the full instruction at:
# https://genestack.atlassian.net/wiki/spaces/ODMP/pages/1143242753/How+to+create+groups+and+add+existing+users+to+them+via+python+scripts
from __future__ import print_function, unicode_literals


import sys

from odm_sdk.utils import make_connection_parser, get_connection
from odm_sdk.scripts.utils import colored, TsvReader, GREEN, RED


def get_permissions_from_odm(connection):
    return connection.application('genestack/usersadmin-api').invoke('getAvailableDomainPermissions')


def add_permissions(connection, email, permissions):
    return connection.application('genestack/usersadmin-api').invoke(
        'setUserDomainPermissions', email, permissions)


def read_data_for_updating_users(args):
    users_for_updating = []
    incorrect_rows = []
    rows_number = 0
    with TsvReader(args.file_with_users) as usersfile:
        for row in usersfile:
            rows_number += 1
            try:
                permissions, emails = row[0].strip(), row[1].strip()
                if len(permissions) == 0 or len(emails) == 0:
                    raise IndexError
            except IndexError:
                incorrect_rows.append(row)
                continue
            user_permissions = [permission.strip() for permission in permissions.split(",") if permission]

            users_for_updating += [
                {'email': email.strip(), 'permissions': user_permissions} for email in emails.split(",")
                if email
            ]

        incorrect_rows_number = len(incorrect_rows)
        if incorrect_rows_number > 0:
            print(colored("Error: each line should contain groups separated by comma and users' "
                          "emails separated by comma, groups and users should be separated by tab.",
                          RED))
            if rows_number != incorrect_rows_number:
                print(colored("Lines to correct:", RED))
                for incorrect_row in incorrect_rows:
                    print(colored(incorrect_row, RED))
            print(colored("FAILED: Correct data and rerun this script.", RED))
            sys.exit()
    return users_for_updating


def check_all_users_exist(connection, all_users_to_be_added):
    existing_users = connection.application('genestack/usersadmin-api').invoke('listUsers')
    existing_emails = {existing_user['email'] for existing_user in existing_users}
    non_existing_emails = {
        user['email'] for user in all_users_to_be_added
        if user['email'] not in existing_emails
    }
    return non_existing_emails


def check_all_permissions_id_exists_in_odm(connection, users_for_updating):
    permission_ids_in_odm = []
    for i in get_permissions_from_odm(connection):
        permission_ids_in_odm.append(i["id"])
    permission_ids_from_file = []
    for i in users_for_updating:
        for j in i["permissions"]:
            permission_ids_from_file.append(j)
    non_existing_permissions = []
    for i in permission_ids_from_file:
        if i not in permission_ids_in_odm:
            non_existing_permissions.append(i)
    return non_existing_permissions


def main():
    parser = make_connection_parser()
    parser.add_argument('--file_with_users', metavar='<file_with_users>',
                        default="permissions_and_users.tsv",
                        help='add permissions to existing users')
    connection = get_connection()
    args = parser.parse_args()
    users_for_updating = read_data_for_updating_users(args)

    non_existing_emails = check_all_users_exist(connection, users_for_updating)
    all_users_exist = len(non_existing_emails) == 0

    non_existing_permissions = check_all_permissions_id_exists_in_odm(connection, users_for_updating)
    all_permissions_exist = len(non_existing_permissions) == 0

    for user in users_for_updating:
        add_permissions(connection, user["email"], user["permissions"])

    if all_permissions_exist and all_users_exist:
        print(colored("Success", GREEN))
    else:
        if not all_permissions_exist:
            print(colored("Permissions %s don't exist" % non_existing_permissions, RED))
        if not all_users_exist:
            print(colored("Users %s don't exist" % non_existing_emails, RED))
        if not all_users_exist or not all_permissions_exist:
            print(colored("Create missed items and rerun this script with the same input file",
                          RED))


if __name__ == "__main__":
    main()
