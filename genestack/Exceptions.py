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

Contains GenestackException class with subclasses, that should be used
instead of Exception class to raise exceptions if something goes wrong.
"""


class GenestackException(Exception):
    """
    GenestackException class, that should be used instead of
    Exception class to raise exceptions if something goes wrong.
    """
    pass


class GenestackServerException(GenestackException):
    """
    GenestackServerException class, that should be thrown when
    Server sends response with error message from Java code.
    """

    def __init__(self, message, path, post_data, stack_trace=None):
        GenestackException.__init__(self, message)
        self.stack_trace = stack_trace
        self.path = path
        self.post_data = post_data

    def __str__(self):

        if isinstance(self.post_data, dict):
            return 'Got error "%s" at call of "%s" of "%s" application.' % (
                self.message,
                self.post_data.get('method', '<unknown>'),
                self.path.split('/', 3)[-1]
            )
        else:
            return self.message  # upload file
