import sys
import unittest
from unittest import mock

import requests_mock

from odm_sdk.scripts import delete_study_or_template

DELETE_URL = "https://odm.test/frontend/rs/genestack/manageData/default-released/data"


def run_script(*argv):
    with mock.patch.object(sys, "argv", ["odm-delete-study", *argv]):
        delete_study_or_template.main()


class DeleteStudyOrTemplateTest(unittest.TestCase):

    def test_deletes_with_api_token(self):
        with requests_mock.Mocker() as m:
            m.delete(DELETE_URL, status_code=202, json=[])
            run_script("-H", "https://odm.test/", "--token", "tkn", "--accession", "GSF1")
        request = m.request_history[0]
        self.assertEqual("tkn", request.headers["Genestack-API-Token"])
        self.assertNotIn("Authorization", request.headers)
        self.assertEqual({"accessions": ["gsf1"]}, request.qs)

    def test_deletes_with_access_token(self):
        with requests_mock.Mocker() as m:
            m.delete(DELETE_URL, status_code=202, json=[])
            run_script("-H", "https://odm.test", "--access-token", "jwt", "--accession", "GSF1")
        request = m.request_history[0]
        self.assertEqual("Bearer jwt", request.headers["Authorization"])
        self.assertNotIn("Genestack-API-Token", request.headers)

    def test_host_is_required(self):
        with requests_mock.Mocker() as m:
            with self.assertRaises(SystemExit) as cm:
                run_script("--token", "tkn", "--accession", "GSF1")
        self.assertEqual(2, cm.exception.code)
        self.assertEqual(0, m.call_count)

    def test_fails_on_error_response(self):
        with requests_mock.Mocker() as m:
            m.delete(DELETE_URL, status_code=404, text="not found")
            with self.assertRaises(SystemExit) as cm:
                run_script("-H", "https://odm.test", "--token", "tkn", "--accession", "GSF1")
        self.assertEqual(1, cm.exception.code)

    def test_requires_a_token(self):
        with requests_mock.Mocker() as m:
            with self.assertRaises(SystemExit) as cm:
                run_script("-H", "https://odm.test", "--accession", "GSF1")
        self.assertEqual(1, cm.exception.code)
        self.assertEqual(0, m.call_count)

    def test_rejects_both_tokens(self):
        with self.assertRaises(SystemExit) as cm:
            run_script("--token", "a", "--access-token", "b", "--accession", "GSF1")
        self.assertEqual(2, cm.exception.code)

    def test_login_and_password_are_not_supported(self):
        with self.assertRaises(SystemExit) as cm:
            run_script("-u", "root@genestack.com", "-p", "pwd", "--accession", "GSF1")
        self.assertEqual(2, cm.exception.code)


if __name__ == "__main__":
    unittest.main()
