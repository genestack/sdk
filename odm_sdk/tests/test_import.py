import sys
import unittest
from contextlib import contextmanager
from io import StringIO

import requests_mock

from odm_sdk.scripts.import_ODM_data import ImportParams, do_import

JOB_API_PATH = "frontend/rs/genestack/job/default-released"
INTEGRATION_LINK_PATH = "frontend/rs/genestack/integrationCurator/default-released/integration/link"


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class ImportTest(unittest.TestCase):

    def test_exception_on_both_study_identifiers(self):
        with self.assertRaises(SystemExit) as cm, captured_output() as (out, err):
            do_import(ImportParams(
                server="https://dummy",
                headers={"Authenticate": "Token example"},
                study_link="provided link",
                study_accession="provided accession",
            ))
        self.assertEqual(1, cm.exception.code)
        error_text = err.getvalue().strip()
        self.assertEqual('You need to provide either study link or accession', error_text)

    def test_exception_on_providing_no_tokens(self):
        with self.assertRaises(SystemExit) as cm, captured_output() as (out, err):
            args = _MockArgs({
                "SERVER": "https://dummy",
                "study_link": "https://provided.link"
            })
            ImportParams.from_parsed_params(args, None)
        self.assertEqual(1, cm.exception.code)
        error_text = err.getvalue().strip()
        self.assertEqual('Please provide a Genestack-Api-Token or an Access Token', error_text)

    def test_exception_on_providing_two_tokens(self):
        with self.assertRaises(SystemExit) as cm, captured_output() as (out, err):
            args = _MockArgs({
                "ACCESS_TOKEN": "aToken",
                "API_TOKEN": "bToken",
                "SERVER": "https://dummy",
                "study_link": "https://provided.link"
            })
            ImportParams.from_parsed_params(args, None)
        self.assertEqual(1, cm.exception.code)
        error_text = err.getvalue().strip()
        self.assertEqual('Please provide a Genestack-Api-Token or an Access Token but not both',
                         error_text)

    def test_exception_on_providing_api_token(self):
        args = _MockArgs({
            "API_TOKEN": "bToken",
            "TEMPLATE_ACCESSION": "some",
            "SERVER": "https://dummy",
            "study_link": "https://provided.link"
        })
        ImportParams.from_parsed_params(args, None)

    def test_exception_on_providing_access_token(self):
        args = _MockArgs({
            "ACCESS_TOKEN": "aToken",
            "TEMPLATE_ACCESSION": "some",
            "SERVER": "https://dummy",
            "study_link": "https://provided.link"
        })
        ImportParams.from_parsed_params(args, None)

    def test_exception_on_providing_access_token_wo_accession(self):
        with self.assertRaises(SystemExit) as cm, captured_output() as (out, err):
            args = _MockArgs({
                "ACCESS_TOKEN": "aToken",
                "SERVER": "https://dummy",
                "study_link": "https://provided.link"
            })
            ImportParams.from_parsed_params(args, None)
        self.assertEqual(1, cm.exception.code)
        error_text = err.getvalue().strip()
        self.assertEqual('Please provide template accession when using Access Token', error_text)

    def test_ImportParams_constructed_with_token(self):
        ip = ImportParams(server="https://dummy",
                          token="aToken",
                          study_link="provided link",
                          study_accession="provided accession")
        self.assertEqual("aToken", ip.headers["Genestack-API-Token"])

    def test_ImportParams_do_not_constructed_wo_headers_and_token(self):
        with self.assertRaises(SystemExit) as cm, captured_output() as (out, err):
            ImportParams(server="https://wow")
        self.assertEqual(1, cm.exception.code)
        error_text = err.getvalue().strip()
        self.assertEqual('You should either provide headers or genestack api token',
                         error_text)

    @requests_mock.Mocker()
    def test_linking_error_is_visible_to_a_user(self, m):
        srv = "https://dummy.genestack.com"

        # mock study import
        study_job_id = 1
        study_job = {
            "jobExecId": study_job_id,
            "startedBy": "Genestack Superuser",
            "jobName": "IMPORT_STUDY_TSV",
            "status": "STARTING",
            "createTime": "16-11-2022 08:40:14"
        }
        m.post(f"{srv}/{JOB_API_PATH}/import/study/", json=study_job)
        study_job["status"] = "COMPLETED"
        m.get(f"{srv}/{JOB_API_PATH}/{study_job_id}/info", json=study_job)
        study_accession = "GSF020175"
        study_job_result = {
            "result": {
                "accession": study_accession
            }
        }
        m.get(f"{srv}/{JOB_API_PATH}/{study_job_id}/output", json=study_job_result)

        # mock samples import
        samples_job_id = 2
        samples_job = {
            "jobExecId": samples_job_id,
            "startedBy": "Genestack Superuser",
            "jobName": "IMPORT_SAMPLES_TSV",
            "status": "STARTING",
            "createTime": "16-11-2022 08:41:14"
        }
        m.post(f"{srv}/{JOB_API_PATH}/import/samples/", json=samples_job)
        samples_job["status"] = "COMPLETED"
        m.get(f"{srv}/{JOB_API_PATH}/{samples_job_id}/info", json=samples_job)
        samples_group_accession = "GSF020176"
        samples_group_result = {
            "result": {
                "groupAccession": samples_group_accession
            }
        }
        m.get(f"{srv}/{JOB_API_PATH}/{samples_job_id}/output", json=samples_group_result)

        # mock linking - gateway time-out
        m.post(f"{srv}/{INTEGRATION_LINK_PATH}"
               f"/sample/group/{samples_group_accession}/to/study/{study_accession}",
               text="""<html>
                           <head><title>504 Gateway Time-out</title></head>
                           <body bgcolor="white">
                               <center><h1>504 Gateway Time-out</h1></center>
                               <hr><center>nginx</center>
                           </body>
                       </html>""",
               status_code=504)

        with self.assertRaises(SystemExit) as cm, captured_output() as (out, err):
            do_import(ImportParams(
                server=srv,
                headers={"Genestack-API-Token": "aToken"},
                study_link="s3://dummy-bucket/dummy-path/study.tsv",
                samples_link="s3://dummy-bucket/dummy-path/samples.tsv"
            ))
        self.assertEqual(1, cm.exception.code)
        study_import_output, samples_import_output = out.getvalue().splitlines()
        self.assertEqual(f"study {study_accession} was added successfully", study_import_output)
        self.assertEqual(f"samples were added successfully "
                         f"(sample group accession is {samples_group_accession})",
                         samples_import_output)
        linking_error_message, linking_server_response = err.getvalue().split('\n', 1)
        self.assertEqual(f"Linking samples to study "
                         f"({samples_group_accession} to {study_accession}) failed",
                         linking_error_message)
        self.assertIn("504 Gateway Time-out", linking_server_response)


class _MockArgs(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return None


if __name__ == '__main__':
    unittest.main()
