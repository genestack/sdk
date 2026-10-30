# Command-line tools

This guide applies to `odm_sdk/scripts/`. It specializes the
[SDK guide](../AGENTS.md); shared validation is in the
[root instructions](../../AGENTS.md#validation-and-completion).
[setup.py](../../setup.py) is the console-entry-point map. Some modules here have
no installed console command; do not infer an entry point from the filename.

## Authentication routes

Keep the route appropriate to the existing command.

- RPC commands such as [share_study_with_group.py](study_management/share_study_with_group.py)
  and [update_template.py](metainfo_templates/update_template.py) use
  `odm_sdk.utils.make_connection_parser` and `get_connection`. Their namespace
  uses lowercase `host`, `token`, `access_token`, `user`, and `pwd`.
- REST commands [import_ODM_data.py](import_ODM_data.py) and
  [delete_study_or_template.py](delete_study_or_template.py) share
  [token_auth.py](token_auth.py). Reuse `add_host_argument`,
  `add_token_arguments`, and `Headers` for this contract. The namespace uses
  `SERVER`, `API_TOKEN`, and `ACCESS_TOKEN`. Host normalization supplies HTTPS,
  trims trailing slashes, and removes a trailing `/frontend`. `Headers` enforces
  a token and chooses `Genestack-API-Token` or Bearer `Authorization`. It does not
  resolve environment variable names or use saved user settings.

These parsers are not interchangeable. Preserve both token modes and rejection
of conflicting credentials. Read [test_delete_study_or_template.py](../tests/test_delete_study_or_template.py)
for request-header and host examples. Both delete commands share one handler,
which uses `DELETE /api/v1/manage-data/data` with the `accessions` query parameter.
HTTP 202 means acceptance; the command does not poll for completed deletion.

## Ordered imports and jobs

[import_ODM_data.py](import_ODM_data.py) combines an ordered CLI parser and REST
import/link operations. `ParserAstState` and the `make_*_action` factories attach
signals, metadata, libraries, preparations, and cells to preceding parent nodes.
Argument order is data structure, not cosmetic. Trace both `main` and
`ImportParams.from_parsed_params`; programmatic `ImportParams` construction uses
`_fill_parser_from_args` when no parser state is supplied.

`SaneArgumentParser` preserves underscore aliases when reading `sys.argv` and
handles a measurement separator beginning with `-`. Explicit `parse_args` lists
skip that normalization. [test_import.py](../tests/test_import.py) contains a
separate parser factory, so tests of its copied options do not alone validate
production `main` argument wiring.

Preserve `do_import` rejection of missing or conflicting study identifiers,
repeated links, inconsistent parent models, and unsupported signal combinations.
Check version-link and mapping-file validation when changing the tree. The
`--dump-args-as-json` path validates and exits before upload; preserve that boundary.

`_async_import` submits a job and recognizes a specific HTTP 409 duplicate-job
response. The default reuses that job's output; `ALLOW_DUPLICATES` and
`FAIL_IF_FILE_EXISTS` express different behavior. `add_study` marks its duplicate
message as consumed by an external `load.py`; keep that output compatible unless
the consuming integration is part of the change.

`_get_finished_job_info` polls `/info` while status is `STARTED`, `STARTING`, or
`RUNNING`, with attempts derived from `JOB_TIMEOUT / ETL_POLLING_INTERVAL`. Only
`COMPLETED` succeeds after fetching `/output`. Preserve timeout and failure
handling; mock successive status responses and sleep in tests. This bounds poll
attempts, not wall-clock duration of HTTP requests, which currently lack timeouts.

`TemplateAccessionSupplier` discovers a default template lazily only when neither
an explicit template nor an existing study accession is supplied. It authenticates
a session before listing templates. Preserve OAuth headers on both calls; the
access-token discovery regression is covered in `test_import.py`.

Linking errors normally stop execution. `IGNORE_LINKING_ERRORS` lets relevant
operations continue and collect failures, but `do_import` still exits nonzero
when failures remain. The mocked 504 case in `test_import.py` checks that the
linking failure and server response remain visible.

## Shell and administrative utilities

[shell.py](shell.py) and [user_setup.py](user_setup.py) use the framework in
[odm_sdk/shell.py](../shell.py). `Command.update_parser` defines command arguments;
`COMMAND_LIST` registers commands; `OFFLINE` avoids a server connection.
`GenestackShell.process_command` ignores `run`'s return value and treats exceptions
as failure. Do not signal failure merely by returning a false value. Parser help
also feeds [generated Sphinx documentation](../../AGENTS.md#documentation-sources).

[load_init_share_dictionaries.py](dictionaries/load_init_share_dictionaries.py)
owns dictionary load, initialization, and sharing. Its `replace` marks existing
dictionaries obsolete before creating another; template `replace` instead reuses
the existing accession. Read the [template guide](metainfo_templates/AGENTS.md)
when changing that other contract. Initialization starts work and sharing follows;
this is not evidence that initialization has completed.

[internal/README.md](internal/README.md) explains backup dictionary generation.
The gene generator uses external Ensembl/NCBI data and local files. Read its
download/subprocess behavior before running it. `wait_for_host.py` checks health;
`wait_until_ready.py` checks repeated zero running-task counts and merely prints
queued counts. Neither proves a particular import completed; use the job status
contract above for imports. [GEO_prepare.py](study_management/GEO_prepare.py)
uses pandas, which is not declared in runtime requirements, and writes files.
