# -*- coding: utf-8 -*-

from genestack_client import BioFileType, CoreFileType, GenestackPermission, FrontendObject


class FileFilter(FrontendObject):

    _JAVA_CLASS_PREFIX = 'com.genestack.api.files.filters'


class TypeFileFilter(FileFilter):

    def __init__(self, file_type):
        super(TypeFileFilter, self).__init__()
        full_type = BioFileType.get_full_name(file_type, False) or CoreFileType.get_full_name(file_type)
        self.set_data({'type': full_type})


class MetainfoKeyValueFileFilter(FileFilter):
    def __init__(self, key, value):
        super(MetainfoKeyValueFileFilter, self).__init__()
        self.set_data({'key': key, 'value': value._data})


class OwnerFileFilter(FileFilter):
    def __init__(self, email):
        super(OwnerFileFilter, self).__init__()
        self.set_data({'owner': email})


class MetainfoValuePatternFileFilter(FileFilter):
    def __init__(self, key, value):
        super(MetainfoValuePatternFileFilter, self).__init__()
        self.set_data({'key': key, 'value': value})


class ChildrenFileFilter(FileFilter):
    def __init__(self, container, recursive=False):
        super(ChildrenFileFilter, self).__init__()
        self.set_data({'file': container, 'recursive': recursive})


class ContainsFileFilter(FileFilter):
    def __init__(self, file_accession):
        super(ContainsFileFilter, self).__init__()
        self.set_data({'contains': file_accession})


class ActualOwnerFileFilter(FileFilter):
    def __init__(self):
        super(ActualOwnerFileFilter, self).__init__()
        self.set_data({'owned': None})


class ActualPermissionFileFilter(FileFilter):
    def __init__(self, permission):
        super(ActualPermissionFileFilter, self).__init__()
        self.set_data({'access': GenestackPermission.get_full_name(permission)})


class FixedValueFileFilter(FileFilter):
    def __init__(self, value):
        super(FixedValueFileFilter, self).__init__()
        self.set_data({'fixed': value})


class HasInProvenanceFileFilter(FileFilter):
    def __init__(self, file_accession):
        super(HasInProvenanceFileFilter, self).__init__()
        self.set_data({'hasInProvenance': file_accession})


class PermissionFileFilter(FileFilter):
    def __init__(self, group, permission):
        super(PermissionFileFilter, self).__init__()
        self.set_data({'group': group, 'value': GenestackPermission.get_full_name(permission)})


class NotFileFilter(FileFilter):
    def __init__(self, other_filter):
        super(NotFileFilter, self).__init__()
        self.set_data({'not': other_filter.get_dict()})


class AndFileFilter(FileFilter):
    def __init__(self, first, second):
        super(AndFileFilter, self).__init__()
        self.set_data({'first': first, 'second': second})


class OrFileFilter(FileFilter):
    def __init__(self, first, second):
        super(OrFileFilter, self).__init__()
        self.set_data({'first': first, 'second': second})
