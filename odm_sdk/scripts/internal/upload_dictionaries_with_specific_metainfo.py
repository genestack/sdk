import os
from odm_sdk import get_connection, Metainfo
from odm_sdk.scripts.dictionaries.load_init_share_dictionaries import (load_dictionary, sharing,
                                                                                   initialization)


def get_path(path):
    return os.path.join(os.path.dirname(__file__), 'data', path)


def upload_disease():

    # Upload Disease Ontology
    disease_ontology = {
        'name': 'Disease Ontology',
        'url': 'https://odm-init.s3.amazonaws.com/dictionaries/with_specific_metainfo/doid.owl',
        'description': 'An ontology for describing the classification of human diseases organized by etiology. '
                       'The original file is available at http://purl.obolibrary.org/obo/doid.owl'
    }
    connection = get_connection()
    disease_ontology_accession = load_dictionary(connection, disease_ontology)
    sharing(connection, [disease_ontology_accession])
    initialization(connection, [disease_ontology_accession])

    # Upload Disease Ontology Extended with reference to Disease Ontology
    metainfo = Metainfo()
    metainfo.add_file_reference("genestack.dictionary:parent", disease_ontology_accession)
    disease_ontology_extended = {
        'name': 'Disease Ontology Extended',
        'url': 'https://odm-init.s3.amazonaws.com/dictionaries/with_specific_metainfo/disease_extension.csv',
        'description': 'An ontology for describing the classification of human diseases organized by etiology.'
                       ' The original file is available at http://purl.obolibrary.org/obo/doid.owl'
    }
    disease_ontology_extended_accession = load_dictionary(connection, disease_ontology_extended, metainfo=metainfo)
    sharing(connection, [disease_ontology_extended_accession])
    initialization(connection, [disease_ontology_extended_accession])


def upload_gene_ontology():

    gene_ontology = {
        "name": "Gene Ontology",
        "url": "https://odm-init.s3.amazonaws.com/dictionaries/with_specific_metainfo/go.owl",
        "description": "A controlled vocabulary describing the gene functions according to three aspects: "
                       "biological process, molecular function and cellular component. "
                       "The original file is available at http://purl.obolibrary.org/obo/go.owl"
    }

    connection = get_connection()
    metainfo = Metainfo()
    metainfo.add_string(Metainfo.DATA_TYPE, 'Gene Ontology')
    gene_ontology_accession = load_dictionary(connection, gene_ontology, metainfo=metainfo)
    sharing(connection, [gene_ontology_accession])
    initialization(connection, [gene_ontology_accession])


def main():
    """
    Currently we don't support metainfo parsing via auxiliary scripts from json in proper way.
    In the future we have to add this possibility and rework script to using only CLI call.
    """
    upload_disease()
    upload_gene_ontology()


if __name__ == '__main__':
    main()
