import json
import unittest

import requests_mock

from odm_sdk import (BioMetaKeys, Connection, DictionaryUtil, GenestackAuthenticationException,
                     GenestackException, GenestackResponseError, Metainfo)

SERVER_URL = "https://odm.test/frontend/endpoint"
SIGNIN_URL = SERVER_URL + "/application/invoke/genestack/signin/"
DICTIONARIES_URL = "https://odm.test/api/v1/dictionaries"
AUTHENTICATED = {"result": {"authenticated": True}, "log": []}


def connection_by_token(m):
    m.post(SIGNIN_URL + "authenticateByApiToken", json=AUTHENTICATED)
    connection = Connection(SERVER_URL)
    connection.login_by_token("tkn")
    return connection


class DictionaryUtilTest(unittest.TestCase):

    def test_creates_a_dictionary_with_the_api_token(self):
        with requests_mock.Mocker() as m:
            connection = connection_by_token(m)
            m.post(DICTIONARIES_URL, status_code=201, json={"genestack:accession": "GSF3"})

            accession = DictionaryUtil(connection).create_dictionary(
                name="Disease Ontology", url="https://example.com/doid.owl", term_type="disease",
                description="description", data_type="Gene Ontology", parent_dictionary="GSF2",
                replaces=["GSF1"])

        self.assertEqual("GSF3", accession)
        request = m.request_history[-1]
        self.assertEqual("tkn", request.headers["Genestack-API-Token"])
        self.assertEqual({
            "name": "Disease Ontology", "url": "https://example.com/doid.owl", "termType": "disease",
            "description": "description", "dataType": "Gene Ontology", "parentDictionary": "GSF2",
            "replaces": ["GSF1"],
        }, request.json())

    def test_creates_a_dictionary_with_the_access_token(self):
        with requests_mock.Mocker() as m:
            m.post(SIGNIN_URL + "authenticateOAuthAccessToken", json=AUTHENTICATED)
            connection = Connection(SERVER_URL)
            connection.login_by_access_token("jwt")
            m.post(DICTIONARIES_URL, status_code=201, json={"genestack:accession": "GSF3"})

            DictionaryUtil(connection).create_dictionary(name="name", url="https://example.com/a.owl")

        request = m.request_history[-1]
        self.assertEqual("Bearer jwt", request.headers["Authorization"])
        self.assertNotIn("Genestack-API-Token", request.headers)

    def test_reads_the_values_from_the_metainfo(self):
        metainfo = Metainfo()
        metainfo.add_string(Metainfo.NAME, "name")
        metainfo.add_external_link(BioMetaKeys.DATA_LINK, "s3://bucket/file name.owl")
        metainfo.add_file_reference(Metainfo.PARENT_DICTIONARY, "GSF2")
        metainfo.add_string(Metainfo.DATA_TYPE, "Gene Ontology")
        with requests_mock.Mocker() as m:
            connection = connection_by_token(m)
            m.post(DICTIONARIES_URL, status_code=201, json={"genestack:accession": "GSF3"})

            DictionaryUtil(connection).create_dictionary(metainfo=metainfo)

        self.assertEqual({
            "name": "name", "url": "s3://bucket/file name.owl", "parentDictionary": "GSF2",
            "dataType": "Gene Ontology", "replaces": [],
        }, json.loads(m.request_history[-1].body))

    def test_a_value_both_as_argument_and_in_metainfo_is_an_error(self):
        metainfo = Metainfo()
        metainfo.add_string(Metainfo.NAME, "name")
        with requests_mock.Mocker() as m:
            connection = connection_by_token(m)
            with self.assertRaises(GenestackException):
                DictionaryUtil(connection).create_dictionary(name="name", url="u", metainfo=metainfo)

    def test_an_unsupported_metainfo_key_is_an_error(self):
        metainfo = Metainfo()
        metainfo.add_string("genestack:other", "value")
        with requests_mock.Mocker() as m:
            connection = connection_by_token(m)
            with self.assertRaises(GenestackException):
                DictionaryUtil(connection).create_dictionary(name="name", url="u", metainfo=metainfo)

    def test_name_and_url_are_required(self):
        with requests_mock.Mocker() as m:
            connection = connection_by_token(m)
            with self.assertRaises(GenestackException):
                DictionaryUtil(connection).create_dictionary(url="u")
            with self.assertRaises(GenestackException):
                DictionaryUtil(connection).create_dictionary(name="name")

    def test_a_login_with_a_password_cannot_create_a_dictionary(self):
        with requests_mock.Mocker() as m:
            m.post(SIGNIN_URL + "authenticate", json=AUTHENTICATED)
            connection = Connection(SERVER_URL)
            connection.login("user@odm.test", "pwd")
            with self.assertRaises(GenestackAuthenticationException):
                DictionaryUtil(connection).create_dictionary(name="name", url="u")
        self.assertFalse(any(r.url == DICTIONARIES_URL for r in m.request_history))

    def test_a_server_error_has_the_status_and_the_body(self):
        with requests_mock.Mocker() as m:
            connection = connection_by_token(m)
            m.post(DICTIONARIES_URL, status_code=400, text='Dictionary "GSF1" is not found.')
            with self.assertRaises(GenestackResponseError) as cm:
                DictionaryUtil(connection).create_dictionary(name="name", url="u", replaces=["GSF1"])
        self.assertIn("400", str(cm.exception))
        self.assertIn('Dictionary "GSF1" is not found.', str(cm.exception))
