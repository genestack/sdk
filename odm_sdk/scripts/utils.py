# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import csv
import sys

PY3 = sys.version_info > (3,)

BLUE = 34
GREEN = 32
RED = 31


def colored(text, color):
    if sys.platform == 'win32' or not sys.stdout.isatty():
        return text
    return '\033[%dm%s\033[0m' % (color, text)


class TsvReader():
    def __init__(self, filename):
        self.filename = filename
        self.dialect = csv.excel_tab
        self.encoding = 'utf-8'
        self.f = None
        self.reader = None

    def __enter__(self):
        if PY3:
            self.f = open(self.filename, 'rt',
                          encoding=self.encoding, newline='')
        else:
            self.f = open(self.filename, 'rb')
        self.reader = csv.reader(self.f, dialect=self.dialect)
        return self

    def __exit__(self, type_, value, traceback):
        self.f.close()

    def next(self):
        row = next(self.reader)
        if PY3:
            return row
        return [s.decode(self.encoding) for s in row]

    __next__ = next

    def __iter__(self):
        return self
