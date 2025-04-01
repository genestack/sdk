#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys

from odm_sdk import Metainfo
from odm_sdk.scripts.utils import colored, RED, YELLOW

ACCESSION = {
    "isRequired": True,
    "metainfoType": "com.genestack.api.metainfo.StringValue",
    "name": Metainfo.ACCESSION,
    "isReadOnly": True,
    "description": "Genestack-generated accession"
}
DATA_CLASS = {
    "isRequired": True,
    "metainfoType": "com.genestack.api.metainfo.StringValue",
    "name": Metainfo.DATA_CLASS,
    "isReadOnly": True,
    "description": "Technical field specifying the exact type of data you have uploaded."
}
FEATURES_STRING = {
    "isRequired": False,
    "metainfoType": "com.genestack.api.metainfo.StringValue",
    "name": Metainfo.FEATURES_STRING,
    "isReadOnly": True,
    "description": "If your dataset contains multiple columns for feature, "
                   "this parameter lists columns with text content (e.g., Gene Name)."
}
FEATURES_NUMERIC = {
    "isRequired": False,
    "metainfoType": "com.genestack.api.metainfo.StringValue",
    "name": Metainfo.FEATURES_NUMERIC,
    "isReadOnly": True,
    "description": "Technical field for dataset containing multiple columns for feature, "
                   "this parameter lists columns with numeric content "
                   "(e.g., Retention Time, M/Z ratio)."
}
VALUES_NUMERIC = {
    "isRequired": False,
    "metainfoType": "com.genestack.api.metainfo.StringValue",
    "name": Metainfo.VALUES_NUMERIC,
    "isReadOnly": True,
    "description": "Technical field for dataset containing multiple measurement or value types "
                   "for each item (like a sample, library, or preparation), "
                   "this parameter lists these (e.g. Intensity, Fold Change, p-value)."
}

__required_data_types = {
    Metainfo.ACCESSION: [],  # empty list means that this field is required for all data types
    Metainfo.DATA_CLASS: [
        'genestack:transcriptomicsParent',
        'genestack:genomicsParent',
        'genestack:facsParent'
    ],
    Metainfo.FEATURES_STRING: ['genestack:transcriptomicsParent'],
    Metainfo.FEATURES_NUMERIC: ['genestack:transcriptomicsParent'],
    Metainfo.VALUES_NUMERIC: ['genestack:transcriptomicsParent']
}

__items_by_name = {
    Metainfo.ACCESSION: ACCESSION,
    Metainfo.DATA_CLASS: DATA_CLASS,
    Metainfo.FEATURES_STRING: FEATURES_STRING,
    Metainfo.FEATURES_NUMERIC: FEATURES_NUMERIC,
    Metainfo.VALUES_NUMERIC: VALUES_NUMERIC
}

__item_positions_by_name = {
    Metainfo.ACCESSION: 0,
    Metainfo.DATA_CLASS: 1,
    # -1 means that the field should be added at the end of the list
    Metainfo.FEATURES_STRING: -1,
    Metainfo.FEATURES_NUMERIC: -1,
    Metainfo.VALUES_NUMERIC: -1
}


def validate_content(content):
    for item in content:
        field_name = item['name']
        data_type = item['dataType']
        data_types = __required_data_types.get(field_name)
        if data_types is not None and _contains_data_type(data_types, data_type):
            technical_item = _with_data_type(__items_by_name[field_name], data_type)
            if _equals_ignoring_description(item, technical_item):
                print(colored(f'Template field "{field_name}" of type "{data_type}" '
                              f'is predefined and can be omitted.', YELLOW))
            else:
                print(colored(f'Template field "{field_name}" of type "{data_type}" '
                              f'is predefined and cannot be edited.', RED), file=sys.stderr)
                sys.exit(1)


def enrich_items(data_type, data_type_items):
    copied_items = data_type_items.copy()
    for field_name, data_types in __required_data_types.items():
        if _contains_data_type(data_types, data_type):
            technical_item = _with_data_type(__items_by_name[field_name], data_type)
            if not any(_equals_ignoring_description(item, technical_item)
                       for item in data_type_items):
                position = __item_positions_by_name[field_name]
                if position != -1:
                    copied_items.insert(position, technical_item)
                else:
                    copied_items.append(technical_item)
    return copied_items


def _contains_data_type(data_types, data_type):
    return len(data_types) == 0 or data_type in data_types


def _with_data_type(field_to_copy, data_type):
    new_field = field_to_copy.copy()
    new_field['dataType'] = data_type
    return new_field


def _equals_ignoring_description(item_fst, item_snd):
    fst_copy = item_fst.copy()
    snd_copy = item_snd.copy()
    fst_copy.pop('description', None)
    snd_copy.pop('description', None)
    return fst_copy == snd_copy
