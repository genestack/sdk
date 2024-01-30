# Description

This directory contains metainfo templates, dictionaries that these templates use, and some
command line scripts for uploading these templates and dictionaries.

# Repository structure

```
.
│
└─── update_templates.py (command line script for updating templates)
│   
└─── importers (package with template importers code)
│   │
│   └─── schemas (JSON schemas for validating input)
│   │   │   ...
│   │     
│   └─── settings (folder with files that contain information about the upload process)    
│       │   ...
│
└─── templates (folder with templates)
     │   ...
```

# How to use

Modify (update) templates as the same user (account) which uploaded them initially, 
otherwise applications that use these templates might be broken.

In order to update templates, execute one the following commands below:

## Default template

* Local installations:

```
python update_templates.py -u public importers/settings/test/default_template_settings.json
```

* `staging` and `production`: 

Should be performed during platform update under the user who uploads applications.

```
python update_templates.py \
    -H <platform_address> -u <user_email> -p <user_password> \
    importers/settings/genestack/default_template_settings.json
```

Script to delete templates is `delete_template_without_limitations.py`

# Configuration file format

When running the `update_template.py` script it must be provided with a configuration file. A 
configuration file must contain a single JSON object with the following content:

```
"template_path": Local filesystem path to the JSON file with template content. 
                 Must be relative to repository root;
                 
"template_name": Name of the Genestack file that will be used when the template is uploaded to the 
                 platform;

"replace" [optional]: When 'true' the uploaded template will replace the existing one (if any). 
                      When 'false' - an exception will be thrown if a template with the same name 
                      exists;
 
"mark_default" [optional]: When 'true' the uploaded template will be set as the default template;
```
