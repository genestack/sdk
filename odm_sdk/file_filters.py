from copy import deepcopy

from odm_sdk import FileTypes, GenestackException, Permissions, validate_constant


class FileFilter(object):
    """
    Base file filter class.
    """
    def __init__(self):
        self._dict = {}

    def get_dict(self):
        return deepcopy(self._dict)

    def AND(self, other):
        """
        Return a new filter combining this one with another one in an AND clause.

        :param other: other filter
        :type other: FileFilter
        :rtype: FileFilter
        """
        return AndFileFilter(self, other)

    def OR(self, other):
        """
        Return a new filter combining this one with another one in an OR clause.

        :param other: other filter
        :type other: FileFilter
        :rtype: FileFilter
        """
        return OrFileFilter(self, other)

    def __and__(self, other):
        return self.AND(other)

    def __or__(self, other):
        return self.OR(other)


class TypeFileFilter(FileFilter):
    """
    Filter to select files with a given file type.
    See :ref:`fileTypes` for a list of possible file types.
    """
    def __init__(self, file_type):
        super(TypeFileFilter, self).__init__()
        if not validate_constant(FileTypes, file_type):
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


class BelongsToDatasetFileFilter(FileFilter):
    """
    Same as :py:class:`~odm_sdk.file_filters.ChildrenFileFilter`
    but searches for files that belong to the specified dataset.
    """
    def __init__(self, file_accession):
        super(BelongsToDatasetFileFilter, self).__init__()
        self._dict.update({'datasetAccession': file_accession})


class ActualPermissionFileFilter(FileFilter):
    """
    Filter to select files for which the current user has a specific permission.
    See :ref:`permissions`.
    """
    def __init__(self, permission):
        super(ActualPermissionFileFilter, self).__init__()
        if not validate_constant(Permissions, permission):
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
        if not validate_constant(Permissions, permission):
            raise GenestackException("Invalid permission")
        self._dict.update({'permission': {'group': group, 'value': permission}})


class NotFileFilter(FileFilter):
    """
    Negation of another :py:class:`~odm_sdk.file_filters.FileFilter`
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
