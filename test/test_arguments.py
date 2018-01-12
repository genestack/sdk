#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import sys
from StringIO import StringIO
from argparse import Namespace

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from genestack_client import get_user, make_connection_parser
from genestack_client.settings.genestack_user import User, DEFAULT_HOST


def test_parse_default_user():
    user = get_user(make_connection_parser().parse_args())
    expected = User('tester@genestack.com', alias='tester',
                    host='localhost:8080', password='pwdTester123', token=None)
    assert user == expected


def test_parse_user_by_email():
    user = get_user(make_connection_parser().parse_args(['-u', 'tester@genesteck.com']))
    expected = User('tester@genesteck.com', alias='tester@genesteck.com',
                    host='platform.genestack.org')
    assert user == expected


def test_parse_default():
    parser = make_connection_parser()
    args = parser.parse_args()
    expected = Namespace(debug=False, host=None, pwd=None, show_logs=False,
                         user=None, token=None)
    assert args == expected


def test_password_without_user(capsys):
    parser = make_connection_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(['-p', 'some_password'])

    # Test stderr output that was written by parser before raising error:

    # Expected output consist of usage section and line with filename and tested error
    expected_error_message = 'Password should not be specified without user'

    # Save parser.print_usage output to the variable
    f = StringIO()
    parser.print_usage(file=f)

    expected_output = f.getvalue()
    expected_output += '%s: error: %s\n' % (
        os.path.basename(__file__), expected_error_message)

    # capture stdout and stderr that was produced during test
    # https://docs.pytest.org/en/latest/capture.html#accessing-captured-output-from-a-test-function
    out, err = capsys.readouterr()

    assert err == expected_output


def test_token_and_user(capsys):
    parser = make_connection_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(['-u', 'some_user', '--token', 'some_token'])

    # Test stderr output that was written by parser before raising error:

    # Expected output consist of usage section and line with filename and tested error
    expected_error_message = 'Token and user should not be specified together'

    # Save parser.print_usage output to the variable
    f = StringIO()
    parser.print_usage(file=f)

    expected_output = f.getvalue()
    expected_output += '%s: error: %s\n' % (
        os.path.basename(__file__), expected_error_message)

    # capture stdout and stderr that was produced during test
    # https://docs.pytest.org/en/latest/capture.html#accessing-captured-output-from-a-test-function
    out, err = capsys.readouterr()

    assert err == expected_output


def test_token_without_username():
    parser = make_connection_parser()
    some_token = 'some_token'
    args = parser.parse_args(['--token', some_token])
    user = get_user(args)
    assert user.token == some_token
    assert user.host == DEFAULT_HOST


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'short', __file__])
