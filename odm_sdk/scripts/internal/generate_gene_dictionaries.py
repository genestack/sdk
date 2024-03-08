# -*- coding: utf-8 -*-

import argparse
import ftplib
import csv
import gzip
import os
import re
import shutil
import time

from collections import defaultdict
from subprocess import check_call

# This script combines code from initialise_raw_gene_dictionary.py and gene_dictionary_creation.py,
# previously located in unified repo. Look up their history there for reference.
# It primarily adapts initialise_raw_gene_dictionary.py, excluding the use of raw file metadata.
# Instead, it incorporates get_ensembl_organisms from gene_dictionary_creation.py.

MAIN_FILE_NAME = 'gene_ensembl__translation__main'
FIRST_COLUMN_NAMES = ['label', 'gene_symbol', 'ensembl_transcript_id', 'ensembl_protein_id', 'description']

# to comply with the Genestack CSV initializer which uses the default 'excel' dialect
ROW_ENTRY_SEPARATOR = ','
TERM_SEPARATOR = ','
BASE_ENSEMBL_FTP = 'ftp://ftp.ensembl.org/pub/release-99/mysql/ensembl_mart_99/'
ENSEMBL_SCHEMA_FILE = 'ensembl_mart_99.sql.gz'
BASE_NCBI_FTP = 'https://ftp.ncbi.nlm.nih.gov/'
NCBI_GENE_DATA_FOLDER = 'gene/DATA/'
NCBI_GENE_INFO_FILENAME = 'gene_info'
NCBI_GENE_INFO_FILENAME_GZ = 'gene_info.gz'


ORGANISMS_TO_LOAD_GENE_SYNONYMS = [
    'Bos taurus',
    'Canis familiaris',
    'Cricetulus griseus chok1gshd',
    'Danio rerio',
    'Homo sapiens',
    'Macaca fascicularis',
    'Mus musculus',
    'Oryctolagus cuniculus',
    'Rattus norvegicus',
    'Sus scrofa'
]

# Common files
DATASET_NAMES_TABLE_GZ = 'dataset_names.txt.gz'
COMMON_FILES = ['dataset_names']

# Organism specific files
DATABASE_FILES = [
    {
        'name': 'gene_ensembl__ox_reactome_gene__dm',
        'columns': {
            'description_1074': 'reactome_pathway_name',
            'display_label_1074': 'reactome_pathway_id'
        },
        # name of the column on which to perform the JOIN
        # (identical in this file and the create_files file)
        'join_key': 'gene_id_1020_key'
    },

    {
        'name': 'gene_ensembl__ox_entrezgene__dm',
        'columns': {
            'dbprimary_acc_1074': 'entrez_gene_id'
        },
        'join_key': 'gene_id_1020_key'
    },

    {
        'name': 'gene_ensembl__ox_uniprot_gn__dm',
        'columns': {
            'dbprimary_acc_1074': 'uniprot_symbol'
        },
        'join_key': 'gene_id_1020_key'
    },

    {
        'name': 'gene_ensembl__ox_hgnc__dm',
        'columns': {
            'description_1074': 'hgnc_description',
            'dbprimary_acc_1074': 'hgnc_id'
        },
        'join_key': 'gene_id_1020_key'
    },

    {
        'name': 'gene_ensembl__gene__main',
        'columns': {
            'name_1059': 'location',
        },
        'join_key': 'gene_id_1020_key'
    },

    {
        'name': 'gene_ensembl__ontology_go__dm',
        'columns': {
            'name_1006': 'go_term_label',
            'dbprimary_acc_1074': 'go_term_id'  # TODO what about GO category?
        },
        'join_key': ['transcript_id_1064_key', 'translation_id_1068_key']
    },

    {  # this is the create_files Ensembl database file
        'name': MAIN_FILE_NAME,
        'columns': {
            'stable_id_1070': 'ensembl_protein_id',
            'stable_id_1066': 'ensembl_transcript_id',
            'stable_id_1023': 'label',  # Ensembl gene ID
            'display_label_1074_r1': 'transcript_symbol',
            'display_label_1074': 'gene_symbol'
        }
    }
]


def get_ensembl_organisms():
    ensembl_ftp_host = 'ftp.ensembl.org'
    ensembl_ftp_mart_path = '/pub/release-99/mysql/ensembl_mart_99/'
    ensembl_ftp_parent_path = '/pub/release-99/mysql/'

    print("Retrieving list of organisms from Ensembl FTP...")
    ftp = ftplib.FTP(ensembl_ftp_host)
    ftp.login('anonymous', 'anonymous')

    # get the list of downloadable database dumps
    files_listing = ftp.nlst(ensembl_ftp_mart_path)
    to_upload = set(os.path.basename(path).split('_')[0] for path in files_listing
                    if os.path.basename(path).endswith('.txt.gz'))
    to_upload.discard('meta')
    to_upload.discard('dataset')

    # use the parent directory listing to match the names of these database dump files
    # to the full name of the corresponding organisms
    files_listing_parent_directory = ftp.nlst(ensembl_ftp_parent_path)
    organisms = {}
    for path in files_listing_parent_directory:
        split_name = os.path.basename(path).split('_')

        for i, part in enumerate(split_name):
            short_name = split_name[0][0] + split_name[i]
            if short_name in to_upload:
                display_name = ' '.join(map(str, split_name[0:(i + 1)]))
                display_name = display_name[0].upper() + display_name[1:]
                organisms[short_name] = display_name
                break

    print('\tTotal short names found: %s' % len(to_upload))
    for short_name in to_upload:
        if short_name not in organisms:
            print('\t[WARNING] No display name found for short name: %s' % short_name)
    print('\tTotal organisms found: %s' % len(organisms))
    return sorted(organisms.items())


def multiple_attempts(exception_to_raise, max_attempts=3, delay=3, backoff=1):
    """A decorator to retry a function call many times."""

    def _multiple_attempts(function):
        def wrapper(*args, **kwargs):
            n_attempts = 0
            next_attempt_delay = delay
            while True:
                try:
                    return function(*args, **kwargs)
                except Exception as e:
                    n_attempts += 1
                    if n_attempts > max_attempts:
                        if exception_to_raise:
                            print("Received exception: %s" % e)
                            raise exception_to_raise
                        raise
                    time.sleep(next_attempt_delay)
                    next_attempt_delay *= backoff
                    print("Retrying...")

        return wrapper
    return _multiple_attempts


def update_list_dict(dic1, dic2):
    # Update list-valued dictionary like this:
    # { 1: [2,3], 2: [5] } + {1: [4,6], 3: [2]} ==> {1: [2,3,4,6], 2: [5], 3: [2]}
    # (in contrast, the method dict.update will just overwrite instead of merging)
    for key, values in dic2.items():
        dic1[key] += values


def unique_list(lst):
    # remove duplicate entries from a list whilst preserving order:
    # [1, 5, 3, 5, 2, 1] -> [1, 5, 3, 2]
    already_seen = set()
    output = []
    for elem in lst:
        if elem not in already_seen:
            already_seen.add(elem)
            output.append(elem)
    return output


def quote_item_if_contains_comma(item):
    """If term contains comma itself, it shoud be quoted before writing into .csv."""
    return '"' + item + '"' if ',' in item else item


def prepare_cell(items):
    """
    We construct cell from list of items (str) that quoted and joined via separator.
    """
    return TERM_SEPARATOR.join(quote_item_if_contains_comma(item) for item in items)


def prepare_csv_row(row):
    """
    row = ['1', ['2', '3'], ['4', '5, 6', '7']] ==> ['1', '2,3', '4,"5, 6",7'].
    Such format of csv row is expected by genestack OntologyCsvInitializer.java class
    :param row: preliminary representation of the csv row
    :type row: list[list[str]]
    :return: list[str]
    """
    return [prepare_cell(items) for items in row]


@multiple_attempts(exception_to_raise=None, max_attempts=10, delay=1, backoff=2)
def download_file(url, local_target):
    # For some reason downloading with urllib/urllib2 is very slow:
    # urllib.urlretrieve(url, local_target)
    print('\tDownloading: %s' % local_target)

    tmp_name = '%s.download' % local_target
    check_call("curl -s '%s' --output '%s'" % (url, tmp_name), shell=True)

    if os.path.isfile(local_target):
        os.remove(local_target)
    shutil.move(tmp_name, local_target)


def parse_ensembl_mart_schema():
    schema_dict = {}
    print('Parsing Ensembl mart schema...')
    local_file = ENSEMBL_SCHEMA_FILE
    download_file(BASE_ENSEMBL_FTP + ENSEMBL_SCHEMA_FILE, local_file)
    selected_file_names = set(descriptor['name'] for descriptor in DATABASE_FILES)

    with gzip.open(local_file, mode='rt', encoding='utf-8') as sql_file:
        table_entries = {}
        skip_current_table = False
        col_counter = -1
        table_name = None

        for line in sql_file:
            # if we get to a new table declaration
            if line.startswith('CREATE TABLE'):
                col_counter = 0
                # if a previous table was parsed, store the parsed info in `schema_dict`
                if len(table_entries) > 0:
                    schema_dict[table_name] = table_entries
                    table_entries = {}

                table_name = re.search(r'CREATE TABLE `(.*)`', line).group(1)
                table_type = table_name.split('_', 1)[1]  # remove the organism
                skip_current_table = (table_type not in selected_file_names) and (table_name not in COMMON_FILES)

            elif skip_current_table:
                continue
            else:
                match = re.search(r'^\s+`(.*)`', line)
                if match is None:
                    continue
                col_name = match.group(1)
                # at the moment, we store the index mapping for *all* columns
                table_entries[col_name] = col_counter
                col_counter += 1

        if len(table_entries) > 0:
            schema_dict[table_name] = table_entries

    print('\tTotal tables used: %s' % len(schema_dict))

    return schema_dict


# TODO NCBI gene synonyms should be added to dictionary before initial write on disk
def add_gene_synonyms_from_ncbi(result_filename, taxonomy_id):
    """
    Add gene synonyms extracted from NCBI `gene_info` file to result .csv file
    :param result_filename: result .csv file where gene synonyms should be added
    :param taxonomy_id: taxonomy id of the organism used to extract organism specific rows from NCBI `gene_info` file
    :return: None
    """
    gene_synonyms_dict = load_gene_synonyms_dict(taxonomy_id)
    write_result_with_synonyms(result_filename, gene_synonyms_dict)


def load_gene_synonyms_dict(taxonomy_id):
    gene_synonyms_dict = {}
    with gzip.open(NCBI_GENE_INFO_FILENAME_GZ, mode='rt', encoding='utf-8') as gene_info_file:
        reader = csv.DictReader(gene_info_file, delimiter='\t')
        for row in reader:
            if row['#tax_id'] == taxonomy_id:
                gene_synonyms = row['Synonyms'].split('|') if row['Synonyms'] != '-' else []
                if row['Symbol_from_nomenclature_authority'] != '-':
                    gene_symbol = row['Symbol_from_nomenclature_authority']
                    if gene_symbol != row['Symbol']:
                        gene_synonyms.append(row['Symbol'])
                else:
                    gene_symbol = row['Symbol']
                gene_synonyms_dict[gene_symbol] = TERM_SEPARATOR.join(gene_synonyms)
    return gene_synonyms_dict


def load_taxonomy_dict(ensembl_column_mappings):
    species_col_index = ensembl_column_mappings['dataset_names']['name']
    tax_id_col_index = ensembl_column_mappings['dataset_names']['tax_id']

    download_file(BASE_ENSEMBL_FTP + DATASET_NAMES_TABLE_GZ, DATASET_NAMES_TABLE_GZ)
    with gzip.open(DATASET_NAMES_TABLE_GZ, mode='rt', encoding='utf-8') as dataset_names_file:
        reader = csv.reader(dataset_names_file, delimiter='\t')
        return {row[species_col_index]: row[tax_id_col_index] for row in reader}


def read_result_file(result_filename):
    with open(result_filename, 'rt', encoding='utf-8') as result_file:
        reader = csv.reader(result_file, delimiter=ROW_ENTRY_SEPARATOR)
        header = next(reader)
        result_file_content = list(reader)
    return header, result_file_content


def write_result_with_synonyms(result_filename, gene_synonyms_dict):
    header, result_file_content = read_result_file(result_filename)
    gene_symbol_index = header.index('gene_symbol')
    header.append('gene_synonyms')

    with open(result_filename, 'w') as result_file:
        writer = csv.writer(result_file, delimiter=ROW_ENTRY_SEPARATOR)
        writer.writerow(header)
        for row in result_file_content:
            gene_symbol = row[gene_symbol_index]
            row.append(gene_synonyms_dict.get(gene_symbol, ''))
            writer.writerow(row)


def get_foreign_key(col_names_to_indices, join_key):
    if not isinstance(join_key, list):
        join_key = [join_key]
    for possible_key in join_key:
        if possible_key in col_names_to_indices:
            return col_names_to_indices[possible_key]


def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Generates source files for gene dictionaries.')
    parser.add_argument('-ncbi', action='store_true', help='Generate only dictionaries with NCBI synonyms.')

    args = parser.parse_args()
    ncbi_patched_only = args.ncbi

    # download ncbi gene_info file in advance
    download_file(BASE_NCBI_FTP + NCBI_GENE_DATA_FOLDER + NCBI_GENE_INFO_FILENAME_GZ, NCBI_GENE_INFO_FILENAME_GZ)
    ensembl_column_mappings = parse_ensembl_mart_schema()
    taxonomy_dict = load_taxonomy_dict(ensembl_column_mappings)
    output_columns = FIRST_COLUMN_NAMES
    for dic in DATABASE_FILES:
        for value in dic['columns'].values():
            if value not in FIRST_COLUMN_NAMES:
                output_columns.append(value)

    for species, organism_name in get_ensembl_organisms():
        if ncbi_patched_only and organism_name not in ORGANISMS_TO_LOAD_GENE_SYNONYMS:
            continue
        secondary_files_data = []

        # dictionary: Ensembl gene id -> dictionary of gene info
        final_data = defaultdict(lambda: defaultdict(list))

        for file_descriptor in DATABASE_FILES:
            # for each of the secondary files for the current species
            # (i.e. not the create_files Ensembl file),
            # store the contents of the file in a dict where keys are the foreign DB keys,
            # and values are lists of dictionaries corresponding to the matching rows in the file.
            # Then, when we get to the create_files file (MAIN_FILE),
            # we combine its data with the data we stored in
            # memory for all the other files and write to the output CSV file

            is_main_file = file_descriptor['name'] == MAIN_FILE_NAME
            file_name = '%s_%s.txt.gz' % (species, file_descriptor['name'])
            file_data = defaultdict(list)
            col_names_to_indices = ensembl_column_mappings.get('%s_%s' % (species, file_descriptor['name']))

            if col_names_to_indices is None:
                print('\tFile `%s_%s` not found in SQL schema' % (species, file_descriptor['name']))
                continue

            if not is_main_file:
                foreign_key_id = get_foreign_key(col_names_to_indices, file_descriptor['join_key'])

            local_name = file_name
            download_file(BASE_ENSEMBL_FTP + file_name, local_name)

            if is_main_file:
                print('\tWriting species dictionary...')

            with gzip.open(local_name, mode='rt', encoding='cp1251') as txt_file:
                csv_reader = csv.reader(txt_file, delimiter='\t')
                for entry in csv_reader:
                    row_dictionary = defaultdict(list)
                    for input_name, output_name in file_descriptor['columns'].items():
                        col_index = col_names_to_indices[input_name]
                        if col_index < len(entry) and entry[col_index] and entry[col_index] != '\\N':
                            row_dictionary[output_name].append(entry[col_index])

                    if is_main_file:
                        if 'label' not in row_dictionary:
                            # if the row doesn't correspond to a "ENSGxxxxxx", skip it
                            continue
                        # add to the current row dictionary the data collected from the other 2ary files
                        for j, secondary_file_data in enumerate(secondary_files_data):
                            # do the JOIN operation
                            foreign_key_value = \
                                entry[get_foreign_key(col_names_to_indices, DATABASE_FILES[j]['join_key'])]
                            if foreign_key_value in secondary_file_data:
                                for secondary_row_dict in secondary_file_data[foreign_key_value]:
                                    # each `secondary_row_dict` corresponds to a row from the secondary file
                                    # which matches the current gene
                                    # (there can be many such rows, e.g. for GO terms)
                                    update_list_dict(row_dictionary, secondary_row_dict)

                        # update the primary file's dictionary
                        ensembl_gene_id = row_dictionary['label'][0]
                        update_list_dict(final_data[ensembl_gene_id], row_dictionary)
                    else:
                        # not the create_files file
                        # It is not main file so foreign_key_id is assigned
                        # noinspection PyUnboundLocalVariable
                        foreign_key_value = entry[foreign_key_id]
                        file_data[foreign_key_value].append(row_dictionary)

            if not is_main_file:
                secondary_files_data.append(file_data)

        # write to output dictionary
        result_name = '%s.csv' % organism_name

        with open(os.path.join(result_name), 'w') as species_file:
            output_writer = csv.writer(species_file, delimiter=ROW_ENTRY_SEPARATOR)
            output_writer.writerow(output_columns)
            for row_dict in final_data.values():
                row = prepare_csv_row(unique_list(row_dict[key]) for key in output_columns)
                output_writer.writerow(row)

        # Add gene synonyms here
        if organism_name in ORGANISMS_TO_LOAD_GENE_SYNONYMS:
            add_gene_synonyms_from_ncbi(os.path.join(result_name), taxonomy_dict[species])


if __name__ == "__main__":
    main()
