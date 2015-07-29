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
from datetime import date, datetime

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from genestack_client import Metainfo, GenestackException


@pytest.fixture
def metainfo():
    return Metainfo()


def test_add_string(metainfo):
    metainfo.add_string('key', "stringValue")
    assert metainfo == {'key': [{'type': 'string', 'value': "stringValue"}]}


def test_add_int(metainfo):
    metainfo.add_integer('key', 42)
    assert metainfo == {'key': [{'type': 'integer', 'value': '42'}]}


def test_add_bool(metainfo):
    metainfo.add_boolean('key', False)
    assert metainfo == {'key': [{'type': 'boolean', 'value': 'False'}]}, 'Value is not match'


def test_add_date(metainfo):
    day = date(year=1982, month=9, day=1)
    metainfo.add_date_time('key', day)
    assert metainfo == {'key': [{'type': 'datetime', 'date': '399686400000'}]}, 'Value is not match'


def test_add_datetime(metainfo):
    day = datetime(year=1982, month=9, day=1)
    metainfo.add_date_time('key', day)
    assert metainfo == {'key': [{'type': 'datetime', 'date': '399686400000'}]}, 'Value is not match'


def test_add_datetime_as_string(metainfo):
    metainfo.add_date_time('key', '1982-09-01')
    assert metainfo == {'key': [{'type': 'datetime', 'date': '399686400000'}]}, 'Value is not match'


def test_wrong_date(metainfo):
    with pytest.raises(GenestackException):
        metainfo.add_date_time('key', '01-09-1982')


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'short', __file__])
