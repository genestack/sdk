#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import os
import sys
from urllib2 import URLError

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from genestack_client import Connection, GenestackException
from genestack_client import get_user
from genestack_client.settings.genestack_user import _get_server_url


wrong_url = 'http://localhost:9999/aaaaz'


user = get_user()

server_url = _get_server_url(user.host)
user_login = user.email
user_pwd = user.password


def test_connection_to_wrong_url():
    with pytest.raises(URLError):
        connection = Connection(wrong_url)
        connection.login(user_login, user_pwd)


def test_login_positive():
    connection = Connection(server_url)
    connection.login(user_login, user_pwd)
    name = connection.application('genestack/signin').invoke('whoami')
    assert name == user_login, "Name does not match %s and  %s" % (name, user_login)


def test_open():
    connection = Connection(server_url)
    connection.login(user_login, user_pwd)
    connection.open('/')


def test_wrong_login():
    connection = Connection(server_url)
    with pytest.raises(GenestackException):
        connection.login("test", 'test')

    with pytest.raises(GenestackException):
        connection.login(user_login, user_login)

    with pytest.raises(GenestackException):
        connection.login(user_pwd, user_pwd)


def test_time_measurement():
    connection = Connection(server_url)
    connection.login(user_login, user_pwd)
    response = connection.application('genestack/signin').get_response('whoami', trace=True)
    assert isinstance(response.trace, list)
    assert isinstance(response.elapsed_microseconds, int)
    assert response.elapsed_microseconds > 0


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'short', __file__])
