# -*- coding: utf-8 -*-


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from builtins import object


class Permissions(object):

    _JAVA_PKG = "com.genestack.file."

    FILE_ACCESS = _JAVA_PKG + "access"
    FILE_READ_CONTENT = _JAVA_PKG + "readContent"
    FILE_WRITE = _JAVA_PKG + "write"
    FILE_CLONE_DATA = _JAVA_PKG + "cloneData"
