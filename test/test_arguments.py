#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import sys
from StringIO import StringIO
from argparse import Namespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from genestack_client import get_user, make_connection_parser
from genestack_client.settings.genestack_user import User


def test_parse_default_user():
    user = get_user(make_connection_parser().parse_args())
    expected = User('tester@genestack.com', alias='tester',
                    host='localhost:8080', password='pwdTester123')
    assert user == expected


def test_parse_user_by_email():
    user = get_user(make_connection_parser().parse_args(['-u', 'tester@genesteck.com']))
    expected = User('tester@genesteck.com', alias='tester@genesteck.com',
                    host='platform.genestack.org')
    assert user == expected


def test_parse_default():
    parser = make_connection_parser()
    args = parser.parse_args()
    expected = Namespace(debug=False, host=None, pwd=None, show_logs=False, user=None)
    assert args == expected


def test_password_without_user(capsys):
    parser = make_connection_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(['-p', 'dumy_token'])

    # Emulate output of parser.error(message)
    f = StringIO()
    parser.print_usage(file=f)
    f.write('test_arguments.py: error: Password should not be specified without user\n')
    expected = f.getvalue()

    out, err = capsys.readouterr()
    assert err == expected


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'short', __file__])
