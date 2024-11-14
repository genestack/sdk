#!/usr/bin/env python3
# coding=utf-8
"""
A script to import and link data to ODM.

See http://odm-user-guide.rtfd.io/en/latest/doc-odm-user-guide/import-data-using-python-script.html
for detailed guide
"""

from __future__ import division, print_function

import argparse
import collections
import copy
import csv
import itertools
import json
import pprint
import re
import sys
from time import sleep

try:
    # Python 3
    from urllib.parse import urlparse
except ImportError:
    # PY3TODO - this is a label for code that could be simplified/improved when
    # dropping support for Python 2
    # Python 2
    from urlparse import urlparse

import requests

# let's do it `six`-style! (https://github.com/benjaminp/six/blob/master/six.py#L35)
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

# PY3TODO
if PY3:
    bytes_type = bytes
else:
    bytes_type = str

ACC_RE = re.compile(r'([A-Z]+[0-9]+)$')

# regexp to match accession in square brackets appended to links
TRAILING_ACC_RE = r'\[([A-Z]+[0-9]+)\]$'
TRAILING_ACC_RE = re.compile(TRAILING_ACC_RE)

LOAD_RETRIES = 60
INTEGRATION_PREFIX = "integrationCurator/%s/integration/link/"
FILE_ENDPOINTS_DICT = {"study": "studyCurator/%s/studies",
                       "samples": "sampleCurator/%s/samples",
                       "variant": "variantCurator/%s/variant/vcf",
                       "expression": "expressionCurator/%s/expression/gct",
                       "flow-cytometry": "flowCytometryCurator/%s/flow-cytometry/facs"}
LINK_ENDPOINTS_DICT = {"samples_to_study": "sample/%s/to/study/%s",
                       "variant_to_sample": "variant/%s/to/sample/%s",
                       "flow-cytometry_to_sample": "flow-cytometry/%s/to/sample/%s",
                       "expression_to_sample": "expression/%s/to/sample/%s"}  # type: dict
LINK_ENDPOINTS_DICT = {k: INTEGRATION_PREFIX + v
                       for k, v in LINK_ENDPOINTS_DICT.items()}

# how long to wait for ETL jobs to be finished (in seconds)
ETL_WAITING_TIMEOUT = 30 * 60
# how often to poll for jobs
ETL_POLLING_INTERVAL = 5

# all supported file "sources" supported by ETL
ETL_SOURCES = ('S3', 'HTTP', 'Arvados', 'LOCAL')

# a mapping of URL scheme to its *default* ETL "source" (see above)
# if no source is provided explicitly
SCHEME_TO_ETL_SOURCE = {
    'http': 'HTTP',
    'https': 'HTTP',
    's3': 'S3',
    'file': 'LOCAL'
}

# guard against possible mistakes in ETL source constants
assert set(SCHEME_TO_ETL_SOURCE.values()).issubset(ETL_SOURCES)

COMMON_URL_PREFIX = 'frontend/rs/genestack'

TAGS = {"-sm": "samples",
        "-lb": "libraries",
        "-pr": "preparations",
        "-f": "flow-cytometry",
        "-fm": "flow-cytometry-metadata",
        "-v": "variant",
        "-vm": "variant-metadata",
        "-e": "expression",
        "-em": "expression-metadata",
        "-fl": "file",
        "-flm": "file-metadata",
        "-mpf": "mapping-file",
        "-mpfa": "mapping-file-accession",
        "-mpfm": "mapping-file-metadata",
        "-nfa": "number-of-feature-attributes",
        "-dc": "data-class",
        "-ms": "measurement-separator"
        }

LIB_PREP_TAGS = {'libraries', 'preparations'}
SIGNAL_TAGS = {'flow-cytometry', 'variant', 'expression'}

FILE_FOUND_ERR_MSG_RE = r'job instance already exists .+ jobExecId=([0-9]+)'
FILE_FOUND_ERR_MSG_RE = re.compile(FILE_FOUND_ERR_MSG_RE)


def is_acc(string):
    return bool(ACC_RE.match(string))


def parse_file_signal(link):
    """ Parse URLs like http://examp.le/file.txt[GSF123456] """
    version = TRAILING_ACC_RE.search(link)
    if version is not None:
        link = link[:version.start()]
        version = version.groups()[0]
    return link, version


def partition(pred, iterable):
    "Use a predicate to partition entries into false entries and true entries"
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = itertools.tee(iterable)
    return itertools.filterfalse(pred, t1), filter(pred, t2)


class GroupLinkingError(Exception):
    """
    Exception raised for error during group linking. E.g linking signals to
    samples or samples to study
    """

    def __init__(self, what, accession_to, accession_from):
        self.what = what
        self.accession_to = accession_to
        self.accession_from = accession_from
        # PY3TODO
        super(GroupLinkingError, self).__init__(self, what, accession_to, accession_from)


def green_text(text):
    if sys.platform == 'win32' or not sys.stdout.isatty():
        return text
    # PY3TODO
    return u"""\u001b[32m""" + text + u"""\u001b[0m"""


def red_text(text):
    if sys.platform == 'win32' or not sys.stdout.isatty():
        return text
    # PY3TODO
    return u"""\u001b[31m""" + text + u"""\u001b[0m"""


class TemplateAccessionSupplier:
    """
    Container for TEMPLATE_ACCESSION.
    If empty, could try to request default template's accession
    """
    def __init__(self, args):
        self.server = args.SERVER
        self.token = args.API_TOKEN
        self.debug = args.debug
        self.template_accession = args.TEMPLATE_ACCESSION
        self.should_request_default = args.TEMPLATE_ACCESSION is None and \
                                      args.study_accession is None
        self._validate()

    def _validate(self):
        if self.token is None and self.should_request_default:
            _err("Please provide template accession when using Access Token", in_red=True)
            sys.exit(1)

    def __call__(self, *args, **kwargs):
        if self.should_request_default:
            self.template_accession = self._request_default_template()
            self.should_request_default = False
        return self.template_accession

    def _authenticate(self):
        aut_url = "/frontend/endpoint/application/invoke/genestack/signin/authenticateByApiToken"
        url_authenticate = self.server + aut_url
        session = requests.Session()
        try:
            result = session.post(url_authenticate, json=[self.token], timeout=10)
            if not json.loads(result.text)["result"]["authenticated"]:
                if self.debug:
                    print(result, result.text)
                print(red_text("You set invalid token or your license is expired!"))
                sys.exit(1)
            return session
        except requests.exceptions.ConnectionError as error:
            if not self.debug:
                if error.__class__.__name__ == 'ConnectionError':
                    _err("Failed connection to server {srv}. Check the server name"
                         .format(srv=self.server))
                if error.__class__.__name__ == 'ConnectTimeout':
                    _err("Connection timeout to server {srv}".format(srv=self.server))
            else:
                _err("{err_name}: {err_args}"
                     "".format(err_name=error.__class__.__name__,
                               err_args=error.args))
            sys.exit(1)

    def _request_default_template(self):
        url_request_template = (self.server +
                                "/frontend/endpoint/application/invoke/genestack"
                                "/study-metainfotemplateeditor/listTemplates")
        session = self._authenticate()
        response = session.post(url=url_request_template, json=[])
        assert response.status_code == 200, response.text
        assert "result" in response.text, response.text
        result = json.loads(response.text)["result"]
        accession = [template["accession"] for template in result
                     if template.get("isDefault", False)][0]
        assert accession
        return accession


def get_study(params):
    response = requests.get(
        url='{0}/frontend/rs/genestack/studyUser/{1}/studies/{2}'.format(
            params.SERVER, params.APP_VERSION, params.study_accession),
        headers=params.headers)
    return response


def check_access_to_study(params):
    response = get_study(params)
    if response.status_code != 200:
        if params.debug:
            print(response, response.text)
        _err("You don't have access permissions to study: "
             "%s or it doesn't exist!" % params.study_accession, in_red=True)
        sys.exit(1)


def read_utf_csv(csv_data):
    ''' Yield stripped and decoded CSV rows as dictionaries '''
    # PY3TODO
    if sys.version_info.major == 3:
        csv_data = (line.decode('utf-8') for line in csv_data)
    for row in csv.DictReader(csv_data):
        yield {k.strip(): v.strip() for k, v in row.items()}


def fetch_and_parse_csv(csv_link):
    """ Fetch remote one-row CSV file and parse it to a dictionary """
    # must not be empty or None
    assert csv_link
    try:
        response = requests.get(csv_link)
    except requests.exceptions.RequestException as error:
        _err("Error accessing metadata file '{link}':\n{err_name}: {err_args}"
             "".format(link=csv_link, err_name=error.__class__.__name__,
                       err_args=error.args))
        sys.exit(1)
    if not response.ok:
        _err("Error accessing metadata file '{}'".format(csv_link),
             response=response, in_red=True)
        sys.exit(1)
    csv_data = read_utf_csv(response.iter_lines())
    try:
        metadata = next(csv_data)
    # pylint: disable=broad-except
    except Exception as err:
        _err("Error parsing '{}' as CSV file:\n"
             "{}: {}".format(csv_link, err, err.args),
             in_red=True)
        sys.exit(1)
    try:
        next(csv_data)
        _err("Metadata file '{}' contains multiple rows, using only the first one"
             "".format(csv_link), in_red=True)
    except StopIteration:
        pass
    return metadata


def _get_etl_source_from_url(url):
    parsed_url = urlparse(url)
    source = SCHEME_TO_ETL_SOURCE.get(parsed_url.scheme)
    if source is None:
        _err("Scheme '{}' is not supported, exiting".format(parsed_url.scheme),
             in_red=True)
        sys.exit(1)
    return source


def link_mappings(mapping_file_acc, expression_acc, params):
    """ Link gene-tx mapping to expression data """
    url = '{}/{}/integrationCurator/{}/links'.format(params.SERVER, COMMON_URL_PREFIX,
                                                     params.APP_VERSION)
    payload = [{'firstId': expression_acc,
                'firstType': 'expressionGroup',
                'secondId': mapping_file_acc,
                'secondType': 'geneTranscriptMapping'}]
    resp = requests.post(url, headers=params.headers, json=payload)
    if not resp.ok:
        _err("Linking gene-transcription mapping '{}' to expression group '{}' failed"
             "".format(mapping_file_acc, expression_acc),
             response=resp, in_red=True)
        sys.exit(1)
    print("Successfully linked: [mapping_file_to_expression]")


def check_mapping_file(acc, params):
    """
    Check if provided accession corresponds to an existing mapping file

    Returns the same accession if it's fine, otherwise exits with error
    """
    if acc is None:
        return None
    url = ('{}/{}/reference-data/{}/xrefsets/{}/metadata'
           ''.format(params.SERVER, COMMON_URL_PREFIX, params.APP_VERSION, acc))
    resp = requests.get(url, headers=params.headers)
    if resp.ok:
        return acc
    _err("mapping file with the accession '{}' is not found".format(acc),
         in_red=True)
    sys.exit(1)


def _err(msg, response=None, in_red=False):
    ''' Print error message '''
    # PY3TODO
    if isinstance(msg, bytes_type):
        msg = msg.decode('utf-8', errors='replace')
    if in_red:
        msg = red_text(msg)
    if response is not None:
        text = response.text
        req = response.request
        if isinstance(text, bytes_type):
            text = text.decode('utf-8', errors='ignore')
        try:
            text = pprint.pformat(json.loads(text))
        except ValueError:
            pass
        msg += (u"\nStatus code: {}\n"
                "Request URL: {}\n"
                "Request body: '{}'\n"
                "Error message from server:\n{}".format(response.status_code,
                                                        req.url,
                                                        req.body,
                                                        text))
    print(msg, file=sys.stderr)


def _check_job_error(response):
    ''' Checks if import job error is actually a message about duplicate '''
    # if a file had already been submitted, REST API returns 409 Conflict
    # pylint: disable=no-member
    if response.status_code != requests.codes.CONFLICT:
        return None
    r_data = _unpack_job_response(response)
    job_id_match = FILE_FOUND_ERR_MSG_RE.search(r_data['error']['message'])
    if job_id_match is None:
        return None
    job_id = int(job_id_match.groups()[0])
    return job_id


def _get_mdata_params(metadata_link, inline_metadata):
    ''' Return dictionary of metadata parameters

    If ``inline_metadata`` is True, parse provided CSV link and return its content
    as a "subdictionary".
    Otherwise, pass metadata link to ETL as-is
    '''
    if not inline_metadata:
        return {"metadataLink": metadata_link}
    metadata = fetch_and_parse_csv(metadata_link)
    return {"data": metadata}


def _select_source(links):
    sources = set(_get_etl_source_from_url(link) for link in links)
    if len(sources) != 1:
        _err("Mixing URL schemes is not supported; provide source explicitly",
             in_red=True)
        sys.exit(1)
    assert sources != set([None])
    return sources.pop()


# pylint: disable-next=too-many-arguments
def _prepare_etl_payload(kind, metadata_link=None, template_id=None, data_link=None,
                         prev_version=None, number_of_feature_attributes=None,
                         data_class=None, measurement_separator=None, source=None, study=None):
    ''' Prepare payload to be sent to ETL as parameters '''
    payload = {}
    if template_id is not None:
        payload["templateId"] = template_id
    inline_metadata = False
    if metadata_link is not None:
        inline_metadata = (kind == 'transcript-mapping')
        md_params = _get_mdata_params(metadata_link, inline_metadata)
        payload.update(md_params)
    if data_link is not None:
        payload["dataLink"] = data_link
    if prev_version is not None:
        payload["previousVersion"] = prev_version
    if number_of_feature_attributes is not None:
        payload["numberOfFeatureAttributes"] = number_of_feature_attributes
    if data_class is not None:
        payload["dataClass"] = data_class
    if measurement_separator is not None:
        payload["measurementSeparator"] = measurement_separator.lstrip()
    if study is not None:
        payload["studyAccession"] = study
    if source is None:
        # determine list of links eligible for source guesswork
        source_links = [data_link]
        if not inline_metadata:
            source_links.append(metadata_link)
        source = _select_source(filter(lambda l: l is not None, source_links))
    payload["source"] = source
    return payload


# pylint: disable-next=too-many-arguments
def _async_import(kind, params, metadata_link=None, data_link=None, prev_version=None,
                  number_of_feature_attributes=None, data_class=None, study=None, measurement_separator=None):
    ''' Import data using Job/ETL API

    Returns ``job_info`` dictionary with all the submitted (and finished) job
    information, and a ``file_exists`` boolean: ``True`` if file has been found
    in ODM, and ``False`` if it has been uploaded anew.
    '''
    if metadata_link is None and kind in ('study', 'samples'):
        _err("No metadata link is provided for {} import"
             "".format(kind))
        sys.exit(1)
    if data_link is None and kind in ('expression', 'variant', 'flow-cytometry',
                                      'transcript-mapping'):
        _err("No data link is provided for {} import"
             "".format(kind))
        sys.exit(1)
    url = "{}/{}/job/{}/import/{}/".format(
        params.SERVER, COMMON_URL_PREFIX, params.APP_VERSION, kind.replace('_', '-'))
    if params.ALLOW_DUPLICATES and kind != 'file':
        url += '?allow_dups=true'
    template_id = params.TEMPLATE_ACCESSION_SUPPLIER() if kind != 'file' else None
    payload = _prepare_etl_payload(kind, metadata_link, template_id, data_link,
                                   prev_version, number_of_feature_attributes,
                                   data_class, measurement_separator, params.ETL_SOURCE, study)

    resp = requests.post(url, headers=params.headers, json=payload)
    if resp.status_code == 200:
        r_data = _unpack_job_response(resp)
        job_id = int(r_data.get('jobExecId'))
        file_exists = False
    else:
        job_id = _check_job_error(resp)
        if job_id is None:
            _err("Submitting job failed!", response=resp, in_red=True)
            sys.exit(1)
        file_exists = True
    job_info = _get_finished_job_info(job_id, params)
    return job_info, file_exists


def _unpack_job_response(r):
    # TODO: go through other unguarded `json.loads` calls and wrap them too
    try:
        return json.loads(r.text)
    except json.decoder.JSONDecodeError:
        _err("Unexpected response received from server "
             "(cannot decode body as JSON)", response=r, in_red=True)
        sys.exit(1)


def _get_finished_job_info(job_id, params):
    ''' Wait for job to finish and return result '''
    job_url = "{}/{}/job/{}/{}".format(
        params.SERVER, COMMON_URL_PREFIX, params.APP_VERSION, job_id)
    info_url = job_url + "/info"
    output_url = job_url + "/output"
    total_tries = params.JOB_TIMEOUT // ETL_POLLING_INTERVAL
    progress_reported = False
    for attempt in range(total_tries):
        status = requests.get(info_url, headers=params.headers)
        status = _unpack_job_response(status).get(u'status')
        if status not in (u'STARTED', u'STARTING', u'RUNNING'):
            break
        sleep(ETL_POLLING_INTERVAL)
        # report "progress" after two minutes of waiting
        if attempt * ETL_POLLING_INTERVAL > 120:
            progress_reported = True
            print("Waiting for job #{} to complete, {} minutes before timeout"
                  "".format(job_id, (total_tries - attempt) * ETL_POLLING_INTERVAL // 60 + 1),
                  end='\r', file=sys.stderr)
    else:
        # clear screen after redrawn messages
        _err('')
        _err("Job {} has been running for {} seconds with no result, exiting"
             "".format(job_id, params.JOB_TIMEOUT))
        sys.exit(1)
    # clear screen after redrawn messages if they had been printed
    if progress_reported:
        _err('')
    output_r = requests.get(output_url, headers=params.headers)
    output = _unpack_job_response(output_r)
    if status != u'COMPLETED':
        _err("Job {} failed with status {}".format(job_id, status),
             response=output_r, in_red=True)
        sys.exit(1)
    return output


def add_mappings(data_link, params, metadata_link=None):
    """ Upload gene-tx mapping file with optional metadata
        for import xref-mappings we are using syncronous endpoint
        https://genestack.atlassian.net/browse/ODM-7489
    """
    metadata = fetch_and_parse_csv(metadata_link) if metadata_link else None
    url = ('{}/{}/reference-data/{}/xrefsets/'
           ''.format(params.SERVER, COMMON_URL_PREFIX, params.APP_VERSION))
    source = _get_etl_source_from_url(data_link).lower()
    payload = {
        "dataLink": data_link,
        "dataSource": source,
        "xrefSetType": "gene-transcript"
    }

    if metadata is not None:
        payload["metadata"] = metadata

    resp = requests.post(url, headers=params.headers, json=payload)
    if resp.status_code != 200:
        _err("Importing '{}' failed!".format(data_link),
             response=resp, in_red=True)
        sys.exit(1)
    accession = json.loads(resp.text)['xrefSetId']
    if accession is None:
        _err("Unexpected response from the server while importing '{}'."
             .format(data_link), response=resp, in_red=True)
        sys.exit(1)
    print("Mapping file {} was added successfully".format(accession))
    return accession


def add_study(params):
    ''' Create new study or return existing one '''
    if params.study_accession:
        check_access_to_study(params)
        return params.study_accession
    job_info, study_exists = _async_import(
        kind='study',
        metadata_link=params.study_link,
        params=params
    )
    accession = job_info.get(u'result', {}).get(u'accession')
    if accession is None:
        _err("Mandatory file: study metadata wasn't loaded. Uploading is stopped!")
        sys.exit(1)
    if study_exists:
        # this error message is parsed by load.py script: do not change it
        _err("'{}' has already been uploaded as study '{}'"
             "".format(params.study_link, accession))
        if params.FAIL_IF_FILE_EXISTS:
            sys.exit(1)
    else:
        print("study " + accession + " was added successfully")
    return accession


def add_and_link_samples(params, study, sample_link):
    job_info, samples_exist = _async_import('samples', metadata_link=sample_link,
                                            params=params)
    group_acc = job_info.get(u'result', {}).get(u'groupAccession')
    if group_acc is None:
        _err("Mandatory file: samples metadata wasn't loaded. "
             "Without samples metadata file, linking of signals to samples are impossible. "
             "Uploading of signals files are stopped!", in_red=True)
        sys.exit(1)
    if samples_exist:
        _err("'{}' has already been uploaded as sample group '{}'"
             "".format(sample_link, group_acc))
        if params.FAIL_IF_FILE_EXISTS:
            sys.exit(1)
    else:
        print("samples were added successfully (sample group accession is {})"
              "".format(group_acc))
    link_by_parent(what="samples_to_study",
                   accession_from=group_acc,
                   accession_to=study,
                   params=params)
    return group_acc


def get_libs_preps_by_study(file_type, params, study):
    link_word = {'libraries': 'library', 'preparations': 'preparation'}[file_type]
    url = ('{}/{}/integrationCurator/{}/integration/link/{}/group/by/study/{}'
           ''.format(params.SERVER, COMMON_URL_PREFIX, params.APP_VERSION, link_word, study))
    response = requests.get(url, headers=params.headers)
    if response.ok:
        return json.loads(response.text)
    if params.debug:
        print(response, response.text)
    _err("You don't have access permissions to study: {} or it doesn't exist!"
         "".format(study), in_red=True)
    sys.exit(1)


def check_study_has_libs_preps(group_acc, samples_group, file_type, params, study):
    libs_preps = get_libs_preps_by_study(file_type, params, study)
    # example of libs_preps: [{"itemId":"GSF020175","metadata":{}}]
    accessions = {item['itemId'] for item in libs_preps}
    if group_acc not in accessions:
        raise GroupLinkingError(what=file_type,
                                accession_to=group_acc,
                                accession_from=samples_group)


def add_and_link_libs_preps(
        samples_group,
        metadata_link,
        file_type,
        params,
        study,
        failures
):
    job_info, exists = _async_import(file_type, metadata_link=metadata_link,
                                     params=params)
    group_acc = job_info.get(u'result', {}).get(u'groupAccession')
    if exists:
        _err("'{}' has already been uploaded as {} group '{}'"
             "".format(metadata_link, file_type, group_acc))
        if params.FAIL_IF_FILE_EXISTS:
            sys.exit(1)
    else:
        print("{ft} were added successfully ({ft} group accession is {acc})"
              "".format(ft=file_type, acc=group_acc))
    link_by_parent(what="{}_to_samples".format(file_type),
                   accession_from=group_acc,
                   accession_to=samples_group,
                   params=params)
    try:
        # TODO remove this check when https://genestack.atlassian.net/browse/ODM-7793 will be fixed
        check_study_has_libs_preps(group_acc, samples_group, file_type, params, study)
    except GroupLinkingError as ex:
        _err("Linking {} ({} to {}) failed"
             "".format(file_type, group_acc, samples_group), in_red=True)
        if not params.IGNORE_LINKING_ERRORS:
            sys.exit(1)
        failures.append(ex)
        return group_acc
    print("Successfully linked: [{}_to_samples]".format(file_type))
    return group_acc


def add_signals(
        file_signal,
        file_metadata,
        file_type,
        number_of_feature_attributes,
        data_class,
        measurement_separator,
        params):
    data_link, prev_version = parse_file_signal(file_signal)
    job_info, signals_exist = _async_import(file_type, metadata_link=file_metadata,
                                            data_link=data_link,
                                            prev_version=prev_version,
                                            number_of_feature_attributes=number_of_feature_attributes,
                                            data_class=data_class,
                                            measurement_separator=measurement_separator,
                                            params=params)
    group_acc = job_info.get(u'result', {}).get(u'groupAccession')
    if signals_exist:
        signal_str = "'{}'".format(file_signal)
        if file_metadata is not None:
            signal_str = "'{} + '{}'".format(signal_str, file_metadata)
        _err("{} {} have already been uploaded as signal group '{}'"
             "".format(file_type, signal_str, group_acc))
        if params.FAIL_IF_FILE_EXISTS:
            sys.exit(1)
    else:
        print("{} data were added successfully (group accession is {})"
              "".format(file_type.replace('-', ' '), group_acc))
    return group_acc


def link_by_parent(what, accession_to, accession_from, params):
    ''' Link data using new group-centric API '''
    ENDPOINT_DICT = {
        'samples_to_study': 'sample/group/{sourceId}/to/study/{targetId}',
        'libraries_to_samples': 'library/group/{sourceId}/to/sample/group/{targetId}',
        'preparations_to_samples': 'preparation/group/{sourceId}/to/sample/group/{targetId}',
        'expression_to_sample': 'expression/group/{sourceId}/to/sample/group/{targetId}',
        'expression_to_libraries': 'expression/group/{sourceId}/to/library/group/{targetId}',
        'expression_to_preparations': 'expression/group/{sourceId}/to/preparation/group/{targetId}',
        'variant_to_sample': 'variant/group/{sourceId}/to/sample/group/{targetId}',
        # API not yet implemented
        # 'variant_to_libraries': 'variant/group/{sourceId}/to/library/group/{targetId}',
        # 'variant_to_preparations': 'variant/group/{sourceId}/to/preparation/group/{targetId}',
        'flow-cytometry_to_sample': 'flow-cytometry/group/{sourceId}/to/sample/group/{targetId}',
        # API not yet implemented
        # 'flow-cytometry_to_libraries':
        #     'flow_cytometry/group/{sourceId}/to/library/group/{targetId}',
        # 'flow-cytometry_to_preparations':
        #     'flow_cytometry/group/{sourceId}/to/preparation/group/{targetId}',
    }
    url = '/'.join([params.SERVER, COMMON_URL_PREFIX,
                    INTEGRATION_PREFIX.rstrip('/') % params.APP_VERSION, ENDPOINT_DICT[what]])
    response = requests.post(url.format(sourceId=accession_from,
                                        targetId=accession_to),
                             headers=params.headers)
    if response.ok:
        print("Successfully linked: [{}]".format(what))
        return

    what = what.replace('_', ' ')
    _err("Linking {what} ({accession_from} to {accession_to}) failed"
         "".format(**locals()), response=response, in_red=True)
    raise GroupLinkingError(what=what,
                            accession_to=accession_to,
                            accession_from=accession_from)


def check_mapping_files_arguments(signal_args):
    # check if there are no mappings and we can skip the checks
    if not any(s.startswith("mapping-file") for s in signal_args):
        return
    if "expression" not in signal_args:
        _err("mapping file is supported with expression matrices only",
             in_red=True)
        sys.exit(1)
    mpf_prefix = 'mapping-'
    mapping_args = collections.Counter(s[len(mpf_prefix):]
                                       for s in signal_args
                                       if s.startswith(mpf_prefix))
    total_mpfiles = mapping_args['file'] + mapping_args['file-accession']
    if total_mpfiles == 0:
        # we checked that there's *something* starting with `mpf_prefix`,
        # and that leaves only metadata
        _err("the parameter '-mpf' for mapping file loading is missing",
             in_red=True)
        sys.exit(1)
    if total_mpfiles > 1:
        _err("Only one mapping file is expected, "
             "check the value of parameters 'mpf' or 'mpfa'",
             in_red=True)
        sys.exit(1)
    if mapping_args["file-metadata"] and mapping_args["file-accession"]:
        _err("Cannot attach mapping metainfo to an existing mapping file",
             in_red=True)
        sys.exit(1)
    if mapping_args["file_metadata"] > 1:
        _err("Cannot attach multiple metadata sources to a mapping file",
             in_red=True)


class SaneArgumentParser(argparse.ArgumentParser):
    """Disables prefix matching in ArgumentParser."""

    # PY3TODO: `argparse.ArgumentParser(allow_abbrev=False)` introduced in 3.5

    def _get_option_tuples(self, option_string):
        """Prevent argument parsing from looking for prefix matches."""
        return []

    # pylint: disable-next=redefined-outer-name
    def parse_args(self, args=None, namespace=None):
        if args is None:
            # args default to the system args
            args = []
            prev = ""
            for a in sys.argv[1:]:
                # to bypass a bug in argparse library, add space to the front of the argument
                if (prev == "-ms" or prev == "--measurement-separator") and a.startswith('-'):
                    args.append(' ' + a)
                elif a.startswith('--'):
                    args.append(a.replace('_', '-'))
                else:
                    args.append(a)
                prev = a
        return super(SaneArgumentParser, self).parse_args(args, namespace)


# pylint: disable-next=protected-access
class _SingletonAction(argparse._StoreAction):
    """ Ensures that only one argument is passed """

    def __init__(self, mutually_exclusive, err_msg, *args, **kwargs):
        super(_SingletonAction, self).__init__(*args, **kwargs)
        self.err_msg = err_msg
        self.mutually_exclusive = mutually_exclusive

    def __call__(self, parser_, namespace, values, option_string=None):
        already_defined = any(getattr(namespace, v) is not None
                              for v in self.mutually_exclusive)
        if already_defined:
            raise argparse.ArgumentError(self, self.err_msg)
        setattr(namespace, self.dest, values)

# pylint: disable-next=protected-access
class _StoreServerName(argparse._StoreAction):
    """ Ensures that server name is not ended wit `/` """

    def __call__(self, parser_, namespace, values, option_string=None):
        setattr(namespace, self.dest, values.rstrip("/"))


def prevent_redundant_parameters(mutually_exclusive, err_msg):
    return lambda *args, **kwargs: _SingletonAction(mutually_exclusive, err_msg, *args, **kwargs)


class Headers(dict):
    """Derives http-headers from arguments"""

    def __init__(self, args):
        super(dict, self).__init__()
        self["Genestack-API-Token"] = args.API_TOKEN
        self["Authorization"] = "Bearer {}".format(args.ACCESS_TOKEN) if args.ACCESS_TOKEN else None
        self["Accept"] = "application/json"
        self["Content-Type"] = "application/json"
        self._validate()

    def _validate(self):
        if self["Genestack-API-Token"] and self["Authorization"]:
            _err("Please provide a Genestack-Api-Token or an Access Token but not both",
                 in_red=True)
            sys.exit(1)
        if self["Genestack-API-Token"] is None and self["Authorization"] is None:
            _err("Please provide a Genestack-Api-Token or an Access Token",
                 in_red=True)
            sys.exit(1)

    def __getstate__(self):
        return self


class DeprecatedAction(argparse.Action):
    """ Issues deprecation warning when called """

    def __call__(self, parser_, namespace, values, option_string=None):
        _err("'{}' is no longer supported, and left a no-op for "
             "compatibility reasons".format(option_string))


# PY3TODO
class ParserAstState(object):
    def __init__(self):
        self.sample_node_list = []
        self.file_node_list = []
        self.current_node = None

    def has_libraries_or_preparations(self):
        all_tags = self.get_all_tags()
        return not all_tags.isdisjoint(LIB_PREP_TAGS)

    def has_files(self):
        return len(self.file_node_list) > 0

    def get_all_tags(self):
        result = set()

        def get_tags(node):
            result.add(node['tag'])
            for child_node in node.get('children', []):
                get_tags(child_node)

        for node in self.sample_node_list:
            get_tags(node)
        return result

    def has_consistent_data_model(self):
        if not self.has_libraries_or_preparations():
            return True
        # in case libraries or preparations have been passed, all signals
        # should be linked to them instead of samples
        for sample_node in self.sample_node_list:
            for child_node in sample_node.get('children', []):
                if child_node['tag'] not in LIB_PREP_TAGS:
                    return False
        return True

    def has_non_expression_signals(self):
        all_tags = self.get_all_tags()
        return not all_tags.issubset({'samples', 'libraries', 'preparations',
                                      'expression', 'mapping-file'})


class BaseCustomAction(argparse.Action):
    def handle_action(self, tag, value, option_string):
        raise NotImplementedError('This method expected to be overrided in subclasses')

    def __call__(self, _parser, _args, value, option_string=None):
        opt_str = option_string.replace('--', '')
        tag = TAGS[opt_str] if opt_str.startswith('-') else opt_str
        if value is None:
            _err("You didn't provide {} file URL! Exit!"
                 "".format(tag.replace('-', ' ')), in_red=True)
            sys.exit(1)
        self.handle_action(tag, value, option_string)
        data = getattr(_args, self.dest)
        data = [] if data is None else data
        data.append(value)
        setattr(_args, self.dest, data)


def make_samples_action(parser_state):
    class SampleAction(BaseCustomAction):
        def handle_action(self, tag, value, option_string):
            new_sample_node = {'tag': tag, 'value': value}
            parser_state.sample_node_list.append(new_sample_node)
            parser_state.current_node = new_sample_node

    return SampleAction


def make_libraries_and_preparations_action(parser_state):
    class LibPrepAction(BaseCustomAction):
        def handle_action(self, tag, value, option_string):
            if is_acc(value):
                # (libraries|preparations) <accession>
                new_implicit_sample_node = {}
                new_implicit_sample_node['tag'] = 'samples'
                new_implicit_sample_node['value'] = 'implicit'
                current_sample_node = new_implicit_sample_node
                parser_state.sample_node_list.append(new_implicit_sample_node)
            else:
                # Search for the closest 'explicit' samples node to link the current lib/prep to it.
                current_sample_node = next(
                    (
                        node for node in reversed(parser_state.sample_node_list)
                        if node['value'] != 'implicit'
                    ),
                    None
                )
                if current_sample_node is None:
                    _err("You've provided {} before sample file or sample parent accession. Exit!"
                         .format(tag.replace('-', ' ')), in_red=True)
                    sys.exit(1)

            new_node = {'tag': tag, 'value': value}
            children = current_sample_node.get('children', [])
            children.append(new_node)
            current_sample_node['children'] = children
            parser_state.current_node = new_node

    return LibPrepAction


def make_signal_action(parser_state):
    class SignalAction(BaseCustomAction):
        def handle_action(self, tag, value, option_string):
            current_node = parser_state.current_node
            if current_node is None:
                _err("You've provided {} before sample file or sample parent accession. Exit!"
                     .format(tag.replace('-', ' ')), in_red=True)
                sys.exit(1)

            if tag.endswith('-metadata'):
                file_type = tag[:-9]
                children = current_node.get('children', [])
                # search for the closest node with the same file_type which
                # doesn't contain a metadata link
                last_node = next(
                    (
                        item for item in reversed(children)
                        if item['tag'] == file_type and 'metadata' not in item
                    ),
                    None
                )
                if last_node is None:
                    _err("No data link is provided for {} metadata '{}'"
                         "".format(file_type, value), in_red=True)
                    sys.exit(1)

                last_node['metadata'] = value
            elif tag == 'number-of-feature-attributes':
                current_tag = current_node.get('tag', '')
                if current_tag == 'file':
                    _err("Number of feature attributes is not a supported parameter for files", in_red=True)
                    sys.exit(1)
                children = current_node.get('children', [])
                last_node = next(
                    (
                        item for item in reversed(children)
                        if 'nfa' not in item
                    ),
                    None
                )
                if last_node is None:
                    _err(
                        "A file can only have one value of number of feature attributes. "
                        "Please check --number-of-feature-attributes (-nfa) argument in your input.",
                        in_red=True)
                    sys.exit(1)

                last_node['nfa'] = value
            elif tag == 'data-class':
                current_tag = current_node.get('tag', '')
                if current_tag == 'file':
                    if 'dc' in current_node:
                        _err(
                            "A file can only have one value of data class. "
                            "Please check --data-class (-dc) argument in your input.",
                            in_red=True)
                        sys.exit(1)
                    current_node['dc'] = value
                else:
                    children = current_node.get('children', [])
                    last_node = next(
                        (
                            item for item in reversed(children)
                            if 'dc' not in item
                        ),
                        None
                    )
                    if last_node is None:
                        _err(
                            "A file can only have one value of data class. "
                            "Please check --data-class (-dc) argument in your input.",
                            in_red=True)
                        sys.exit(1)

                    last_node['dc'] = value
            elif tag == 'measurement-separator':
                current_tag = current_node.get('tag', '')
                if current_tag == 'file':
                    _err("Measurement separator is not a supported parameter for files", in_red=True)
                    sys.exit(1)
                children = current_node.get('children', [])
                last_node = next(
                    (
                        item for item in reversed(children)
                        if 'ms' not in item
                    ),
                    None
                )
                if last_node is None:
                    _err(
                        "A file can have only one value for the measurement separator. "
                        "Please check --measurement-separator (-ms) argument in your input.",
                        in_red=True)
                    sys.exit(1)

                last_node['ms'] = value
            else:
                new_signal_node = {'tag': tag, 'value': value}
                children = current_node.get('children', [])
                children.append(new_signal_node)
                current_node['children'] = children

    return SignalAction


def make_file_action(parser_state):
    class FileAction(BaseCustomAction):
        def handle_action(self, tag, value, option_string):
            if tag == 'file-metadata':
                current_node = parser_state.current_node
                if current_node is None:
                    _err("No file link is provided for the file metadata 'PROVIDED_METADATA_LINK'", in_red=True)
                    sys.exit(1)
                if 'metadata' in current_node:
                    _err(
                        "A file can only have one file metadata link. "
                        "Please check --file-metadata (-flm) argument in your input.",
                        in_red=True)
                    sys.exit(1)
                current_node['metadata'] = value
            else:
                new_file_node = {'tag': tag, 'value': value}
                parser_state.file_node_list.append(new_file_node)
                parser_state.current_node = new_file_node

    return FileAction


def make_mapping_file_action(parser_state):
    class MappingFileAction(BaseCustomAction):
        def handle_action(self, tag, value, option_string):
            current_node = parser_state.current_node
            if current_node is None:
                _err("You provide " + tag.replace('-', ' ') +
                     " before sample file. Exit!", in_red=True)
                sys.exit(1)

            children = current_node.get('children', [])
            mapping_node = {'tag': tag, 'value': value}
            children.append(mapping_node)
            current_node['children'] = children

    return MappingFileAction


def check_and_merge_mapping_file_nodes(signal_nodes):
    non_mf_nodes_f, mf_nodes_f = partition(
        lambda node: node['tag'].startswith('mapping-file'),
        signal_nodes)
    mf_nodes = list(mf_nodes_f)
    if len(mf_nodes) == 0:
        return signal_nodes

    signal_args = []
    for node in signal_nodes:
        signal_args.append(node['tag'])
        signal_args.append(node['value'])
    check_mapping_files_arguments(signal_args)

    new_mf_node = {'tag': 'mapping-file'}
    for mf_node in mf_nodes:
        if mf_node['tag'] == 'mapping-file-metadata':
            new_mf_node['metadata'] = mf_node['value']
        else:
            new_mf_node['value'] = mf_node['value']
    return list(non_mf_nodes_f) + [new_mf_node]


def check_and_merge_mapping_file_in_sample_nodes(sample_nodes):
    for sample_node in sample_nodes:
        children = sample_node.get('children', [])
        children_tags = {child['tag'] for child in children}
        if children_tags.issubset(LIB_PREP_TAGS):
            for lib_prep_node in children:
                if 'children' not in lib_prep_node:
                    continue
                signal_nodes = lib_prep_node.get('children')
                lib_prep_node['children'] = check_and_merge_mapping_file_nodes(signal_nodes)
        else:
            if 'children' in sample_node:
                sample_node['children'] = check_and_merge_mapping_file_nodes(children)


def add_signals_to_parent(parent_prep_group, parent_prep_file_type, signal_nodes, signal_cache,
                          params, failures):
    expression_accs = []
    for node in signal_nodes:
        file_type = node['tag']
        url = node['value']
        nfa = node['nfa'] if 'nfa' in node else None
        data_class = node['dc'] if 'dc' in node else None
        separator = node['ms'] if 'ms' in node else None
        metadata = node.get('metadata', None)
        if file_type in SIGNAL_TAGS:
            signal_group = signal_cache.get(url, None)
            if signal_group is None:
                signal_group = add_signals(file_signal=url,
                                           file_metadata=metadata,
                                           file_type=file_type,
                                           number_of_feature_attributes=nfa,
                                           data_class=data_class,
                                           measurement_separator=separator,
                                           params=params)
                signal_cache[url] = signal_group
            if file_type == 'expression':
                expression_accs.append(signal_group)
            what = '{}_to_{}'.format(file_type, parent_prep_file_type)
            try:
                link_by_parent(what, parent_prep_group, signal_group, params)
            except GroupLinkingError as ex:
                if not params.IGNORE_LINKING_ERRORS:
                    sys.exit(1)
                failures.append(ex)
                continue
        elif file_type == 'mapping-file':
            # mapping file is always the last node, if present
            if is_acc(url):
                map_f_acc = check_mapping_file(url, params)
            else:
                map_f_acc = add_mappings(url, params, metadata)
            for expr_acc in expression_accs:
                link_mappings(map_f_acc, expr_acc, params)


def add_lib_prep(sample_group, nodes, link_cache, params, study, failures):
    for node in nodes:
        lib_prep_file_type = node['tag']
        url = node['value']
        lib_prep_group = link_cache.get(url, None)
        if lib_prep_group is None:
            lib_prep_group = add_and_link_libs_preps(
                sample_group, url, lib_prep_file_type, params, study, failures
            )
            link_cache[url] = lib_prep_group
        children = node.get('children', [])
        add_signals_to_parent(
            lib_prep_group, lib_prep_file_type, children,
            link_cache, params, failures
        )


def existing_lib_prop(node, signal_cache, params, failures):
    lib_prep_file_type = node['tag']
    lib_prep_group = node['value']
    children = node.get('children', [])
    add_signals_to_parent(
        lib_prep_group, lib_prep_file_type, children, signal_cache, params, failures
    )


def handle_lib_prep_case(parser_state, params, study, failures):
    link_cache = {}
    for sample_node in parser_state.sample_node_list:
        value = sample_node['value']
        libraries_and_preparations = sample_node.get('children', [])
        if value == 'implicit':
            assert len(libraries_and_preparations) == 1, \
                'Internal error: expect only one subnode for implicit sample node'
            sub_node = libraries_and_preparations[0]
            existing_lib_prop(sub_node, link_cache, params, failures)
            return

        if is_acc(value):
            # existing samples group, expect some libraries and preparations
            if len(libraries_and_preparations) == 0:
                print('samples argument {} is ignored'.format(value))
                return
            sample_group = value
        else:
            try:
                sample_group = add_and_link_samples(params, study, sample_link=value)
            except GroupLinkingError as ex:
                if not params.IGNORE_LINKING_ERRORS:
                    sys.exit(1)
                failures.append(ex)
                continue

        add_lib_prep(
            sample_group, libraries_and_preparations,
            link_cache, params, study, failures
        )


def handle_samples_signals_case(parser_state, params, study, failures):
    signal_cache = {}
    for sample_node in parser_state.sample_node_list:
        value = sample_node['value']
        signals = sample_node.get('children', [])

        if is_acc(value):
            # existing samples group, expect some signals
            if not signals:
                _err('No signals provided to link, ignoring `--samples {}`'.format(value))
                return
            sample_group = value
        else:
            try:
                sample_group = add_and_link_samples(params, study, sample_link=value)
            except GroupLinkingError as ex:
                if not params.IGNORE_LINKING_ERRORS:
                    sys.exit(1)
                failures.append(ex)
                continue

        add_signals_to_parent(
            sample_group, 'sample', signals, signal_cache, params, failures
        )


def handle_files_case(parser_state, params, study):
    for file_node in parser_state.file_node_list:
        value = file_node['value']
        dc = file_node.get('dc')
        if dc is None:
            _err("No Data class for the file was provided", in_red=True)
            sys.exit(1)
        flm = file_node.get('metadata')
        job_info, _ = _async_import(
            'file', params, metadata_link=flm, data_link=value, study=study, data_class=dc)
        accession = job_info.get(u'result', {}).get(u'accession')
        print(f"file {accession} was attached successfully to study {study}")


def check_for_repeated_links(link, nodes, links_cache):
    links_cache[link] = 'study'
    for node in nodes:
        value = node['value']
        tag = node['tag']
        value = None if value == 'implicit' else value
        if value is not None:
            if value in links_cache:
                _err('Duplicate link or accession: --{} {}'.format(tag, value), in_red=True)
                sys.exit(1)
            links_cache[value] = tag
        meta = node.get('metainfo', None)
        if meta is not None:
            if meta in links_cache:
                _err('Duplicate link or accession: --{} {}'.format(tag, meta), in_red=True)
                sys.exit(1)
            else:
                links_cache[meta] = tag
        children = node.get('children', [])
        check_for_repeated_links(link, children, links_cache)


def collect_all_nodes_by_tag(nodes, filter_tag_fun):
    result = []
    for node in nodes:
        if filter_tag_fun(node['tag']):
            result.append(node)
        children = node.get('children', [])
        result = result + collect_all_nodes_by_tag(children, filter_tag_fun)
    return result


def collect_all_mapping_file_nodes(nodes):
    return collect_all_nodes_by_tag(
        nodes,
        lambda x: x.startswith('mapping-file')
    )


def add_all_signal_args_to_all_lib_preps(sample_nodes):
    all_libs_preps = collect_all_nodes_by_tag(
        sample_nodes,
        lambda x: x in LIB_PREP_TAGS
    )
    all_signal_nodes = collect_all_nodes_by_tag(
        sample_nodes,
        lambda x: x in SIGNAL_TAGS
    )
    mapping_file_nodes = collect_all_mapping_file_nodes(sample_nodes)
    for libs_preps_node in all_libs_preps:
        libs_preps_node['children'] = copy.deepcopy(all_signal_nodes)
    for sample_node in sample_nodes:
        sample_node['children'] = copy.deepcopy(all_libs_preps)
    if mapping_file_nodes:
        sample_node = sample_nodes[0]
        libs_preps_node = sample_node['children'][0]
        libs_preps_node['children'] = all_signal_nodes + mapping_file_nodes


def add_all_signal_args_to_all_samples(sample_nodes):
    all_signal_nodes = collect_all_nodes_by_tag(
        sample_nodes,
        lambda x: x in SIGNAL_TAGS
    )
    for sample_node in sample_nodes:
        children = sample_node.get('children', [])
        non_signal_children = [node for node in children if node['tag'] not in SIGNAL_TAGS]
        sample_node['children'] = all_signal_nodes + non_signal_children


def check_signal_versions(study_acc, parent_accession, parent_tag, signals):
    """ Perform basic validation of signal versioning arguments
    Updating version is allowed when:
    - study already exists
    - samples already exist
    - designated previous version of signal object appears only once in a
      script call
    """
    prev_versions = set()
    for signal_node in signals:
        value = signal_node['value']
        _, prev_version = parse_file_signal(value)
        if prev_version is None:
            continue
        if study_acc is None:
            _err("Previous versions cannot be specified when creating new studies, "
                 "only for signal group objects of existing studies",
                 in_red=True)
            sys.exit(1)
        if parent_accession is None:
            _err("Previous versions cannot be specified when creating new {0}, "
                 "only for signal group objects of existing {0}".format(parent_tag),
                 in_red=True)
            sys.exit(1)
        if prev_version in prev_versions:
            _err("It is not possible to import a new version of an existing "
                 "signal group object version ('{}') more than once "
                 "in the same script call".format(prev_version),
                 in_red=True)
            sys.exit(1)
        prev_versions.add(prev_version)


def check_signal_versions_libs_preps(sample_nodes, study_acc):
    for sample_node in sample_nodes:
        libs_preps = sample_node.get('children', [])
        for libs_preps_node in libs_preps:
            value = libs_preps_node['value']
            parent_accession = value if is_acc(value) else None
            parent_tag = libs_preps_node['tag']
            signals = [node for node in libs_preps_node.get('children', [])
                       if node['tag'] in SIGNAL_TAGS]
            check_signal_versions(study_acc, parent_accession, parent_tag, signals)


def check_signal_versions_samples(sample_nodes, study_acc):
    for sample_node in sample_nodes:
        value = sample_node['value']
        parent_accession = value if is_acc(value) else None
        parent_tag = sample_node['tag']
        signals = [node for node in sample_node.get('children', []) if node['tag'] in SIGNAL_TAGS]
        check_signal_versions(study_acc, parent_accession, parent_tag, signals)


def do_import(import_params):
    parser_args_state = import_params.parser_args_state
    if not (import_params.SERVER.startswith("https://") or import_params.SERVER.startswith("http://")):
        _err("The server url should start with 'http' or 'https'")
        sys.exit(1)
    if not (import_params.study_link or import_params.study_accession):
        _err("No study link or accession was provided", in_red=True)
        sys.exit(1)
    if import_params.study_link and import_params.study_accession:
        _err("You need to provide either study link or accession", in_red=True)
        sys.exit(1)

    check_for_repeated_links(
        import_params.study_link,
        parser_args_state.sample_node_list,
        links_cache={}
    )

    # If the option LINK_SIGNALS_TO_ALL_SAMPLES is set, we try to modify
    # the arguments in such a way as to conform to the behaviour, which is described in
    # ODM-7826.
    # The subsequent code actually works with repeated links for signal data

    if import_params.LINK_SIGNALS_TO_ALL_SAMPLES:
        if parser_args_state.has_libraries_or_preparations():
            add_all_signal_args_to_all_lib_preps(parser_args_state.sample_node_list)
        else:
            add_all_signal_args_to_all_samples(parser_args_state.sample_node_list)

    check_and_merge_mapping_file_in_sample_nodes(parser_args_state.sample_node_list)

    mapping_files_number = len(collect_all_mapping_file_nodes(parser_args_state.sample_node_list))
    if import_params.LINK_SIGNALS_TO_ALL_SAMPLES and mapping_files_number > 1:
        _err('Only one mapping file is expected with link-all-to-all option', in_red=True)
        sys.exit(1)

    if (parser_args_state.has_libraries_or_preparations()
            and parser_args_state.has_non_expression_signals()):
        _err('the linkage between libraries/preparations and variants/flow-cytometry '
             'is not supported', in_red=True)
        sys.exit(1)

    if not parser_args_state.has_consistent_data_model():
        _err('inconsistent data model', in_red=True)
        sys.exit(1)

    if parser_args_state.has_libraries_or_preparations():
        check_signal_versions_libs_preps(
            parser_args_state.sample_node_list,
            import_params.study_accession
        )
    else:
        check_signal_versions_samples(
            parser_args_state.sample_node_list,
            import_params.study_accession
        )

    if import_params.dump_args_as_json:
        print(json.dumps(parser_args_state.sample_node_list, indent=2))
        sys.exit(0)

    study = add_study(params=import_params)
    failures = []
    if parser_args_state.has_libraries_or_preparations():
        handle_lib_prep_case(parser_args_state, import_params, study, failures)
    else:
        handle_samples_signals_case(parser_args_state, import_params, study, failures)

    if parser_args_state.has_files():
        handle_files_case(parser_args_state, import_params, study)

    print(green_text(u"Execution is finished!"))
    if failures:
        sys.exit(1)
    return study


class ImportParams:
    # The class constructor is a subject to change, its parameters might be changed in the future.
    def __init__(
            self,
            server,
            headers=None,
            token=None,
            study_link=None,
            study_accession=None,
            app_version="default-released",
            etl_source=None,
            template_accession_supplier=lambda: None,
            allow_duplicates=False,
            number_of_feature_attributes=None,
            data_class=None,
            measurement_separator=None,
            fail_if_file_exists=False,
            link_signals_to_all_samples=False,
            ignore_linking_errors=False,
            job_timeout=ETL_WAITING_TIMEOUT,
            debug=False,
            dump_args_as_json=False,
            # provide dedicated links to entities
            # or parser_args_state, containing any of them
            # (used for command line call, wider functionality is supported)
            samples_link=None,
            libraries_link=None,
            preparations_link=None,
            expression_link=None,
            expression_metadata_link=None,
            variant_link=None,
            variant_metadata_link=None,
            flow_cytometry_link=None,
            flow_cytometry_metadata_link=None,
            parser_args_state=None
    ):
        self.SERVER = server.rstrip('/')
        self.study_link = study_link
        self.study_accession = study_accession
        self.APP_VERSION = app_version
        self.ETL_SOURCE = etl_source
        self.TEMPLATE_ACCESSION_SUPPLIER = template_accession_supplier
        self.ALLOW_DUPLICATES = allow_duplicates
        self.NUMBER_OF_FEATURE_ATTRIBUTES = number_of_feature_attributes
        self.DATA_CLASS = data_class
        self.MEASUREMENT_SEPARATOR = measurement_separator
        self.FAIL_IF_FILE_EXISTS = fail_if_file_exists
        self.LINK_SIGNALS_TO_ALL_SAMPLES = link_signals_to_all_samples
        self.IGNORE_LINKING_ERRORS = ignore_linking_errors
        self.JOB_TIMEOUT = job_timeout
        self.debug = debug
        self.dump_args_as_json = dump_args_as_json
        if headers is not None:
            self.headers = headers
        elif token is not None:
            self.headers = {"Genestack-API-Token": token,
                            "Accept": "application/json",
                            "Content-Type": "application/json"}
        else:
            _err("You should either provide headers or genestack api token")
            sys.exit(1)
        if not parser_args_state:
            parser_args_state = ImportParams._fill_parser_from_args(
                samples_link, libraries_link, preparations_link,
                expression_link, expression_metadata_link,
                variant_link, variant_metadata_link,
                flow_cytometry_link, flow_cytometry_metadata_link,
            )
        self.parser_args_state = parser_args_state

    @staticmethod
    def _fill_parser_from_args(
            samples_link,
            libraries_link,
            preparations_link,
            expression_link,
            expression_metadata_link,
            variant_link,
            variant_metadata_link,
            flow_cytometry_link,
            flow_cytometry_metadata_link
    ):
        parser_args_state = ParserAstState()
        if samples_link:
            make_samples_action(parser_args_state)(
                dest="data",
                option_strings=[]
            ).handle_action(
                tag="samples",
                value=samples_link,
                option_string=None
            )
        if libraries_link:
            make_libraries_and_preparations_action(parser_args_state)(
                dest="data",
                option_strings=[]
            ).handle_action(
                tag="libraries",
                value=libraries_link,
                option_string=None
            )
        if preparations_link:
            make_libraries_and_preparations_action(parser_args_state)(
                dest="data",
                option_strings=[]
            ).handle_action(
                tag="preparations",
                value=preparations_link,
                option_string=None
            )
        if expression_link:
            make_signal_action(parser_args_state)(
                dest="data",
                option_strings=[]
            ).handle_action(
                tag="expression",
                value=expression_link,
                option_string=None
            )
        if expression_metadata_link:
            make_signal_action(parser_args_state)(
                dest="data",
                option_strings=[]
            ).handle_action(
                tag="expression-metadata",
                value=expression_metadata_link,
                option_string=None
            )
        if variant_link:
            make_signal_action(parser_args_state)(
                dest="data",
                option_strings=[]
            ).handle_action(
                tag="variant",
                value=variant_link,
                option_string=None
            )
        if variant_metadata_link:
            make_signal_action(parser_args_state)(
                dest="data",
                option_strings=[]
            ).handle_action(
                tag="variant-metadata",
                value=variant_metadata_link,
                option_string=None
            )
        if flow_cytometry_link:
            make_signal_action(parser_args_state)(
                dest="data",
                option_strings=[]
            ).handle_action(
                tag="flow-cytometry",
                value=flow_cytometry_link,
                option_string=None
            )
        if flow_cytometry_metadata_link:
            make_signal_action(parser_args_state)(
                dest="data",
                option_strings=[]
            ).handle_action(
                tag="flow-cytometry-metadata",
                value=flow_cytometry_metadata_link,
                option_string=None
            )
        return parser_args_state

    @classmethod
    def from_parsed_params(cls, args, parser_args_state):
        return cls(
            server=args.SERVER,
            headers=Headers(args),
            study_link=args.study_link,
            study_accession=args.study_accession,
            app_version=args.APP_VERSION,
            etl_source=args.ETL_SOURCE,
            template_accession_supplier=TemplateAccessionSupplier(args),
            allow_duplicates=args.ALLOW_DUPLICATES,
            number_of_feature_attributes=args.NUMBER_OF_FEATURE_ATTRIBUTES,
            data_class=args.DATA_CLASS,
            measurement_separator=args.MEASUREMENT_SEPARATOR,
            fail_if_file_exists=args.FAIL_IF_FILE_EXISTS,
            link_signals_to_all_samples=args.LINK_SIGNALS_TO_ALL_SAMPLES,
            ignore_linking_errors=args.IGNORE_LINKING_ERRORS,
            job_timeout=args.JOB_TIMEOUT,
            debug=args.debug,
            dump_args_as_json=args.dump_args_as_json,
            parser_args_state=parser_args_state
        )


def main():
    parser_args_state = ParserAstState()
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
                             "Usually not required, but you might need to override "
                             "heuristics based on URL itself and server configuration"
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
    args = parser.parse_args()

    do_import(ImportParams.from_parsed_params(args, parser_args_state))


if __name__ == "__main__":
    main()
