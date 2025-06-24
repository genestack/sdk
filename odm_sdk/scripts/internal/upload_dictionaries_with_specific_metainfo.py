from odm_sdk import get_connection, Metainfo
from odm_sdk.scripts.dictionaries.load_init_share_dictionaries import (load_dictionary, sharing,
                                                                                   initialization)

def upload_disease():

    # Upload Disease Ontology
    disease_ontology = {
        'name': 'Disease Ontology - DOID',
        'url': 'https://odm-init.s3.ap-south-1.amazonaws.com/dictionaries/odm-12611/doid.owl',
        'description': 'Classification of human diseases by etiology. Domain: Diseases / Human Health, Version: 2025-05-30. The original data is available via the link https://purl.obolibrary.org/obo/doid/releases/2025-05-30/doid.owl'
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
        'url': 'https://odm-init.s3.ap-south-1.amazonaws.com/dictionaries/odm-12611/disease_extension.csv',
        'description': 'Classification of human diseases by etiology enriched by term "Healthy" and its synonyms. Domain: Diseases / Human Health, Version: 2025-05-30, extended by term "Healthy". The original data is available via the link https://purl.obolibrary.org/obo/doid/releases/2025-05-30/doid.owl'
    }
    disease_ontology_extended_accession = load_dictionary(connection, disease_ontology_extended, metainfo=metainfo)
    sharing(connection, [disease_ontology_extended_accession])
    initialization(connection, [disease_ontology_extended_accession])


def upload_gene_ontology():

    gene_ontology = {
        "name": "Gene Ontology - GO",
        "url": "https://odm-init.s3.ap-south-1.amazonaws.com/dictionaries/odm-12611/go.owl",
        "description": "Describes gene functions: biological process, molecular function, cellular component. Domain: Molecular Function / Biological Process, Version: 2024-11-03. The original data is available via the link https://purl.obolibrary.org/obo/go/releases/2024-11-03/extensions/go-plus.owl"
    }

    connection = get_connection()
    metainfo = Metainfo()
    metainfo.add_string(Metainfo.DATA_TYPE, 'Gene Ontology')
    gene_ontology_accession = load_dictionary(connection, gene_ontology, metainfo=metainfo)
    sharing(connection, [gene_ontology_accession])
    initialization(connection, [gene_ontology_accession])


def upload_gene_dictionaries():
    organisms_to_load = [
        'Bos taurus',
        'Danio rerio',
        'Homo sapiens',
        'Macaca fascicularis',
        'Mus musculus',
        'Oryctolagus cuniculus',
        'Rattus norvegicus',
        'Sus scrofa'
    ]
    connection = get_connection()
    dictionary_accessions = []

    for organism in organisms_to_load:
        gene_dict = {
            "name": organism + " genes",
            "url": "https://odm-init.s3.ap-south-1.amazonaws.com/dictionaries/gene-dictionaries/" +
                   organism.replace(" ", "+") + ".csv",
            "description": "Dictionary contains the following information about gene: Ensembl gene name and id, "
                           "Ensembl transcript name and id, Ensembl protein id, Reactome pathway name and id, "
                           "Entrez gene id, Uniprot symbol, HGNC gene id and description, GO term label and id."
        }

        metainfo = Metainfo()
        metainfo.add_string('genestack.dictionary:termType', 'gene')
        metainfo.add_string('Release', '99')
        metainfo.add_string('genestack.bio:organism', organism)
        gene_ontology_accession = load_dictionary(connection, gene_dict, metainfo=metainfo)
        dictionary_accessions.append(gene_ontology_accession)


    sharing(connection, dictionary_accessions)


def main():
    """
    Currently we don't support metainfo parsing via auxiliary scripts from json in proper way.
    In the future we have to add this possibility and rework script to using only CLI call.
    """
    upload_disease()
    upload_gene_ontology()
    # upload_gene_dictionaries()    "It was decided not to load outdated gene dictionaries"


if __name__ == '__main__':
    main()
