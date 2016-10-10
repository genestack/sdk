# -*- coding: utf-8 -*-

from genestack_client import (GenestackException, MetainfoScalarValue, StringValue, BooleanValue, IntegerValue,
                              MemorySizeValue, DecimalValue, ExternalLink, Person, Publication, Organization,
                              DateTimeValue, FileReference, xstr)


class Metainfo(dict):
    """
    A Python representation of metainfo objects.
    """
    NAME = 'genestack:name'
    DESCRIPTION = 'genestack:description'
    ACCESSION = 'genestack:accession'
    # METHOD =      'genestack.bio:method'
    ORGANIZATION = 'genestack:organization'
    CONTACT_PERSON = 'genestack:contactPerson'
    EXTERNAL_LINK = 'genestack:links'
    CREATION_DATE = 'genestack:dateCreated'
    PARENT_DICTIONARY = 'genestack.dictionary:parent'

    YEAR = 'YEAR'
    MONTH = 'MONTH'
    WEEK = 'WEEK'
    DAY = 'DAY'
    HOUR = 'HOUR'
    MINUTE = 'MINUTE'
    SECOND = 'SECOND'
    MILLISECOND = 'MILLISECOND'

    CELSIUS = 'CELSIUS'
    KELVIN = 'KELVIN'
    FAHRENHEIT = 'FAHRENHEIT'

    def _add_value(self, key, value, type):
        self.setdefault(key, []).append({'type': type, 'value': xstr(value)})

    @staticmethod
    def _create_dict_with_type(type):
        return {'type': type}

    def add_value(self, key, value):
        """
        Add a scalar value to a metainfo key.
        If adding to an existing key, the value will be appended to the list of existing values.
        :param key: key
        :type key: str
        :param value: value
        :type value: MetainfoScalarValue
        :rtype None:
        """
        if not isinstance(value, MetainfoScalarValue):
            raise GenestackException("Value is not an instance of `MetainfoScalarValue`")
        self.setdefault(key, []).append(value)

    def add_string(self, key, value):
        """
        Add a string value.

        :param key: key
        :type key: str
        :param value: string value
        :type value: str
        :rtype: None
        """
        self.add_value(key, StringValue(value))

    def add_boolean(self, key, value):
        """
        Add a boolean value.

        :param key: key
        :type key: str
        :param value: boolean value
        :type value: bool
        :rtype: None
        """
        self.add_value(key, BooleanValue(value))

    def add_integer(self, key, value):
        """
        Add an integer value.

        :param key: key
        :type key: str
        :param value: integer value
        :type value: int
        :rtype: None
        """
        self.add_value(key, IntegerValue(value))

    def add_memory_size(self, key, value):
        """
        Add a memory size in bytes.

        :param key: key
        :type key: str
        :param value: integer value
        :type value: int
        :rtype: None
        """
        self.add_value(key, MemorySizeValue(value))

    def add_decimal(self, key, value):
        """
        Add a decimal value.

        :param key: key
        :type key: str
        :param value: integer value
        :type value: float or str
        :rtype: None
        """
        self.add_value(key, DecimalValue(value))

    def add_external_link(self, key, url, text=None, fmt=None):
        """
        Add an external link. The URL should point to a valid source file.
        The source should be either a publicly available file on the web, or a local file.
        Local files will be uploaded if imported with :py:class:`~genestack_client.DataImporter`

        :param key: key
        :type key: str
        :param text: URL text for display purposes
        :type text: str
        :param fmt: format for an unaligned reads link
        :type fmt: dict
        :rtype: None
        """
        self.add_value(key, ExternalLink(url, text, fmt))

    def add_person(self, key, name, phone=None, email=None):
        """
        Add a person. The name is required, and all other fields are optional.
        All fields will be visible to anyone who has access to this metainfo object.

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
        self.add_value(key, Person(name, phone, email))

    def add_publication(self, key, title, authors, journal_name,
                        issue_date, identifiers=None, issue_number=None, pages=None):
        """
        Add a publication.
        All fields will be visible to anyone who has access to this metainfo object.

        :param key:
        :type key: str
        :param title: publication title
        :type title: str
        :param identifiers: publication identifiers
        :type identifiers: dict
        :param authors: publication authors
        :type authors: str
        :param journal_name: name of the journal containing this publication
        :type journal_name: str
        :param issue_date: journal issue date
        :type issue_date: str
        :param issue_number: journal issue number
        :type issue_number: str
        :param pages: pages in the journal issue
        :type pages: str
        :rtype: None
        """
        self.add_value(key, Publication(title, authors, journal_name, issue_date,
                                        identifiers, issue_number, pages))

    def add_organization(self, key, name, department=None, country=None, city=None, street=None,
                         postal_code=None, state=None, phone=None, email=None, url=None):
        """
        Add an organization. The name is required, and all other fields are optional.
        All fields will be visible to anyone who has access to this metainfo object.

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
        self.add_value(key, Organization(name, department, country, city, street,
                                         postal_code, state, phone, email, url))

    @DeprecationWarning
    def add_time(self, key, value, unit):
        """
        Add a time value (like an age, or the duration of an experiment for example).

        The value can be any number, supplied with a unit from a controlled vocabulary.

        The time unit should be one of the following:
            :py:attr:`~genestack_client.Metainfo.YEAR`,
            :py:attr:`~genestack_client.Metainfo.MONTH`,
            :py:attr:`~genestack_client.Metainfo.WEEK`,
            :py:attr:`~genestack_client.Metainfo.DAY`,
            :py:attr:`~genestack_client.Metainfo.HOUR`,
            :py:attr:`~genestack_client.Metainfo.MINUTE`,
            :py:attr:`~genestack_client.Metainfo.SECOND`,
            :py:attr:`~genestack_client.Metainfo.MILLISECOND`

        :param key: key
        :type key: str
        :param: number of units as float
        :type value: float | str
        :param unit: unit
        :type unit: str
        :rtype: None
        """
        result = Metainfo._create_dict_with_type('time')
        result['value'] = xstr(value)
        result['unit'] = unit.upper()
        self.setdefault(key, []).append(result)

    @DeprecationWarning
    def add_temperature(self, key, value, unit):
        """
        Add a temperature value.
        The value can be any number, supplied with a unit from a controlled vocabulary.


        The temperature unit should be one of the following:
            :py:attr:`~genestack_client.Metainfo.CELSIUS`,
            :py:attr:`~genestack_client.Metainfo.KELVIN`,
            :py:attr:`~genestack_client.Metainfo.FAHRENHEIT`,

        :param key: key
        :type key: str
        :param value: number of units as float
        :type value: float | str
        :param unit: unit
        :type unit: str
        :rtype: None
        """
        result = Metainfo._create_dict_with_type('temperature')
        result['value'] = xstr(value)
        result['unit'] = unit.upper()
        self.setdefault(key, []).append(result)

    def add_file_reference(self, key, accession):
        """
        Add a reference to another Genestack file.

        :param key: key
        :type key: str
        :param accession: accession of the file to reference
        :type accession: str
        :rtype: None
        """
        self.add_value(key, FileReference(accession))

    def add_date_time(self, key, time):
        """
        Add a date.
        The time parameter can be passed in one of the following formats:

         - :py:class:`datetime.datetime`
         - :py:class:`datetime.date`
         - :py:class:`str` in format: ``'%Y-%m-%d %H:%M:%S'`` or ``'%Y-%m-%d'``
         - number of seconds since the epoch as a floating point number

        :param key: key
        :type key: str
        :param time: time value
        :rtype: None
        """
        self.add_value(key, DateTimeValue(time))
