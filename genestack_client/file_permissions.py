# -*- coding: utf-8 -*-
_JAVA_PKG = "com.genestack.file"

FILE_ACCESS = _JAVA_PKG + "access"
FILE_READ_CONTENT = _JAVA_PKG + "readContent"
FILE_WRITE = _JAVA_PKG + "write"
FILE_CLONE_DATA = _JAVA_PKG + "cloneData"


def is_permission(permission_str):
    permissions = {v for k, v in globals().iteritems() if (not k.startswith("_") and isinstance(v, basestring))}
    return permission_str in permissions
