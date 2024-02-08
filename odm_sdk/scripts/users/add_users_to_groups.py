#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script adds existing users to existing groups.
# It requires tsv file groups_and_users.tsv to be present in the same directory as this script.
# groups_and_users.tsv should contain lines of the next format: groups, separated by commas,
# and users, separated by commas.
# Groups and users should be separated by tabs.

# Same groups may be repeated several times on different lines.

# For example:
# group1,group2 alice@alphacorp.com,suzy@alphacorp.com
# group3  bob@alphacorp.com

# See the full instruction at:
# https://genestack.atlassian.net/wiki/spaces/ODMP/pages/1143242753/How+to+create+groups+and+add+existing+users+to+them+via+python+scripts
from __future__ import print_function, unicode_literals


import sys

from odm_sdk.utils import make_connection_parser, get_connection
from odm_sdk.scripts.utils import colored, TsvReader, GREEN, BLUE, RED


def get_groups(connection):
    return connection.application('genestack/groupsadmin-api').invoke('getData')['groups']


def add_group_member(connection, group_accession, email):
    return connection.application('genestack/groupsadmin-api').invoke(
        'addMemberToGroup', group_accession, email)


def add_user_to_groups(connection, user, non_existing_groups,
                       existing_group_names_and_user_emails, group_names_and_accessions):
    email = user.get("email")
    groups = user.get("groups")
    for group in groups:
        if group not in non_existing_groups:
            if email not in existing_group_names_and_user_emails[group]:
                add_group_member(connection, group_names_and_accessions[group], email)
                print(colored("Added user %s to group %s" % (email, group),
                              GREEN))
            else:
                print(colored("User %s already belongs to group %s" % (email, group),
                              BLUE))


def read_data_for_adding_users(args, unique_group_names):
    all_users_to_be_added = []
    incorrect_rows = []
    rows_number = 0
    with TsvReader(args.file_with_users) as usersfile:
        for row in usersfile:
            rows_number += 1
            try:
                groups, emails = row[0].strip(), row[1].strip()
                if len(groups) == 0 or len(emails) == 0:
                    raise IndexError
            except IndexError:
                incorrect_rows.append(row)
                continue
            user_groups = [group_name.strip() for group_name in groups.split(",") if group_name]
            unique_group_names.update(user_groups)

            all_users_to_be_added += [
                {'email': email.strip(), 'groups': user_groups} for email in emails.split(",")
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
    return all_users_to_be_added


def check_all_users_exist(connection, all_users_to_be_added):
    existing_users = connection.application('genestack/usersadmin-api').invoke('listUsers')
    existing_emails = {existing_user['email'] for existing_user in existing_users}
    non_existing_emails = {
        user['email'] for user in all_users_to_be_added
        if user['email'] not in existing_emails
    }
    return non_existing_emails


def check_all_groups_exist(connection, group_names_and_accessions,
                           existing_group_names_and_user_emails, unique_group_names):
    all_groups = get_groups(connection)
    for group in all_groups:
        group_names_and_accessions[group['name']] = group['accession']
        members_emails = [member['email'] for member in group['members']]
        existing_group_names_and_user_emails[group['name']] = members_emails
    return unique_group_names - set(group_names_and_accessions.keys())


def main():
    parser = make_connection_parser()
    parser.add_argument('--file_with_users', metavar='<file_with_users>',
                        default="groups_and_users.tsv",
                        help='add existing users to existing groups')
    connection = get_connection()
    args = parser.parse_args()

    unique_group_names = set()

    group_names_and_accessions = {}
    existing_group_names_and_user_emails = {}

    all_users_to_be_added = read_data_for_adding_users(args, unique_group_names)

    non_existing_emails = check_all_users_exist(connection, all_users_to_be_added)
    all_users_exist = len(non_existing_emails) == 0

    non_existing_groups = check_all_groups_exist(connection, group_names_and_accessions,
                                                 existing_group_names_and_user_emails,
                                                 unique_group_names)
    all_groups_exist = len(non_existing_groups) == 0

    for user in all_users_to_be_added:
        if user['email'] not in non_existing_emails:
            add_user_to_groups(connection, user, non_existing_groups,
                               existing_group_names_and_user_emails, group_names_and_accessions)

    if all_groups_exist and all_users_exist:
        print(colored("Success", GREEN))
    else:
        if not all_groups_exist:
            print(colored("Groups %s don't exist" % non_existing_groups, RED))
        if not all_users_exist:
            print(colored("Users %s don't exist" % non_existing_emails, RED))
        if not all_users_exist or not all_groups_exist:
            print(colored("Create missed items and rerun this script with the same input file",
                          RED))


if __name__ == "__main__":
    main()
