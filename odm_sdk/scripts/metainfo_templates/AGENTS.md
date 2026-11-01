# Template imports

This guide applies to `odm_sdk/scripts/metainfo_templates/`. It inherits the
[CLI guide](../AGENTS.md), [SDK guide](../../AGENTS.md), and
[root validation requirements](../../../AGENTS.md#validation-and-completion).

## Configuration and replacement

[update_template.py](update_template.py) takes one or more config paths and uses
the shared RPC connection parser. [TemplateImporter](importers/template_importer.py)
validates configuration with [config_schema.json](importers/schemas/config_schema.json),
then template fields with [template_schema.json](importers/schemas/template_schema.json).
Keep schemas, Python signatures, and outgoing fields aligned. The config schema
permits extra properties, but `_create_from_config` has explicit named parameters;
schema acceptance alone does not prove a config can be imported.

`template_path` is opened directly by [json_validation.load_json](importers/json_validation.py).
Relative paths resolve from the working directory, not the config file's folder.
The config schema describes repository-root-relative paths, so use the repository
root for that convention. Schemas themselves resolve relative to the module.

`TemplateImporter` construction finds or creates the Import Templates folder.
Do not instantiate it against a live connection as a validation-only operation.
Existing template lookup searches public, import-template, and created folders
and calls `loadTemplate` to verify the candidate. `replace=True` reuses the found
accession; without replacement it prints a message and returns without updating.
`mark_default` runs only after an accession was created or reused.

The established [README](README.md#how-to-use) requires updating as the account
that originally uploaded the template. Preserve that ownership constraint. Its
command and directory examples are historical; use `setup.py` and current source
for executable names and behavior. Permission errors recognize both
`Template Administrator` and legacy `MANAGE_TEMPLATES`, print a hint, and re-raise.

## Field and dictionary contracts

Before writing fields, `validate_content` in
[template_technical_fields.py](importers/template_technical_fields.py) rejects
changes to predefined technical fields except for descriptions. `enrich_items`
adds fields applicable to each data type without duplicating existing matching
fields. Missing Accession and Data Class fields are inserted first and second
when applicable; missing feature fields go last for transcriptomics. Existing
matching fields keep their positions. Preserve applicability, insertion order,
description tolerance, and idempotence.

`_put_content` copies fields, replaces dictionary name/path with a resolved
`dictionaryAccession`, groups by `dataType`, enriches each group, and calls
`setKeyInfosForFileKind`. [DictionarySearch](importers/dictionary_search.py)
defaults to public `Dictionaries`; an explicit relative path starts at the home
folder. A missing named dictionary raises `GenestackException`; keep that failure
instead of silently dropping the association.

[test_template_technical_fields.py](../../tests/test_template_technical_fields.py)
covers technical-field rejection, ordering, data types, descriptions, and repeated
enrichment. It does not cover config loading, dictionary lookup, replacement, or
server writes. For changes there, mock the RPC calls and cover the affected path;
use the [root packaging guidance](../../../AGENTS.md#build-and-dependencies) when
adding or moving schemas.
