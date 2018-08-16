#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from genestack_client import (Connection, GenestackAuthenticationException,
                              GenestackConnectionFailure, GenestackResponseError, get_user,
                              GenestackException)
from genestack_client.settings.genestack_user import _get_server_url

wrong_url = 'http://localhost:9999/aaaaz'

user = get_user()

server_url = _get_server_url(user.host)
user_login = user.email
user_pwd = user.password


def test_connection_to_wrong_url():
    with pytest.raises(GenestackConnectionFailure, match='<connection failed '):
        connection = Connection(wrong_url)
        connection.login(user_login, user_pwd)


def test_connection_404():
    with pytest.raises(GenestackResponseError,
                       match='<urlopen error 404 Client Error: Not Found for url:'):
        connection = Connection(server_url)
        connection.perform_request('/hhhh')


def test_login_by_password_positive():
    connection = Connection(server_url)
    connection.login(user_login, user_pwd)
    name = connection.application('genestack/signin').invoke('whoami')
    assert name == user_login, 'Name ("%s") does not match login ("%s")' % (name, user_login)


def test_login_negative():
    connection = Connection(server_url)
    with pytest.raises(GenestackAuthenticationException,
                       match='Fail to login with "test" to "localhost"'):
        connection.login('test', 'test')

    with pytest.raises(GenestackAuthenticationException):
        connection.login(user_login, user_login)

    with pytest.raises(GenestackAuthenticationException):
        connection.login(user_pwd, user_pwd)


def test_access_by_anonymous():
    connection = Connection(server_url)
    with pytest.raises(GenestackException,
                       match="Cannot parse content: No JSON object could be decoded"):
        connection.perform_request('/')


def test_method_forbidden_for_anonymous():
    connection = Connection(server_url)
    with pytest.raises(GenestackAuthenticationException) as e:
        connection.application('genestack/signin').invoke('whoami')


def test_time_measurement():
    connection = Connection(server_url)
    connection.login(user_login, user_pwd)
    response = connection.application('genestack/signin').get_response('whoami', trace=True)
    assert isinstance(response.trace, list)
    assert isinstance(response.elapsed_microseconds, int)
    assert response.elapsed_microseconds > 0


if __name__ == '__main__':
    pytest.main(['-v', '--tb', 'short', __file__])
