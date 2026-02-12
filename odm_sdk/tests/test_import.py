import argparse
import sys
import unittest
from contextlib import contextmanager
from io import StringIO

import requests_mock

from odm_sdk.scripts.import_ODM_data import ImportParams, do_import, ParserAstState, \
    SaneArgumentParser, prevent_redundant_parameters, _StoreServerName, make_samples_action, \
    DeprecatedAction, make_libraries_and_preparations_action, make_cell_action, make_signal_action, \
    make_file_action, make_mapping_file_action, ETL_WAITING_TIMEOUT, ETL_SOURCES

JOB_API_PATH = "frontend/endpoint/rs/genestack/job/default-released"
INTEGRATION_LINK_PATH = "frontend/endpoint/rs/genestack/integrationCurator/default-released/integration/link"


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def get_arg_parser(parser_args_state):
    parser = SaneArgumentParser(description=__doc__,
                                epilog="Old style options using underscores "
                                       "(e.g., '--link_all_to_all') are still supported, "
                                       "but considered obsolete",
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-t", "--token",
                        action=prevent_redundant_parameters(("API_TOKEN", "ACCESS_TOKEN"),
                                                            "only one token can be specified. "
                                                            "Please choose the authentication method: "
                                                            "through the Access Token or "
                                                            "through the Genestack-API-token"),
                        dest="API_TOKEN",
                        nargs="?",
                        help="API_TOKEN")
    parser.add_argument("-at", "--access-token",
                        action=prevent_redundant_parameters(("API_TOKEN", "ACCESS_TOKEN"),
                                                            "only one token can be specified. "
                                                            "Please choose the authentication method: "
                                                            "through the Access Token or "
                                                            "through the Genestack-API-token"),
                        dest="ACCESS_TOKEN",
                        nargs="?",
                        help="ACCESS_TOKEN")
    parser.add_argument("-H", "--host", "-srv", "--server",
                        action=_StoreServerName,
                        const="https://odm-demos.genestack.com/",
                        default="https://odm-demos.genestack.com/",
                        nargs="?",
                        dest="SERVER",
                        help="URL of the instance data is being loaded to")
    parser.add_argument("-tmpl", "--template",
                        action="store",
                        const=None,
                        default=None,
                        nargs="?",
                        dest="TEMPLATE_ACCESSION",
                        help="Accession of the template, by default will use "
                             "template marked as default.")
    parser.add_argument("--debug",
                        action="store",
                        const=True,
                        default=False,
                        nargs="?",
                        dest="debug",
                        help="Enable debug mode.")
    parser.add_argument("-s", "--study",
                        action=prevent_redundant_parameters(('study_link', 'study_accession'),
                                                            "provide exactly one study via a link or an existing study accession"),
                        dest="study_link",
                        help="link to study file")
    parser.add_argument("-sa", "--study-accession",
                        action=prevent_redundant_parameters(('study_link', 'study_accession'),
                                                            "provide exactly one study via a link or an existing study accession"),
                        dest="study_accession",
                        help="accession of existing study")
    parser.add_argument("-sm", "--samples",
                        action=make_samples_action(parser_args_state),
                        dest="data",
                        metavar="SAMPLES_LINK_OR_ACCESSION",
                        nargs="?",
                        help="existing sample group accession "
                             "or link to file with sample data")
    parser.add_argument("-la", "--link-attribute",
                        # "Attribute to link data with sample source"
                        # linking by group does not support custom linking attribute
                        # it's left for compatibility reasons
                        action=DeprecatedAction,
                        help=argparse.SUPPRESS)
    parser.add_argument("-lb", "--libraries",
                        action=make_libraries_and_preparations_action(parser_args_state),
                        dest="data",
                        metavar="LIBRARIES_LINK_OR_ACCESSION",
                        help="link to libraries data file or accession of existing library group",
                        nargs="?")
    parser.add_argument("-pr", "--preparations",
                        action=make_libraries_and_preparations_action(parser_args_state),
                        dest="data",
                        metavar="PREPARATIONS_LINK_OR_ACCESSION",
                        help="link to preparations data file or accession of "
                             "existing preparation group",
                        nargs="?")
    parser.add_argument("-c", "--cell",
                        action=make_cell_action(parser_args_state),
                        dest="data",
                        metavar="SIGNAL_LINK",
                        help="link to cell data file",
                        nargs="?")
    parser.add_argument("-e", "--expression",
                        action=make_signal_action(parser_args_state),
                        dest="data",
                        metavar="SIGNAL_LINK",
                        help="link to tabular data file (not only expression data) except Gene "
                             "Variant or Flow Cytometry",
                        nargs="?")
    parser.add_argument("-em", "--expression-metadata",
                        action=make_signal_action(parser_args_state),
                        dest="data",
                        metavar="SIGNAL_METADATA_LINK",
                        help="link to tabular metadata file (not only expression data) except Gene "
                             "Variant or Flow Cytometry",
                        nargs="?")
    parser.add_argument("-v", "--variant",
                        action=make_signal_action(parser_args_state),
                        dest="data",
                        metavar="SIGNAL_LINK",
                        help="link to variants data file",
                        nargs="?")
    parser.add_argument("-vm", "--variant-metadata",
                        action=make_signal_action(parser_args_state),
                        dest="data",
                        metavar="SIGNAL_METADATA_LINK",
                        help="link to variant metadata file",
                        nargs="?")
    parser.add_argument("-f", "--flow-cytometry",
                        action=make_signal_action(parser_args_state),
                        dest="data",
                        metavar="SIGNAL_LINK",
                        help="link to flow cytometry data file",
                        nargs="?")
    parser.add_argument("-fm", "--flow-cytometry-metadata",
                        action=make_signal_action(parser_args_state),
                        dest="data",
                        metavar="SIGNAL_METADATA_LINK",
                        help="link to flow cytometry metadata file",
                        nargs="?")
    parser.add_argument("-fl", "--file",
                        action=make_file_action(parser_args_state),
                        help="link to a file to be attached",
                        nargs="?")
    parser.add_argument("-flm", "--file-metadata",
                        action=make_file_action(parser_args_state),
                        help="link to metadata file for this attached file",
                        nargs="?")
    parser.add_argument("-nfa", "--number-of-feature-attributes",
                        action=make_signal_action(parser_args_state),
                        dest="NUMBER_OF_FEATURE_ATTRIBUTES",
                        metavar="NUMBER_OF_FEATURE_ATTRIBUTES",
                        help="number of feature attribute columns in a tsv file",
                        nargs="?")
    parser.add_argument("-dc", "--data-class",
                        action=make_signal_action(parser_args_state),
                        dest="DATA_CLASS",
                        metavar="DATA_CLASS",
                        help="describes the data type of the uploaded file",
                        nargs="?")
    parser.add_argument("-ms", "--measurement-separator",
                        action=make_signal_action(parser_args_state),
                        dest="MEASUREMENT_SEPARATOR",
                        metavar="MEASUREMENT_SEPARATOR",
                        help="separator for sample/library/preparation name from the measurement name in column names in a tsv file",
                        nargs="?")
    parser.add_argument("-mpf", "--mapping-file",
                        action=make_mapping_file_action(parser_args_state),
                        dest="data",
                        metavar="MAPPING_FILE_LINK",
                        help="link to mapping file",
                        nargs="?")
    parser.add_argument("-mpfa", "--mapping-file-accession",
                        action=make_mapping_file_action(parser_args_state),
                        dest="data",
                        metavar="MAPPING_FILE_ACCESSION",
                        help="accession of the existing mapping file",
                        nargs="?")
    parser.add_argument("-mpfm", "--mapping-file-metadata",
                        action=make_mapping_file_action(parser_args_state),
                        dest="data",
                        metavar="MAPPING_FILE_METADATA_LINK",
                        help="link to metadata file for this mapping file",
                        nargs="?")
    parser.add_argument("-av", "--app-version",
                        action="store",
                        default="default-released",
                        dest="APP_VERSION",
                        help="application version, appended to server URL to select "
                             "a particular endpoint version; default is '%(default)s' "
                             "(it is recommended not to change this parameter)",
                        nargs="?")
    parser.add_argument("-T", "--job-timeout", dest="JOB_TIMEOUT",
                        metavar="TIMEOUT-SECONDS", type=int, default=ETL_WAITING_TIMEOUT,
                        help="time to wait for import jobs to finish (in seconds), "
                             "defaults to %(default)s")
    parser.add_argument("--import-source", dest="ETL_SOURCE", metavar="PROTOCOL",
                        choices=ETL_SOURCES,
                        help="protocol (source) for server to fetch data; valid choices are: {}\n"
                             "The source parameter is ignored and will be removed in version 1.61."
                             "The source is automatically extracted from the link"
                             "".format(ETL_SOURCES))
    parser.add_argument("-lata", "--link-all-to-all",
                        dest="LINK_SIGNALS_TO_ALL_SAMPLES",
                        action="store_true",
                        default=False,
                        help="Link all signals to all samples, instead of "
                             "preceding 'samples' file only")
    parser.add_argument("-ile", "--ignore-linking-errors",
                        dest="IGNORE_LINKING_ERRORS",
                        action="store_true",
                        default=False,
                        help="To allow the script to continue even if errors "
                             "linking study, samples and signal files occur")
    parser.add_argument('-J', '--dump-args-as-json',
                        action="store_true",
                        default=False,
                        help=argparse.SUPPRESS)
    behaviour_args = parser.add_mutually_exclusive_group()
    behaviour_args.add_argument("--allow-duplicates", dest="ALLOW_DUPLICATES",
                                action='store_true',
                                help="allow uploading of duplicate data (warning: "
                                     "this is *not* recommended outside of training use or tests)")
    behaviour_args.add_argument("--fail-if-exists", dest="FAIL_IF_FILE_EXISTS",
                                action='store_true',
                                help=("exit if the file being imported already exists on the "
                                      "server (default is to re-use existing file)"))
    return parser


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

    def test_ImportParams_ODM_cell(self):
        """
        Tests if hierarchy is parsed correctly. Samples can have libraries, preparations
        and cells. Libraries and preparations can have samples for parent and
        signals and cells for children. Cells can have samples, libraries or preparations
        for parents and expressions for children.
        """
        parser_args_state = ParserAstState()
        parser = get_arg_parser(parser_args_state)
        argsMock = ["-t",
                    "tknRoot ",
                    "--host",
                    "https://testhost.io ",
                    "--study",
                    "https://study.tsv",
                    "--samples",
                    "https://samples1.tsv",
                    "-pr",
                    "https://preparations",
                    "-c",
                    "https://cell1",
                    "--cell",
                    "https://cell2",
                    "-e",
                    "https://expressions1",
                    "--samples",
                    "https://samples2.tsv",
                    "-c",
                    "https://cell3",
                    "-lb",
                    "https://library1",
                    "-e",
                    "https://expressions2",
                    "-c",
                    "https://cell4",
                    "-e",
                    "https://expressions3",
                    "-pr",
                    "https://preparations1",
                    "-e",
                    "https://expressions4",
                    "-c",
                    "https://cell5",
                    "-e",
                    "https://expressions5",
                    "-e",
                    "https://expressions6"]
        args = parser.parse_args(args=argsMock)
        parsedArgs = ImportParams.from_parsed_params(args, parser_args_state).parser_args_state
        sample_node_list = parsedArgs.sample_node_list
        self.assertEqual(2,
                         len(sample_node_list),
                         "There should be two samples for the study"
                         " - https://samples1.tsv and https://samples2.tsv")
        get_cell_children = lambda parent: (
            [c for c in parent.get('children') if c['tag'] == 'cells']
        )
        active_sample = sample_node_list[0]
        self.assertEqual(1,
                         len(active_sample.get('children')),
                         "First sample should have one child - preparations (https://preparations)")
        preparation = active_sample.get('children')[0]
        self.assertEqual(2,
                         len(preparation.get('children')),
                         "First samples preparation should have two children")
        cell_children = get_cell_children(active_sample.get('children')[0])
        self.assertEqual(2,
                         len(cell_children),
                         "First sample's preparation should have two cell children"
                         " - https://cell1 and https://cell2")
        self.assertEqual(1,
                         len(cell_children[1].get('children')),
                         "Second cell should have one expression child (https://expressions1)")
        active_sample = sample_node_list[1]
        self.assertEqual(3,
                         len(active_sample.get('children')),
                         "Second sample should have three children"
                         " - https://cell3, https://library1 and https://preparations1")
        self.assertEqual(1,
                         len(get_cell_children(active_sample)),
                         "Second sample should have one cell child")
        library = next((l for l in active_sample.get('children') if l['tag'] == 'libraries'),
                       None)
        self.assertIsNotNone(library,
                             "Second sample should have library")
        self.assertEqual(2,
                         len(library.get('children')),
                         "Second sample's library should have two children"
                         " - https://expressions2 and https://cell4")
        cell_children = get_cell_children(library)
        self.assertEqual(1,
                         len(cell_children),
                         "Second sample library should have one cell child")
        self.assertEqual(1,
                         len(cell_children[0].get('children')),
                         "Second sample's library cell child should have one expression child")
        preparation = next((p for p in active_sample.get('children') if p['tag'] == 'preparations'),
                           None)
        self.assertIsNotNone(preparation,
                             "Second sample should have one preparation")
        self.assertEqual(2,
                         len(preparation.get('children')),
                         "Second sample's preparation should have two children"
                         " - https://expressions4 and https://cell5")
        cell_children = get_cell_children(preparation)
        self.assertEqual(1,
                         len(cell_children),
                         "Second sample's  preparation should have one cell child")
        self.assertEqual(2,
                         len(cell_children[0].get('children')),
                         "Second sample's preparation cell should have two children"
                         " - https://expressions5 and https://expressions6")

    def test_ImportParams_ODM_cell_expression(self):
        parser_args_state = ParserAstState()
        parser = get_arg_parser(parser_args_state)
        argsMock = [
            '-t', 'tknRoot',
            '--host', 'https://test.io',
            '-sa', 'GSF000001',
            #SAMPLE (1 implicit cell, 1 regular cell, 1 LIB, 1 PREP)
            '-sm', 'GSF000002',
            '-c', 'GSF000003',
            '-e', 'https://testexp01.io',
            '-nfa', '2',
            '--data-class', 'Blood counts',
            '--expression-metadata', 'https://testexpmeta01.io',
            '-e', 'https://testexp02.io',
            '-nfa', '2',
            '-c', 'https://testcell01.io',
            '-e', 'https://testexp03.io',
            '-nfa', '2',
            #LIBRARY (1 implicit cell, 2 regular cell)
            '-lb', 'https://testlib01.io',
            '-c', 'https://testcell02.io',
            '-e', 'https://testexp04.io',
            '-nfa', '2',
            '-dc', 'other',
            '-em', 'https://expressionMetadata01.io',
            '-c', 'GSF000004',
            '-e', 'https://testexp05.io',
            '-nfa', '2',
            '-c', 'https://testcell03.io',
            '-e', 'https://testexp05.io',
            '-nfa', '2',
            #PREPARATION (1 implicit cell, 1 regular cell)
            '--preparations', 'https://testprep01.io',
            '-c', 'GSF000006',
            '-e', 'https://testexp06.io',
            '-nfa', '2',
            '-c', 'https://testcell04.io',
            '-e', 'https://testexp07.io',
            '-nfa', '2',
        ]
        args = parser.parse_args(args=argsMock)
        parsedArgs = ImportParams.from_parsed_params(args, parser_args_state).parser_args_state
        sample_node_list = parsedArgs.sample_node_list
        self.assertEqual(4,
                         len(sample_node_list),
                         "There should be four samples nodes for the study"
                         " - one regular (GSF000001) and three implicit")
        implicit_sample_nodes = [s for s in sample_node_list if s['value'] == 'implicit']
        self.assertEqual(3,
                         len(implicit_sample_nodes),
                         "There should be three implicit samples nodes for the study,"
                         " for cells accessions GSF000003, GSF000004, GSF000006")
        sample_node = sample_node_list[0]
        self.assertEqual(3, len(sample_node.get('children')),
                         "Sample node should have three children - "
                         " cell (https://testcell01),"
                         " library and preparation")
        sample_cell = sample_node.get('children')[0]
        self.assertEqual(1, len(sample_cell.get('children')))
        self.assertEqual("https://testexp03.io", sample_cell.get('children')[0]['value'])
        sample_library = sample_node.get('children')[1]
        self.assertEqual('libraries', sample_library['tag'])
        self.assertEqual(2, len(sample_library.get('children')))
        self.assertEqual("https://testcell02.io", sample_library.get('children')[0]['value'])
        self.assertEqual(1, len(sample_library.get('children')[0].get('children')))
        self.assertEqual("https://testcell03.io", sample_library.get('children')[1]['value'])
        self.assertEqual(1, len(sample_library.get('children')[1].get('children')))
        sample_preparation = sample_node.get('children')[2]
        self.assertEqual('preparations', sample_preparation['tag'])
        self.assertEqual(1, len(sample_preparation.get('children')))
        self.assertEqual("https://testcell04.io", sample_preparation.get('children')[0]['value'])
        self.assertEqual(1, len(sample_preparation.get('children')[0].get('children')))
        firs_implicit_cell = sample_node_list[1].get('children')[0]
        self.assertEqual("GSF000003", firs_implicit_cell['value'])
        self.assertEqual(2, len(firs_implicit_cell.get('children')))
        self.assertEqual("https://testexp01.io", firs_implicit_cell.get('children')[0]['value'])
        self.assertEqual("https://testexp02.io", firs_implicit_cell.get('children')[1]['value'])
        second_implicit_cell = sample_node_list[2].get('children')[0]
        self.assertEqual("GSF000004", second_implicit_cell['value'])
        self.assertEqual(1, len(second_implicit_cell.get('children')))
        self.assertEqual("https://testexp05.io", second_implicit_cell.get('children')[0]['value'])
        third_implicit_cell = sample_node_list[3].get('children')[0]
        self.assertEqual("GSF000006", third_implicit_cell['value'])
        self.assertEqual("https://testexp06.io", third_implicit_cell.get('children')[0]['value'])


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
