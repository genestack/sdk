from odm_sdk import get_connection, Metainfo
from odm_sdk.scripts.dictionaries.load_init_share_dictionaries import load_dictionary

def upload_disease():

    # Upload Disease Ontology
    disease_ontology = {
        'name': 'Disease Ontology - DOID',
        'url': 'https://odm-init.s3.amazonaws.com/dictionaries/odm-12611/doid.owl',
        'description': 'Classification of human diseases by etiology. Domain: Diseases / Human Health, Version: 2025-05-30. The original data is available via the link https://purl.obolibrary.org/obo/doid/releases/2025-05-30/doid.owl'
    }
    connection = get_connection()
    disease_ontology_accession = load_dictionary(connection, disease_ontology)

    # Upload Disease Ontology Extended with reference to Disease Ontology
    metainfo = Metainfo()
    metainfo.add_file_reference("genestack.dictionary:parent", disease_ontology_accession)
    disease_ontology_extended = {
        'name': 'Disease Ontology Extended',
        'url': 'https://odm-init.s3.amazonaws.com/dictionaries/odm-12611/disease_extension.csv',
        'description': 'Classification of human diseases by etiology enriched by term "Healthy" and its synonyms. Domain: Diseases / Human Health, Version: 2025-05-30, extended by term "Healthy". The original data is available via the link https://purl.obolibrary.org/obo/doid/releases/2025-05-30/doid.owl'
    }
    load_dictionary(connection, disease_ontology_extended, metainfo=metainfo)


def upload_gene_ontology():

    gene_ontology = {
        "name": "Gene Ontology - GO",
        "url": "https://odm-init.s3.amazonaws.com/dictionaries/odm-12611/go.owl",
        "description": "Describes gene functions: biological process, molecular function, cellular component. Domain: Molecular Function / Biological Process, Version: 2024-11-03. The original data is available via the link https://purl.obolibrary.org/obo/go/releases/2024-11-03/extensions/go-plus.owl"
    }

    connection = get_connection()
    metainfo = Metainfo()
    metainfo.add_string(Metainfo.DATA_TYPE, 'Gene Ontology')
    load_dictionary(connection, gene_ontology, metainfo=metainfo)


def main():
    """
    Currently we don't support metainfo parsing via auxiliary scripts from json in proper way.
    In the future we have to add this possibility and rework script to using only CLI call.
    """
    upload_disease()
    upload_gene_ontology()


if __name__ == '__main__':
    main()
