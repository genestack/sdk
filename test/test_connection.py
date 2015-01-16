#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#


from urllib2 import URLError

import pytest

from genestack import Connection, GenestackException
import environment


'''
from genestack import Connection

from genestack.settings import get_args

conn = Connection(server_url = 'http://{}:8080/frontend/endpoint'.format(get_args().host))

print conn


res = conn.login('aaa', 'bbb')

print res.getcode(), res.geturl()
print res.info()

print '========'

res = conn.login('tester@genestack.com', 'pwdTester123')

print res.getcode(), res.geturl()
print res.info()'''

server_url = environment.server_url
wrong_url = 'http://localhost:9999/aaaaz'


def test_connection_to_wrong_url():
    with pytest.raises(URLError):
        connection = Connection(wrong_url)
        connection.login(environment.userPublic, environment.pwdPublic)


def test_login_positive():
    connection = Connection(server_url)
    connection.login(environment.userPublic, environment.pwdPublic)
    name = connection.application('shell').invoke('whoami')
    assert name == environment.userPublic, "Name does not match %s and  %s" % (name, environment.userPublic)


def test_open():
    connection = Connection(server_url)
    connection.login(environment.userPublic, environment.pwdPublic)
    connection.open('/')


def test_wrong_login():
    connection = Connection(server_url)
    with pytest.raises(GenestackException):
        connection.login("test", 'test')

    with pytest.raises(GenestackException):
        connection.login(environment.userPublic, environment.userPublic)

    with pytest.raises(GenestackException):
        connection.login(environment.pwdPublic, environment.pwdPublic)


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'short', __file__])
