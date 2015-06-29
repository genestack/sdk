#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

import sys
sys.path.insert(0, '../')

import pytest
from genestack import GenestackException, get_connection
from genestack.version import __version__


def test_current_version():
    connection = get_connection()
    assert connection.check_version(__version__) == None


def test_too_old():
    connection = get_connection()
    with pytest.raises(GenestackException):
        assert connection.check_version('0.0.1')


def test_future_version():
    connection = get_connection()
    assert connection.check_version('99.99.99') == 'You use version from future'


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'short', __file__])
