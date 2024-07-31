#  Copyright (c) 2011-2024 Genestack Limited
#  All Rights Reserved
#  THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
#  The copyright notice above does not evidence any
#  actual or intended publication of such source code.

import contextlib
import re
import unittest
from argparse import Namespace
from io import StringIO

import pytest

from odm_sdk import get_user, make_connection_parser


class ArgumentsTest(unittest.TestCase):

    def test_parse_default(self):
        parser = make_connection_parser()
        args = parser.parse_args()
        expected = Namespace(debug=False, host=None, pwd=None, show_logs=False,
                             user=None, token=None, access_token=None)
        self.assertEqual(expected, args)

    def test_password_without_user(self):
        parser = make_connection_parser()
        error_message = StringIO()
        with pytest.raises(SystemExit) as se, contextlib.redirect_stderr(error_message):
            parser.parse_args(['-p', 'some_password'])

        # Test stderr output that was written by parser before raising error:

        # Expected output consist of usage section and line with filename and tested error
        expected_error_message = 'Password should not be specified without user'

        # Save parser.print_usage output to the variable
        f = StringIO()
        parser.print_usage(file=f)

        expected_output = f.getvalue()
        test_runner = re.search(r'^usage: (\S+)?', f.getvalue()).group(1)
        expected_output += '%s: error: %s\n' % (test_runner, expected_error_message)

        self.assertEqual(SystemExit, se.type)
        self.assertEqual(2, se.value.code)
        self.assertEqual(expected_output, error_message.getvalue())

    def test_token_and_user(self):
        parser = make_connection_parser()

        error_message = StringIO()
        with pytest.raises(SystemExit) as se, contextlib.redirect_stderr(error_message):
            parser.parse_args(['-u', 'some_user', '--token', 'some_token'])

        # Test stderr output that was written by parser before raising error:

        # Expected output consist of usage section and line with filename and tested error
        expected_error_message = 'Exactly one of token, access_token or user should be specified'

        # Save parser.print_usage output to the variable
        f = StringIO()
        parser.print_usage(file=f)

        expected_output = f.getvalue()
        test_runner = re.search(r'^usage: (\S+)?', f.getvalue()).group(1)
        expected_output += '%s: error: %s\n' % (test_runner, expected_error_message)

        self.assertEqual(SystemExit, se.type)
        self.assertEqual(2, se.value.code)
        self.assertEqual(expected_output, error_message.getvalue())

    def test_token_without_username(self):
        parser = make_connection_parser()
        some_token = 'some_token'
        args = parser.parse_args(['--token', some_token])
        user = get_user(args)
        self.assertEqual(some_token, user.token)


if __name__ == '__main__':
    unittest.main()
