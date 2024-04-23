#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script shares a study with a group.

# See the full instruction at:
# https://genestack.atlassian.net/wiki/spaces/ODMP/pages/1262419987/How+to+share+a+study
from __future__ import print_function, unicode_literals

import re
from odm_sdk import GenestackServerException, GroupsUtil, ShareUtil
from odm_sdk.utils import make_connection_parser, get_connection

from odm_sdk.scripts.utils import colored, RED, GREEN


def share_study(share_params):
    connection = get_connection(share_params)
    study_accession = share_params.study_accession
    try:
        groups_util = GroupsUtil(connection)
        group_accession = groups_util.find_group_by_name(share_params.group_name)
        share_util = ShareUtil(connection)
        share_util.share_files_for_view(study_accession, group_accession)
        print(colored('Success', GREEN))
    except GenestackServerException as e:
        __handle_error_and_exit_with_code(e, study_accession)


def __handle_error_and_exit_with_code(e, study_accession):
    raw_to_custom_error_map = {
        r'File .* not found': f'Study with accession {study_accession} does not exist',
        r'Not enough user permissions to call method .*': 'Only the owner can share a study.'
    }

    for raw_err, custom_err in raw_to_custom_error_map.items():
        if re.search(raw_err, e.message):
            print(colored(custom_err, RED))
            exit(2)

    print(colored(e, RED))
    exit(1)


class ShareParams:
    # The class constructor is a subject to change, its parameters might be changed in the future.
    def __init__(
            self,
            host,
            study_accession,
            group_name,
            token=None,
            access_token=None,
            user=None,
            pwd=None,
            show_logs=False,
            debug=False
    ):
        self.host = host.rstrip('/')
        self.token = token
        self.access_token = access_token
        self.user = user
        self.pwd = pwd
        self.study_accession = study_accession
        self.group_name = group_name
        self.show_logs = show_logs
        self.debug = debug

    @classmethod
    def from_parsed_params(cls, args):
        return cls(
            host=args.host,
            study_accession=args.study_accession,
            group_name=args.group_name,
            token=args.token,
            access_token=args.access_token,
            user=args.user,
            pwd=args.pwd,
            show_logs=args.show_logs,
            debug=args.debug
        )


def main():
    parser = make_connection_parser()
    group = parser.add_argument_group('required arguments')
    group.add_argument('--study_accession', metavar='<study_accession>',
                       help='accession of study to share', required=True)
    group.add_argument('--group_name', metavar='<group_name>',
                       help='group name with which to share', required=True)
    args = parser.parse_args()
    share_study(ShareParams.from_parsed_params(args))


if __name__ == "__main__":
    main()
