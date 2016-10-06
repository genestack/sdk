# -*- coding: utf-8 -*-

from genestack_client import BioFileType, CoreFileType, GenestackPermission
from copy import deepcopy


class FileFilter(object):
    def __init__(self):
        self._dict = {}

    def get_dict(self):
        return deepcopy(self._dict)


class TypeFileFilter(FileFilter):
    def __init__(self, file_type):
        super(TypeFileFilter, self).__init__()
        full_type = BioFileType.get_full_name(file_type, False) or CoreFileType.get_full_name(file_type)
        self._dict = {'type': full_type}


class KeyValueFileFilter(FileFilter):
    def __init__(self, key, value):
        super(KeyValueFileFilter, self).__init__()
        self._dict = {'keyValue': {'key': key, 'value': value}}


class OwnerFileFilter(FileFilter):
    def __init__(self, email):
        super(OwnerFileFilter, self).__init__()
        self._dict = {'owner': email}


class MetainfoValuePatternFileFilter(FileFilter):
    def __init__(self, key, value):
        super(MetainfoValuePatternFileFilter, self).__init__()
        self._dict = {'pattern': {'key': key, 'value': value}}


class ChildrenFileFilter(FileFilter):
    def __init__(self, container, recursive=False):
        super(ChildrenFileFilter, self).__init__()
        self._dict = {'children': {'file': container, 'recursive': recursive}}


class ContainsFileFilter(FileFilter):
    def __init__(self, file_accession):
        super(ContainsFileFilter, self).__init__()
        self._dict = {'contains': file_accession}


class ActualOwnerFileFilter(FileFilter):
    def __init__(self):
        super(ActualOwnerFileFilter, self).__init__()
        self._dict = {'owned': None}


class ActualPermissionFileFilter(FileFilter):
    def __init__(self, permission):
        super(ActualPermissionFileFilter, self).__init__()

        self._dict = {'access': GenestackPermission.get_full_name(permission)}


class FixedValueFileFilter(FileFilter):
    def __init__(self, value):
        super(FixedValueFileFilter, self).__init__()
        self._dict = {'fixed': value}


class HasInProvenanceFileFilter(FileFilter):
    def __init__(self, file_accession):
        super(HasInProvenanceFileFilter, self).__init__()
        self._dict = {'hasInProvenance': file_accession}


class PermissionFileFilter(FileFilter):
    def __init__(self, group, permission):
        super(PermissionFileFilter, self).__init__()
        self._dict = {'permission': {'group': group, 'value': GenestackPermission.get_full_name(permission)}}


class NotFileFilter(FileFilter):
    def __init__(self, other_filter):
        super(NotFileFilter, self).__init__()
        self._dict = {'not': other_filter.get_dict()}


class AndFileFilter(FileFilter):
    def __init__(self, *args):
        super(AndFileFilter, self).__init__()
        self._dict = {'and': [file_filter.get_dict() for file_filter in args]}


class OrFileFilter(FileFilter):
    def __init__(self, *args):
        super(OrFileFilter, self).__init__()
        self._dict = {'or': [file_filter.get_dict() for file_filter in args]}
