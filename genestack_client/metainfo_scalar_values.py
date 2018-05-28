import datetime
import os
from pprint import pformat
from urlparse import unquote, urlparse

from genestack_client import GenestackException


class MetainfoScalarValue(dict):
    _TYPE = None

    def _set_fields(self, value, stringify=True):
        if isinstance(value, dict):
            val = value.copy()
            val['type'] = self._TYPE
            if stringify:
                for key in val:
                    if not isinstance(val[key], dict):
                        val[key] = self._xstr(val[key])
            self.update(val)
        else:
            self.update({'type': self._TYPE, 'value': self._xstr(value)})

    def __init__(self, value):
        super(MetainfoScalarValue, self).__init__()
        self._set_fields(value)

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.get('value'))

    @staticmethod
    def _xstr(arg):
        """
        Convert the input argument to a string if it is not ``None``.

        :param arg: input object
        :type arg: object
        :return: string representation of the object
        :rtype: str
        """
        return str(arg) if arg is not None else None


class StringValue(MetainfoScalarValue):
    _TYPE = 'string'

    def get_string(self):
        return self._xstr(self.get('value'))


class BooleanValue(MetainfoScalarValue):
    _TYPE = 'boolean'

    def get_boolean(self):
        return bool(self.get('value'))

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.get_boolean())


class IntegerValue(MetainfoScalarValue):
    _TYPE = 'integer'

    def get_int(self):
        return int(self.get('value'))

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.get_int())


class MemorySizeValue(MetainfoScalarValue):
    _TYPE = 'memorySize'

    def get_int(self):
        return int(self.get('value'))

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.get_int())


class DecimalValue(MetainfoScalarValue):
    _TYPE = 'decimal'

    def get_decimal(self):
        return float(self.get('value'))

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.get_decimal())


class ExternalLink(MetainfoScalarValue):
    _TYPE = 'externalLink'

    def __init__(self, url, text=None, fmt=None):
        super(MetainfoScalarValue, self).__init__()
        if not text:
            text = os.path.basename(urlparse(unquote(url)).path)
        self._set_fields({'text': text, 'url': url, 'format': fmt})

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.get_url())

    def get_text(self):
        return self.get('text')

    def get_url(self):
        return self.get('url')

    def get_format(self):
        return self.get('format')


class FileReference(MetainfoScalarValue):
    _TYPE = 'file'

    def __init__(self, accession):
        super(MetainfoScalarValue, self).__init__()
        self._set_fields({'accession': accession})

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.get_accession())

    def get_accession(self):
        return self.get('accession')


class DateTimeValue(MetainfoScalarValue):
    _TYPE = 'datetime'

    _DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    _DATE_FORMAT = '%Y-%m-%d'

    def __init__(self, time):
        super(MetainfoScalarValue, self).__init__()
        milliseconds = self._parse_date_time(time)
        self._set_fields({'date': milliseconds})

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.get_date())

    @staticmethod
    def _can_be_cast_to_int(time_str):
        try:
            int(time_str)
            return True
        except ValueError:
            return False

    @classmethod
    def _parse_date_time(cls, time):
        if isinstance(time, basestring):
            if cls._can_be_cast_to_int(time):
                return int(time)
            try:
                time = datetime.datetime.strptime(time, cls._DATE_TIME_FORMAT)
            except ValueError:
                try:
                    time = datetime.datetime.strptime(time, cls._DATE_FORMAT)
                except ValueError:
                    raise GenestackException('Unexpected datetime string format: %s, '
                                             'specify date in on of the next format: "%s", "%s"' % (time,
                                                                                                    cls._DATE_TIME_FORMAT,
                                                                                                    cls._DATE_FORMAT))
        if isinstance(time, datetime.datetime):
            diff = time - datetime.datetime(1970, 1, 1)
            milliseconds = (diff.days * 24 * 60 * 60 + diff.seconds) * 1000 + diff.microseconds / 1000
        elif isinstance(time, datetime.date):
            diff = time - datetime.date(1970, 1, 1)
            milliseconds = diff.days * 24 * 60 * 60 * 1000
        elif isinstance(time, float):
            milliseconds = int(time * 1000)
        else:
            raise GenestackException('Unexpected datetime input type: %s' % type(time))
        return milliseconds

    def get_milliseconds(self):
        return float(self.get('date'))

    def get_date(self):
        return datetime.datetime.fromtimestamp(self.get_milliseconds()/1000.0)


class Person(MetainfoScalarValue):
    _TYPE = 'person'

    def __init__(self, name, phone=None, email=None):
        super(MetainfoScalarValue, self).__init__()
        self._set_fields({'name': name, 'phone': phone, 'email': email})

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               pformat(self.get_person()))

    def get_person(self):
        return {key: self.get(key) for key in {'name', 'phone', 'email'}}


class Publication(MetainfoScalarValue):
    _TYPE = 'publication'

    def __init__(self, title, authors, journal_name, issue_date, identifiers=None, issue_number=None, pages=None):
        super(MetainfoScalarValue, self).__init__()
        self._set_fields({
            'identifiers': identifiers if identifiers else {},
            'journalName': journal_name,
            'issueDate': issue_date,
            'title': title,
            'authors': authors,
            'issueNumber': issue_number,
            'pages': pages
        })

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               pformat(self.get_publication()))

    def get_publication(self):
        return {key: self.get(key) for key in {'identifiers', 'journalName', 'issueDate', 'title', 'authors',
                                               'issueNumber', 'pages'}}


class Organization(MetainfoScalarValue):
    _TYPE = 'organization'

    def __init__(self, name, department=None, country=None, city=None, street=None,
                 postal_code=None, state=None, phone=None, email=None, url=None):
        super(MetainfoScalarValue, self).__init__()
        self._set_fields({
            'name': name,
            'department': department,
            'country': country,
            'city': city,
            'street': street,
            'postalCode': postal_code,
            'state': state,
            'phone': phone,
            'email': email,
            'url': url
        })

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               pformat(self.get_organization()))

    def get_organization(self):
        return {key: self.get(key) for key in {'name', 'department', 'country', 'city', 'street',
                                               'postalCode', 'state', 'phone', 'email', 'url'}}

