#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from genestack_client import GenestackException, get_connection
from genestack_client.version import __version__


def test_current_version():
    connection = get_connection()
    assert connection.check_version(__version__) == ''


def test_too_old():
    connection = get_connection()
    with pytest.raises(GenestackException):
        assert connection.check_version('0.0.1')


def test_future_version():
    connection = get_connection()
    assert connection.check_version('99.99.99') == 'You use version from future'


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'short', __file__])
