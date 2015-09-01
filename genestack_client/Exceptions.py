# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#

"""
Genestack exceptions.

The base class for Genestack exception is ``GenestackException``.
These classes should be used in your scripts instead of standard Python exceptions.
"""


class GenestackException(Exception):
    """
    This is the base Genestack exception class. It should be used instead of
    ``Exception`` to raise exceptions if something goes wrong.
    """
    pass


class GenestackServerException(GenestackException):
    """
    GenestackServerException class. Should be thrown when
    a server sends a response with an error message from Java code.
    :py:class:`GenestackServerException` is a subclass of the :py:class:`GenestackException`.
    """

    def __init__(self, message, path, post_data, stack_trace=None):
        """
        :param message: exception message
        :type message: str
        :param path: path after server URL of connection.
        :type path: str
        :param post_data: POST data (file or dict)
        :param stack_trace: server stack trace
        :type stack_trace: str
        """
        GenestackException.__init__(self, message)
        self.stack_trace = stack_trace
        self.path = path
        self.post_data = post_data

    def __str__(self):
        if isinstance(self.post_data, dict):
            return 'Got error "%s" at call of method "%s" of "%s"' % (
                self.message,
                self.post_data.get('method', '<unknown>'),
                self.path
            )
        else:
            # upload file
            return 'Got error "%s" at call of "%s"' % (
                self.message,
                self.path
            )
