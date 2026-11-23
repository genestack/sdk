# SDK contracts

This guide applies to `odm_sdk/`, including tests and scripts. The
[root instructions](../AGENTS.md) govern shared compatibility, build setup, and
validation. Read the [CLI guide](scripts/AGENTS.md) for script behavior.

## RPC and public interfaces

[connection.py](connection.py) owns `Connection`, `Application`, and the response
envelope. `Application.invoke(method, *params)` sends a JSON array of positional
parameters to `/application/invoke/{vendor}/{application}/{method}` and returns
`Response.result`. `get_response` returns the envelope, including logs and trace.
Preserve that distinction and the order of parameters in wrapper methods.

`Application` accepts either an explicit application ID or a subclass
`APPLICATION_ID`, rejecting both together and IDs without two slash-separated
components. [FilesUtil](files_util.py), [ShareUtil](share_util.py), and
[GroupsUtil](groups_util.py) are existing wrappers to inspect before adding calls
for file lookup, sharing, or group resolution. Check each helper's actual
defaults and results; `FilesUtil.search_files` returns the server search result,
whereas `find_file_by_name` returns an accession or `None`.

Keep failure categories from [exceptions.py](exceptions.py) distinct. HTTP 401
becomes `GenestackAuthenticationException`; other HTTP failures become
`GenestackResponseError`; request failures become `GenestackConnectionFailure`.
An envelope with a non-null `error` becomes `GenestackServerException` in
`Application`. Changing one layer must not silently turn failures into results.
`GENESTACK_CLIENT_TIMEOUT` controls RPC POST requests in `perform_request`; it
does not cover `get_request`, multipart uploads, or the separate REST scripts.

## Metadata and import helpers

[Metainfo](metainfo.py) maps each key to a list of typed scalar dictionaries.
[metainfo_scalar_values.py](metainfo_scalar_values.py) defines their wire shapes:
ordinary scalars use `value`, dates use `date`, external links use `url`, `text`,
and `format`, and file references use `accession`. Preserve multi-value semantics
and test both construction and `parse_metainfo_from_dict` for serialization changes.

[DataImporter](data_importer.py) calls `genestack/upload.createFile` and extracts
an accession. It is distinct from the REST job importer in
[scripts/import_ODM_data.py](scripts/import_ODM_data.py). Its private
`__add_to_metainfo` enforces required values and rejects supplying the same key
through both a method argument and metainfo. Keep these checks in affected
creation methods. `_copy_metainfo` is a shallow copy; nested values can still be
shared. Do not claim caller isolation without checking nested mutation.

The dictionary CLI is a current consumer of `DataImporter.create_dictionary`.
Several older creation methods explicitly reject use. In particular,
`create_experiment` mentions `FilesUtil.create_dataset` in its error text, but no
such helper exists here. Verify a replacement API before recommending one.

[chunked_upload.py](chunked_upload.py) implements the resumable upload used by
`Application.upload_chunked_file`. Its GET probe, multipart POST, resumable
identifier, final `lastChunkUploaded` result, retry limits, and worker termination
are one protocol. Changes need mocked probe/upload/error coverage and a check
that workers terminate; existing CLI tests do not exercise this protocol.

## Authentication and local settings

[utils.py](utils.py) owns `make_connection_parser`, `get_user`, and
`get_connection`. This route supports a configured alias, email/password, API
token, or OAuth access token. [settings/user.py](settings/user.py) turns a host
into the RPC endpoint and authenticates a `Connection`; it may probe the health
endpoint. `Connection.login_by_access_token` accepts either a literal token or
an environment variable name and adds the Bearer header. This is different from
the REST CLI token route described in the [CLI guide](scripts/AGENTS.md#authentication-routes).

[settings/config.py](settings/config.py) loads the local `.genestack/genestack.xml`
configuration at import time. Password and API-token persistence tries keyring
first, then uses the existing raw-storage choice and prompts. Preserve those
choices and credential masking when changing settings. OAuth access tokens are
held by `User` but are not persisted by `Config.save`; adding that behavior would
be a credential-storage change.

For parser and user selection changes, start with
[test_arguments.py](tests/test_arguments.py). Extend validation for the contract
you change; that module does not establish transport, storage, or upload coverage.
