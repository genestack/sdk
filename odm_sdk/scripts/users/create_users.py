#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script creates new users. It requires tsv file users.tsv to be laying in the same directory
# as this script.
# users.tsv should contain user's email and name and optionally password separated by tab per line,
# for example:
# alice@alphacorp.com	Alice	pwdAlice123
# bob@alphacorp.com	Bob

# See the full instruction at:
# https://genestack.atlassian.net/wiki/spaces/ODMP/pages/1074823180/How+to+create+users+via+python+script
from __future__ import print_function, unicode_literals

import random
import re
import string
import sys
import time

from odm_sdk import GenestackServerException
from odm_sdk.utils import make_connection_parser, get_connection

from odm_sdk.scripts.utils import colored, TsvReader, GREEN, RED, BLUE


def create_user(connection, user):
    email = user['email']
    pwd = user['pwd']
    name = user['name']
    try:
        connection.application('genestack/usersadmin-api').invoke('createUser', email, pwd, name)
        print(colored("%s\t%s\t%s" % (email, pwd, name), GREEN))
    except GenestackServerException as e:
        p = re.compile('is already taken')
        result = p.search(e.message)
        if result is not None:
            print(colored("E-mail %s is already taken" % email, BLUE))
        else:
            raise e


def mkpasswd(length=8, digits=2, upper=2, lower=2):
    random.seed(time.time())
    password = (
            [random.choice(string.digits) for _ in range(digits)] +
            [random.choice(string.ascii_uppercase) for _ in range(upper)] +
            [random.choice(string.ascii_lowercase) for _ in range(lower)] +
            [random.choice(string.ascii_letters) for _ in range(length - digits - upper - lower)]
    )
    return "".join(random.sample(password, len(password)))


def read_users_from_file(args):
    users = []
    incorrect_rows = []
    with TsvReader(args.file_with_users) as usersfile:
        for row in usersfile:
            try:
                email = row[0].strip()
                name = row[1].strip()
                pwd = row[2].strip()
                if len(email) == 0 or len(name) == 0:
                    raise IndexError
                if len(pwd) == 0:
                    pwd = mkpasswd()
                users += [
                    {'email': email, 'pwd': pwd, 'name': name}
                ]
            except IndexError:
                incorrect_rows.append(row)
    if len(incorrect_rows) > 0:
        print(colored("Error: each line should contain email and user's name separated by "
                      "tab. \nReceived: %s. \nCorrect data and rerun script" % incorrect_rows,
                      RED))
        sys.exit()
    if len(users) == 0:
        print(colored('Error: At least one user should present in the file users.tsv',
                      RED))
        sys.exit()
    return users


def main():
    parser = make_connection_parser()
    parser.add_argument('--file_with_users', metavar='<file_with_users>', default="users.tsv",
                        help='create users')
    connection = get_connection()
    args = parser.parse_args()

    users = read_users_from_file(args)

    for user in users:
        create_user(connection, user)


if __name__ == "__main__":
    main()
