# ODM SDK repository instructions

This repository publishes the `odm-sdk` Python library and the `odm-*` command-line
tools for Open Data Manager. Server implementations and the separately packaged
`odm-api` dependency are outside this checkout.

## Scope and reading routes

For planning, editing, and review, read this file and each `AGENTS.md` between the
repository root and the affected file. When starting at the root, explicitly open
the applicable guides below before working in their subtrees. More specific
guides specialize their ancestors; they cannot relax the shared compatibility and
validation requirements here. Links to another area supply context, not authority
over that area's files. Platform instructions and permissions still take priority.

| Task | Read |
| --- | --- |
| SDK interfaces, RPC, metadata, credentials, or tests of those contracts | [SDK guide](odm_sdk/AGENTS.md) |
| CLI arguments, authentication, import jobs, shell commands, or administrative utilities | [CLI guide](odm_sdk/scripts/AGENTS.md), with its SDK ancestor |
| Template configuration, schemas, dictionary resolution, or technical fields | [Template guide](odm_sdk/scripts/metainfo_templates/AGENTS.md), with both ancestors |
| Packaging, dependencies, CI, or version generation | [Build and dependencies](#build-and-dependencies) |
| Sphinx sources or generated command help, including changes to shell parsers | [Documentation sources](#documentation-sources) |

Codex and Claude use this same rule set. Codex discovers ancestors down to its
starting directory, so the explicit routes also cover work below that directory.
Claude Code 2.1.277 or later can load `AGENTS.md` natively, including descendant
guides when it reads files there. A project or ancestor `CLAUDE.md` or
`CLAUDE.local.md` can suppress that default. For that setup, use Claude's user-level
Project instructions setting to load both file types. Loading details are in the
official [Codex instructions documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
and [Claude memory documentation](https://code.claude.com/docs/en/memory#agentsmd).

## Shared compatibility

- Preserve public imports in [odm_sdk/__init__.py](odm_sdk/__init__.py), console
  names in [setup.py](setup.py), and existing argument aliases unless the task
  calls for changing that interface. Trace consumers before changing request
  shapes, return values, or failure behavior.
- Server method names and positional argument order are wire contracts. This
  repository contains clients, not the server definitions. Local mocks establish
  client behavior; they do not prove compatibility with a deployed server.
- Confirm helpers against implementation and callers. Some historical examples in
  [getting_started.rst](docs/source/getting_started.rst) reference removed methods;
  they are not evidence that an API still exists. Keep unrelated modernization
  outside the requested change.

## Build and dependencies

[setup.py](setup.py) declares Python support and console entry points. It reads
both [requirements.txt](requirements.txt) and an ignored, generated
`requirements-internal.txt` even for package metadata. The latter comes from
[requirements-internal.txt.envtpl](requirements-internal.txt.envtpl) with an actual
`OPENAPI_VERSION`. Obtain the required version from the task or build context;
do not invent one or silently remove `odm-api` to make installation pass.

[Earthfile](Earthfile) defines the maintained container targets. `+test` resolves
that dependency and runs tox; `+build` also substitutes `SDK_VERSION` into
[version.py](odm_sdk/version.py) using its
[template](odm_sdk/version.py.envtpl) before making the source distribution.
The checked-in `version.py` also supports an environment override. Preserve both
paths when changing version behavior.

The default Earthly `main` builds `+push`, which uploads to PyPI or TestPyPI.
Use an explicit target for testing; do not invoke the default target as a local
check. Read the target and its dependencies before execution.

[tox.ini](tox.ini) defines the Python test matrix and skips missing interpreters.
The container carries one interpreter. [uv.toml](uv.toml) disables interpreter
downloads and gives PyPI priority before falling back to TestPyPI for missing
versions. Preserve this resolution behavior when changing dependency tooling;
pip's extra-index resolution is not equivalent.

Package data rules live in [MANIFEST.in](MANIFEST.in). Changes to template schemas
or internal dictionary data must remain present in the source distribution.
[CODEOWNERS](.github/CODEOWNERS) is Terraform-managed.

## Validation and completion

With the runtime and test dependencies available, run `python3 -m pytest
odm_sdk/tests` from the repository root, or target the affected test module.
`python3 -m tox` additionally exercises packaging and the available interpreters;
it needs the generated internal requirement and build dependencies described
above. A skipped tox interpreter is not coverage for that Python version.

The checked-in tests use `unittest`, pytest, and `requests_mock`; they do not need
a live ODM instance. For changed HTTP behavior, assert the request as well as the
result, including authentication, path, payload, and rejection behavior relevant
to the change. Use synthetic credentials and mock settings/keyring access when
testing account configuration.

Run the hooks in [.pre-commit-config.yaml](.pre-commit-config.yaml) with explicit
changed paths, including new files, and inspect any fixes. The
[GitHub workflow](.github/workflows/pre-commit.yml) runs these hooks for ready
pull requests targeting `develop`; it does not run pytest. Documentation-only
instruction edits need link and whitespace checks, not an application build.

Report the changed contracts, checks actually run, and missing prerequisites or
runtime evidence. Do not substitute a live import, delete, share, or user-setup
command for a local check: those commands mutate remote data or local credentials.

## Documentation sources

Sphinx input is under [docs/source](docs/source/index.rst). API reference content
comes from Python docstrings through [api_reference.rst](docs/source/api_reference.rst).
For public behavior changes, update the affected docstring or maintained source.
Check signatures against code rather than copying the older getting-started examples.

The maintained local build is `make -C docs html`, defined in
[docs/Makefile](docs/Makefile). It needs Sphinx extensions from
[docs/requirements.txt](docs/requirements.txt), including `sphinx_markdown_builder`
and `future`, which the shorter root `requirements-docs.txt` does not include.
[Read the Docs](.readthedocs.yaml) also uses `docs/requirements.txt`.

[conf.py](docs/source/conf.py) imports the SDK and calls
[make_shell_docs.py](docs/source/make_shell_docs.py). This executes the shell
module definitions and writes `docs/source/scripts/odm-shell.rst` and
`odm-user-setup.rst` from parser help. Change the parsers in
[shell.py](odm_sdk/scripts/shell.py), [user_setup.py](odm_sdk/scripts/user_setup.py),
or their [shared framework](odm_sdk/shell.py), rather than editing generated help.
Keep module imports and parser construction free of new network or mutation effects.
