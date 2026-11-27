import sys

from odm_sdk import BioMetaKeys, GenestackException, Metainfo

DICTIONARIES_PATH = '/api/v1/dictionaries'
TERM_TYPE_KEY = 'genestack.dictionary:termType'

# Metainfo keys that create_dictionary accepts, with the field of the request and the field of the value
_METAINFO_FIELDS = {
    Metainfo.NAME: ('name', 'value'),
    BioMetaKeys.DATA_LINK: ('url', 'url'),
    Metainfo.DESCRIPTION: ('description', 'value'),
    TERM_TYPE_KEY: ('termType', 'value'),
    Metainfo.DATA_TYPE: ('dataType', 'value'),
    Metainfo.PARENT_DICTIONARY: ('parentDictionary', 'accession'),
}


class DictionaryUtil(object):
    """
    Creates dictionaries. Only a Reference Data Administrator can create a dictionary.

    The connection must log in with an API token or an access token, because the ODM REST API
    does not accept a login with an email and a password.
    """

    def __init__(self, connection):
        self.connection = connection

    def create_dictionary(self, parent=None, name=None, url=None, term_type=None, metainfo=None,
                          parent_dictionary=None, description=None, data_type=None, replaces=None):
        """
        Create a dictionary from a local or remote file. ODM shares the dictionary with all users,
        starts its initialization and marks the replaced dictionaries obsolete.
        ``owl``, ``obo`` and ``csv`` formats are supported.

        ``name`` and ``url`` are required. Give them as arguments or in a
        :py:class:`~odm_sdk.Metainfo` instance. Do not give the same value both ways.
        The metainfo can contain only the keys of the other arguments.

        :param parent: not used (legacy).
        :type parent: str
        :param name: name of the dictionary
        :type name: str
        :param url: URL of the file with the terms
        :type url: str
        :param term_type: type of the terms
        :type term_type: str
        :param metainfo: metainfo object
        :type metainfo: Metainfo
        :param parent_dictionary: accession of the parent dictionary
        :type parent_dictionary: str
        :param description: description of the dictionary
        :type description: str
        :param data_type: data type of the dictionary, for example ``Gene Ontology``
        :type data_type: str
        :param replaces: accessions of the dictionaries to mark obsolete
        :type replaces: list[str]
        :return: accession of the new dictionary
        :rtype: str
        """
        if parent is not None:
            sys.stderr.write('The "parent" argument is not used anymore\n')
        request = self._from_metainfo(metainfo)
        arguments = {'name': name, 'url': url, 'termType': term_type,
                     'parentDictionary': parent_dictionary, 'description': description,
                     'dataType': data_type}
        for field, value in arguments.items():
            if value is None:
                continue
            if field in request:
                raise GenestackException('"%s" is given both as an argument and in the metainfo'
                                         % field)
            request[field] = value
        for field in ('name', 'url'):
            if not request.get(field):
                raise GenestackException('"%s" is required' % field)
        request['replaces'] = list(replaces or [])
        response = self.connection.post_rest(DICTIONARIES_PATH, request)
        return response[Metainfo.ACCESSION]

    @staticmethod
    def _from_metainfo(metainfo):
        request = {}
        for key, values in (metainfo or {}).items():
            if key not in _METAINFO_FIELDS:
                raise GenestackException('Metainfo key "%s" is not supported for a dictionary' % key)
            if len(values) != 1:
                raise GenestackException('Metainfo key "%s" must have one value' % key)
            field, value_field = _METAINFO_FIELDS[key]
            request[field] = values[0][value_field]
        return request
