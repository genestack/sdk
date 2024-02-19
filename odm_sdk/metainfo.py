import sys
from odm_sdk import (BooleanValue, DateTimeValue, DecimalValue, ExternalLink,
                              FileReference, GenestackException, IntegerValue, MemorySizeValue,
                              MetainfoScalarValue, Organization, Person,
                              Publication, StringValue)


class Metainfo(dict):
    """
    A Python representation of metainfo objects.
    """
    NAME = 'genestack:name'
    DESCRIPTION = 'genestack:description'
    ACCESSION = 'genestack:accession'
    ORGANIZATION = 'genestack:organization'
    CONTACT_PERSON = 'genestack:contactPerson'
    EXTERNAL_LINK = 'genestack:links'
    CREATION_DATE = 'genestack:dateCreated'
    PARENT_DICTIONARY = 'genestack.dictionary:parent'
    SOURCE_DATA = 'genestack:sourceData'
    DATA_TYPE = 'genestack:dataType'
    LAST_UPDATE_DATE = 'genestack:file.last-update'

    # Metainfo key for links from data files to their samples.
    SAMPLE_LINK = "genestack:sampleLink"
    # Metainfo key for links from the dataset with data files to the according study.
    STUDY_LINK = "genestack:studyLink"

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
        self.setdefault(key, []).append({'type': type, 'value': value})

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
        :type value: float | str
        :rtype: None
        """
        self.add_value(key, DecimalValue(value))

    def add_external_link(self, key, url, text=None, fmt=None):
        """
        Add an external link. The URL should point to a valid source file.
        The source should be either a publicly available file on the web, or a local file.
        Local files will be uploaded if imported with :py:class:`~odm_sdk.DataImporter`

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

        **Deprecated** since *0.32.0*, use compound metainfo keys instead
        """
        self._print_metainfo_type_deprecation_message('add_person')
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

        **Deprecated** since *0.32.0*, use compound metainfo keys instead
        """
        self._print_metainfo_type_deprecation_message('add_publication')
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

        **Deprecated** since *0.32.0*, use compound metainfo keys instead
        """
        self._print_metainfo_type_deprecation_message('add_organization')
        self.add_value(key, Organization(name, department, country, city, street,
                                         postal_code, state, phone, email, url))

    def add_time(self, key, value, unit):
        """
        Add a time value (like an age, or the duration of an experiment for example).

        The value can be any number, supplied with a unit from a controlled vocabulary.

        The time unit should be one of the following:
            :py:attr:`~odm_sdk.Metainfo.YEAR`,
            :py:attr:`~odm_sdk.Metainfo.MONTH`,
            :py:attr:`~odm_sdk.Metainfo.WEEK`,
            :py:attr:`~odm_sdk.Metainfo.DAY`,
            :py:attr:`~odm_sdk.Metainfo.HOUR`,
            :py:attr:`~odm_sdk.Metainfo.MINUTE`,
            :py:attr:`~odm_sdk.Metainfo.SECOND`,
            :py:attr:`~odm_sdk.Metainfo.MILLISECOND`

        :param key: key
        :type key: str
        :param: number of units as float
        :type value: float | str
        :param unit: unit
        :type unit: str
        :rtype: None

        **Deprecated** since *0.32.0*, use compound metainfo keys instead
        """
        self._print_metainfo_type_deprecation_message('add_time')
        result = Metainfo._create_dict_with_type('time')
        result['value'] = value
        result['unit'] = unit.upper()
        self.setdefault(key, []).append(result)

    def add_temperature(self, key, value, unit):
        """
        Add a temperature value.
        The value can be any number, supplied with a unit from a controlled vocabulary.


        The temperature unit should be one of the following:
            :py:attr:`~odm_sdk.Metainfo.CELSIUS`,
            :py:attr:`~odm_sdk.Metainfo.KELVIN`,
            :py:attr:`~odm_sdk.Metainfo.FAHRENHEIT`,

        :param key: key
        :type key: str
        :param value: number of units as float
        :type value: float | str
        :param unit: unit
        :type unit: str
        :rtype: None

        **Deprecated** since *0.32.0*, use compound metainfo keys instead
        """
        self._print_metainfo_type_deprecation_message('add_temperature')
        result = Metainfo._create_dict_with_type('temperature')
        result['value'] = value
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

    @classmethod
    def parse_metainfo_from_dict(cls, source_dict):
        """
        Parse a Java map representing a metainfo object and create a Python Client Metainfo.
        :param source_dict: Java map
        :type source_dict: dict
        :rtype: Metainfo
        """
        output = Metainfo()
        for key in source_dict:
            for scalar_value in map(cls._parse_scalar_value, source_dict[key]):
                output.add_value(key, scalar_value)
        return output

    @staticmethod
    def _parse_scalar_value(source_dict):
        java_type = source_dict['type']
        if java_type == BooleanValue._TYPE:
            return BooleanValue(source_dict['value'])
        elif java_type == DateTimeValue._TYPE:
            return DateTimeValue(source_dict['date'])
        elif java_type == ExternalLink._TYPE:
            return ExternalLink(
                source_dict['url'], source_dict['text'],
                source_dict.get('format')
            )
        elif java_type == IntegerValue._TYPE:
            return IntegerValue(source_dict['value'])
        elif java_type == DecimalValue._TYPE:
            return DecimalValue(source_dict['value'])
        elif java_type == MemorySizeValue._TYPE:
            return MemorySizeValue(source_dict['value'])
        elif java_type == Organization._TYPE:
            return Organization(
                source_dict['name'], source_dict['department'],
                source_dict['street'], source_dict['city'],
                source_dict['state'], source_dict['postalCode'],
                source_dict['country'], source_dict['email'],
                source_dict['phone'], source_dict['url']
            )
        elif java_type == Person._TYPE:
            return Person(source_dict['name'], source_dict['phone'], source_dict['email'])
        elif java_type == Publication._TYPE:
            return Publication(
                source_dict['title'], source_dict['authors'],
                source_dict['journalName'], source_dict['issueDate'],
                source_dict['identifiers'], source_dict['issueNumber'],
                source_dict['pages']
            )
        elif java_type == StringValue._TYPE:
            return StringValue(source_dict['value'])
        elif java_type == FileReference._TYPE:
            return FileReference(source_dict['accession'])
        else:
            # this is safer than raising an exception, since new metainfo types
            # can be added in Java (and some deprecated ones like physical values are not handled here)
            return MetainfoScalarValue(source_dict)


    @staticmethod
    def _print_metainfo_type_deprecation_message(method_name):
        sys.stderr.write(
            "Method `%s` is deprecated. Use compound metainfo keys to store complex values "
            "(e.g. two separate keys: 'myKey/value' and 'myKey/unit').\n" % method_name
        )
