# -*- coding: utf-8 -*-

from genestack_client import BioFileType, CoreFileType, GenestackPermission


class FileFilter(object):
    """
    Base file filter class.
    """
    def __init__(self):
        self._dict = {}

    def get_dict(self):
        return self._dict.copy()


class TypeFileFilter(FileFilter):
    """
    Filter to select files with a given file type. See :py:class:`~genestack_client.java_enums.CoreFileType` and
    :py:class:`~genestack_client.java_enums.BioFileType` for a list of possible file types.
    """
    def __init__(self, file_type):
        super(TypeFileFilter, self).__init__()
        full_type = BioFileType.get_full_name(file_type, False) or CoreFileType.get_full_name(file_type)
        self._dict = {'type': full_type}


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
    Filter to select files matching a given metainfo key-value pattern.
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

        self._dict = {'access': GenestackPermission.get_full_name(permission)}


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
        self._dict = {'permission': {'group': group, 'value': GenestackPermission.get_full_name(permission)}}


class NotFileFilter(FileFilter):
    """
    Negation of another :py:class:`~genestack_client.file_filters.FileFilter`
    """
    def __init__(self, other_filter):
        super(NotFileFilter, self).__init__()
        self._dict = {'not': other_filter.get_dict()}


class AndFileFilter(FileFilter):
    """
    "AND" combination of other file filters.
    """
    def __init__(self, *args):
        super(AndFileFilter, self).__init__()
        self._dict = {'and': [file_filter.get_dict() for file_filter in args]}


class OrFileFilter(FileFilter):
    """
    "OR" combination of other file filters.
    """
    def __init__(self, *args):
        super(OrFileFilter, self).__init__()
        self._dict = {'or': [file_filter.get_dict() for file_filter in args]}
