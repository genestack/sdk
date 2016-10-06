import json


class FrontendObject(object):

    _JAVA_CLASS_PREFIX = None

    def __init__(self):
        self._data = {}

    def set_data(self, dic):
        self._data = ['%s.%s' % (self._JAVA_CLASS_PREFIX, self.__class__.__name__), dic]

    def serialize(self):
        return json.dumps(self._data)


class MetainfoScalarValue(FrontendObject):

    _JAVA_CLASS_PREFIX = 'com.genestack.api.metainfo'


class StringValue(MetainfoScalarValue):

    def __init__(self, value):
        super(StringValue, self).__init__()
        self.set_data({'value': value})


class IntegerValue(MetainfoScalarValue):

    def __init__(self, value):
        super(IntegerValue, self).__init__()
        self.set_data({'value': int(value)})


class DecimalValue(MetainfoScalarValue):

    def __init__(self, value):
        super(DecimalValue, self).__init__()
        self.set_data({'value': str(value)})


class MemorySizeValue(MetainfoScalarValue):

    def __init__(self, value):
        super(MemorySizeValue, self).__init__()
        self.set_data({'value': int(value)})


class ExternalLink(MetainfoScalarValue):

    def __init__(self, text, url):
        super(ExternalLink, self).__init__()
        self.set_data({'text': text, 'url': url})


class FileReference(MetainfoScalarValue):

    def __init__(self, accession, direction):
        super(FileReference, self).__init__()
        self.set_data({
            'accession': accession,
            'direction': ['com.genestack.api.metainfo.FileReference$Direction', direction]
        })


class BooleanValue(MetainfoScalarValue):

    def __init__(self, value):
        super(BooleanValue, self).__init__()
        self.set_data({'value': bool(value)})