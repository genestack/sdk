# -*- coding: utf-8 -*-
from genestack_client import GenestackException, is_file_type, is_permission


class FileFilter(object):
    """
    Base file filter class.
    """
    def __init__(self):
        self._dict = {}

    def get_dict(self):
        return self._dict.copy()

    @staticmethod
    def AND(*args):
        full_filter = FileFilter()
        full_filter._dict = {'and': [f.get_dict() for f in args]}
        return full_filter

    @staticmethod
    def OR(*args):
        full_filter = FileFilter()
        full_filter._dict = {'or': [f.get_dict() for f in args]}
        return full_filter


class TypeFileFilter(FileFilter):
    """
    Filter to select files with a given file type. See :py:class:`~genestack_client.java_enums.CoreFileType` and
    :py:class:`~genestack_client.java_enums.BioFileType` for a list of possible file types.
    """
    def __init__(self, file_type):
        super(TypeFileFilter, self).__init__()
        if not is_file_type(file_type):
            raise GenestackException("Invalid file type")
        self._dict = {'type': file_type}


class KeyValueFileFilter(FileFilter):
    """
    Filter to select files with a given metainfo key-value pair.
    """
    def __init__(self, key, value):
        super(KeyValueFileFilter, self).__init__()
        self._dict = {'keyValue': {'key': key, 'value': value}}


class OwnerFileFilter(FileFilter):
    """
    Filter to select files owned by a specific user.
    """
    def __init__(self, email):
        super(OwnerFileFilter, self).__init__()
        self._dict = {'owner': email}


class MetainfoValuePatternFileFilter(FileFilter):
    """
    Filter to select files matching a specific substring value for a metainfo key.
    """
    def __init__(self, key, value):
        super(MetainfoValuePatternFileFilter, self).__init__()
        self._dict = {'pattern': {'key': key, 'value': value}}


class ChildrenFileFilter(FileFilter):
    """
    Filter to select files that are the children or descendants of a given container.
    """
    def __init__(self, container, recursive=False):
        super(ChildrenFileFilter, self).__init__()
        self._dict = {'children': {'file': container, 'recursive': recursive}}


class ContainsFileFilter(FileFilter):
    """
    Filter to select containers that contain a given file.
    """
    def __init__(self, file_accession):
        super(ContainsFileFilter, self).__init__()
        self._dict = {'contains': file_accession}


class ActualOwnerFileFilter(FileFilter):
    """
    Filter to select files that are owned by the current user.
    """
    def __init__(self):
        super(ActualOwnerFileFilter, self).__init__()
        self._dict = {'owned': None}


class ActualPermissionFileFilter(FileFilter):
    """
    Filter to select files for which the current user has a specific permission.
    See :py:class:`~genestack_client.java_enums.GenestackPermission`.
    """
    def __init__(self, permission):
        super(ActualPermissionFileFilter, self).__init__()
        self._dict = {'access': permission}


class FixedValueFileFilter(FileFilter):
    """
    Fixed value filter (either ``True`` or ``False``).
    """
    def __init__(self, value):
        super(FixedValueFileFilter, self).__init__()
        self._dict = {'fixed': value}


class HasInProvenanceFileFilter(FileFilter):
    """
    Filter to select files that have a given file in their provenance graph.
    """
    def __init__(self, file_accession):
        super(HasInProvenanceFileFilter, self).__init__()
        self._dict = {'hasInProvenance': file_accession}


class PermissionFileFilter(FileFilter):
    """
    Filter to select files for which a specific group has a specific permission.
    See :py:class:`~genestack_client.java_enums.GenestackPermission`.
    """
    def __init__(self, group, permission):
        super(PermissionFileFilter, self).__init__()
        if not is_permission(permission):
            raise GenestackException("Invalid permission")
        self._dict = {'permission': {'group': group, 'value': permission}}


class NotFileFilter(FileFilter):
    """
    Negation of another :py:class:`~genestack_client.file_filters.FileFilter`
    """
    def __init__(self, other_filter):
        super(NotFileFilter, self).__init__()
        self._dict = {'not': other_filter.get_dict()}


class AndFileFilter(FileFilter):
    """
    "AND" combination of two file filters.
    """
    def __init__(self, first, second):
        super(AndFileFilter, self).__init__()
        self._dict = {'and': [first.get_dict(), second.get_dict()]}


class OrFileFilter(FileFilter):
    """
    "OR" combination of two file filters.
    """
    def __init__(self, first, second):
        super(OrFileFilter, self).__init__()
        self._dict = {'or': [first.get_dict(), second.get_dict()]}
