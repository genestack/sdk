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
    """
    Convert argument to string if it is not None.

    :param arg:
    :type arg: object
    :return: string representation of item
    :rtype: str
    """
    return str(arg) if arg is not None else None


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
        """
        Add string value.

        :param key: key
        :type key: str
        :param value: string value
        :type value: str
        :rtype: None
        """
        self._add_value(key, value, 'string')

    def add_boolean(self, key, value):
        """
        Add boolean value.

        :param key: key
        :type key: str
        :param value: boolean value
        :type value: bool
        :rtype: None
        """
        self._add_value(key, value, 'boolean')

    def add_integer(self, key, value):
        """
        Add integer value.

        :param key: key
        :type key: str
        :param value: integer value
        :type value: int
        :rtype: None
        """
        self._add_value(key, value, 'integer')

    def add_external_link(self, key, text, url, fmt=None):
        """
        Add external link. Url should be to valid source.
        Source should be in public access in www or local file.
        Local files will be uploaded if import file with :py:class:`~genestack.DataImporter.DataImporter`

        :param key: key
        :type key: str
        :param text: url text for display purposes
        :type text: str
        :param fmt: format for unaligned read link
        :type fmt: dict
        :rtype: None
        """
        result = Metainfo._create_dict_with_type('externalLink')
        result['text'] = xstr(text)
        result['url'] = xstr(url)
        result['format'] = fmt
        self.setdefault(key, []).append(result)

    def add_person(self, key, name, phone=None, email=None):
        """
        Add person. Name is required. All other fields is optional.
        All fields will be visible for all who can access this metainfo.

        :param key: key
        :type key: str
        :param name: full name
        :type name: str
        :param phone: phone number
        :type phone: str
        :param email: contact email
        :type email: str
        :rtype: None
        """
        result = Metainfo._create_dict_with_type('person')
        result['name'] = xstr(name)
        result['phone'] = xstr(phone)
        result['email'] = xstr(email)
        self.setdefault(key, []).append(result)

    def add_organization(self, key, name, department=None, country=None, city=None, street=None,
                         postal_code=None, state=None, phone=None, email=None, url=None):
        """
        Add organization. Name is required. All other fields is optional.
        All fields will be visible for all who can access this metainfo.

        :param key: key
        :type key: str
        :param name: name
        :type name: str
        :param department: department
        :type department: str
        :param country: country
        :type country: str
        :param city: city
        :type city: str
        :param street: street
        :type street: str
        :param postal_code: postal/zip code
        :type postal_code: str
        :param state: state
        :type state: str
        :param phone: phone
        :type phone: str
        :param email: email
        :type email: str
        :param url: organisation web page
        :type url: str
        :rtype: None
        """
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
        """
        Add time value (for example age).

        value can be any number.

        Unit values can be one of next: :py:attr:`~Metainfo.YEAR`, :py:attr:`~Metainfo.MONTH`, :py:attr:`~Metainfo.WEEK`,
        :py:attr:`~Metainfo.DAY`, :py:attr:`~Metainfo.HOUR`, :py:attr:`~Metainfo.MINUTE`, :py:attr:`~Metainfo.SECOND`,
        :py:attr:`~Metainfo.MILLISECOND`

        :param key: key
        :type key: str
        :param unit: unit
        :type unit: str
        :rtype: None
        """
        result = Metainfo._create_dict_with_type('time')
        result['value'] = xstr(value)
        result['unit'] = unit.upper()
        self.setdefault(key, []).append(result)

    def add_file_reference(self, key, accession):
        """
        Add reference to other file.

        :param key: key
        :type key: str
        :param accession: accession for referenced file
        :type accession: str
        :rtype: None
        """
        result = Metainfo._create_dict_with_type('file')
        result['accession'] = xstr(accession)
        self.setdefault(key, []).append(result)

    def add_date_time(self, key, time):
        """
        Add date to metainfo.
        Time can be passed in one of the next formats:

         - :py:class:`datetime.datetime`
         - :py:class:`datetime.date`
         - :py:class:`str` in format: ``'%Y-%m-%d %H:%M:%S'`` or ``'%Y-%m-%d'``
         - number of seconds since the epoch as a floating point number

        :param key: key
        :type key: str
        :param value: time value
        :rtype: None
        """
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
