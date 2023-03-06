from genestack_client import (DataImporter, FilesUtil, SpecialFolders, get_connection)

connection = get_connection()
fu = FilesUtil(connection)
parent = fu.get_folder(fu.get_special_folder(SpecialFolders.CREATED),
                       'Data samples', 'Reference genome', create=True)

assembly = 'GRCh38',
release = '109',
organism = 'Homo sapiens'
gtf_url = 'https://ftp.ensembl.org/pub/release-109/gtf/homo_sapiens/Homo_sapiens.GRCh38.109.gtf.gz'

accession = DataImporter(connection).create_reference_genome(
    parent, name='name',  # change me
    description='description',  # change me
    organism=organism,
    assembly=assembly,
    release=release,
    annotation_url=gtf_url
)

print(f'Reference genome id: {accession}')
