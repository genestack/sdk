# -*- coding: utf-8 -*-

#
# Copyright (c) 2011-2015 Genestack Limited
# All Rights Reserved
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF GENESTACK LIMITED
# The copyright notice above does not evidence any
# actual or intended publication of such source code.
#
import datetime

from Exceptions import GenestackException


def xstr(arg):
    if arg is None:
        return None
    if isinstance(arg, basestring):
        return arg
    return str(arg)


class Metainfo(dict):
    """
    Python representation of metainfo.
    """

    NAME = 'genestack:name'
    DESCRIPTION = 'genestack:description'
    ACCESSION = 'genestack:accession'
    # METHOD =      'genestack.bio:method'
    ORGANIZATION = 'genestack:organization'
    CONTACT_PERSON = 'genestack:contactPerson'
    EXTERNAL_LINK = 'genestack:links'
    CREATION_DATE = 'genestack:dateCreated'

    YEAR = 'YEAR'
    MONTH = 'MONTH'
    WEEK = 'WEEK'
    DAY = 'DAY'
    HOUR = 'HOUR'
    MINUTE = 'MINUTE'
    SECOND = 'SECOND'
    MILLISECOND = 'MILLISECOND'

    def _add_value(self, key, value, type):
        self.setdefault(key, []).append({'type': type, 'value': xstr(value)})

    @staticmethod
    def _create_dict_with_type(type):
        return {'type': type}

    def add_string(self, key, value):
        self._add_value(key, value, 'string')

    def add_boolean(self, key, value):
        self._add_value(key, value, 'boolean')

    def add_integer(self, key, value):
        self._add_value(key, value, 'integer')

    def add_external_link(self, key, text, url, fmt=None):
        result = Metainfo._create_dict_with_type('externalLink')
        result['text'] = xstr(text)
        result['url'] = xstr(url)
        result['format'] = fmt
        self.setdefault(key, []).append(result)

    def add_person(self, key, name, phone=None, email=None):
        result = Metainfo._create_dict_with_type('person')
        result['name'] = xstr(name)
        result['phone'] = xstr(phone)
        result['email'] = xstr(email)
        self.setdefault(key, []).append(result)

    def add_organization(self, key, name, department=None, country=None, city=None, street=None,
                         postal_code=None, state=None, phone=None, email=None, url=None):
        result = Metainfo._create_dict_with_type('organization')
        result['name'] = xstr(name)
        result['department'] = xstr(department)
        result['country'] = xstr(country)
        result['city'] = xstr(city)
        result['street'] = xstr(street)
        result['postalCode'] = xstr(postal_code)
        result['state'] = xstr(state)
        result['phone'] = xstr(phone)
        result['email'] = xstr(email)
        result['url'] = xstr(url)
        self.setdefault(key, []).append(result)

    def add_time(self, key, value, unit):
        result = Metainfo._create_dict_with_type('time')
        result['value'] = xstr(value)
        result['unit'] = unit.upper()
        self.setdefault(key, []).append(result)

    def add_file_reference(self, key, value):
        result = Metainfo._create_dict_with_type('file')
        result['accession'] = xstr(value)
        self.setdefault(key, []).append(result)

    # This method takes time as returned from time.time() function.
    def add_date_time(self, key, time):
        date_time_format = '%Y-%m-%d %H:%M:%S'
        date_format = '%Y-%m-%d'
        result = Metainfo._create_dict_with_type('datetime')

        if isinstance(time, basestring):
            try:
                time = datetime.datetime.strptime(time, date_time_format)
            except ValueError:
                try:
                    time = datetime.datetime.strptime(time, date_format)
                except ValueError:
                    raise GenestackException('Unexpected datetime string format: %s, '
                                             'specify date in on of the next format: "%s", "%s"' % (time,
                                                                                                    date_time_format,
                                                                                                    date_format))

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

        result['date'] = xstr(milliseconds)
        self.setdefault(key, []).append(result)

    def get_string_value(self, key):
        values = self.get(key)
        if values is not None:
            if len(values) > 0:
                value = values[0].get('value')
                return xstr(value)
