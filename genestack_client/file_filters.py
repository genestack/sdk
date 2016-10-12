# -*- coding: utf-8 -*-
from genestack_client import GenestackException, JavaFileTypes, Permissions


class FileFilter(object):
    """
    Base file filter class.
    """
    def __init__(self):
        self._dict = {}

    def get_dict(self):
        return self._dict.copy()

    @staticmethod
    def AND(*filters):
        full_filter = FileFilter()
        full_filter._dict.update({'and': [f.get_dict() for f in filters]})
        return full_filter

    @staticmethod
    def OR(*filters):
        full_filter = FileFilter()
        full_filter._dict.update({'or': [f.get_dict() for f in filters]})
        return full_filter


class TypeFileFilter(FileFilter):
    """
    Filter to select files with a given file type.
    See :ref:`fileTypes` for a list of possible file types.
    """
    def __init__(self, file_type):
        super(TypeFileFilter, self).__init__()
        if not JavaFileTypes.is_file_type(file_type):
            raise GenestackException("Invalid file type")
        self._dict.update({'type': file_type})


class KeyValueFileFilter(FileFilter):
    """
    Filter to select files with a given metainfo key-value pair.
    """
    def __init__(self, key, value):
        super(KeyValueFileFilter, self).__init__()
        self._dict.update({'keyValue': {'key': key, 'value': value}})


class OwnerFileFilter(FileFilter):
    """
    Filter to select files owned by a specific user.
    """
    def __init__(self, email):
        super(OwnerFileFilter, self).__init__()
        self._dict.update({'owner': email})


class MetainfoValuePatternFileFilter(FileFilter):
    """
    Filter to select files matching a specific substring value for a metainfo key.
    """
    def __init__(self, key, value):
        super(MetainfoValuePatternFileFilter, self).__init__()
        self._dict.update({'pattern': {'key': key, 'value': value}})


class ChildrenFileFilter(FileFilter):
    """
    Filter to select files that are the children or descendants of a given container.
    """
    def __init__(self, container, recursive=False):
        super(ChildrenFileFilter, self).__init__()
        self._dict.update({'children': {'file': container, 'recursive': recursive}})


class ContainsFileFilter(FileFilter):
    """
    Filter to select containers that contain a given file.
    """
    def __init__(self, file_accession):
        super(ContainsFileFilter, self).__init__()
        self._dict.update({'contains': file_accession})


class ActualOwnerFileFilter(FileFilter):
    """
    Filter to select files that are owned by the current user.
    """
    def __init__(self):
        super(ActualOwnerFileFilter, self).__init__()
        self._dict.update({'owned': None})


class ActualPermissionFileFilter(FileFilter):
    """
    Filter to select files for which the current user has a specific permission.
    See :ref:`permissions`.
    """
    def __init__(self, permission):
        super(ActualPermissionFileFilter, self).__init__()
        if not Permissions.is_permission(permission):
            raise GenestackException("Invalid permission")
        self._dict.update({'access': permission})


class FixedValueFileFilter(FileFilter):
    """
    Fixed value filter (either ``True`` or ``False``).
    """
    def __init__(self, value):
        super(FixedValueFileFilter, self).__init__()
        self._dict.update({'fixed': value})


class HasInProvenanceFileFilter(FileFilter):
    """
    Filter to select files that have a given file in their provenance graph.
    """
    def __init__(self, file_accession):
        super(HasInProvenanceFileFilter, self).__init__()
        self._dict.update({'hasInProvenance': file_accession})


class PermissionFileFilter(FileFilter):
    """
    Filter to select files for which a specific group has a specific permission.
    See :ref:`permissions`.
    """
    def __init__(self, group, permission):
        super(PermissionFileFilter, self).__init__()
        if not Permissions.is_permission(permission):
            raise GenestackException("Invalid permission")
        self._dict.update({'permission': {'group': group, 'value': permission}})


class NotFileFilter(FileFilter):
    """
    Negation of another :py:class:`~genestack_client.file_filters.FileFilter`
    """
    def __init__(self, other_filter):
        super(NotFileFilter, self).__init__()
        self._dict.update({'not': other_filter.get_dict()})


class AndFileFilter(FileFilter):
    """
    "AND" combination of two file filters.
    """
    def __init__(self, first, second):
        super(AndFileFilter, self).__init__()
        self._dict.update({'and': [first.get_dict(), second.get_dict()]})


class OrFileFilter(FileFilter):
    """
    "OR" combination of two file filters.
    """
    def __init__(self, first, second):
        super(OrFileFilter, self).__init__()
        self._dict.update({'or': [first.get_dict(), second.get_dict()]})
