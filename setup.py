from setuptools import setup, find_packages
import re

regex = re.compile(r'^--.*$')
# Read requirements file to download deps with filtering params.
with open('requirements.txt') as f:
    required = [line for line in f.read().splitlines() if not regex.match(line)]

with open('requirements-internal.txt') as f:
    required_internal = [line for line in f.read().splitlines() if not regex.match(line)]

# Import version directly, without execute __init__.py script
exec(open('odm_sdk/version.py').read())

setup(
    name='odm-sdk',
    install_requires=required + required_internal,
    version=__version__,
    packages=find_packages(),
    url='https://github.com/genestack/sdk',
    license='MIT',
    author='Genestack Limited',
    author_email='',
    description='SDK for interacting with the Open Data Manager',
    long_description=__doc__,
    long_description_content_type="text/markdown",
    keywords=['genestack', 'odm', 'import', 'share', 'create',
              'delete', 'curate', 'genomics', 'api'],
    include_package_data=True,
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'odm-user-setup = odm_sdk.scripts.user_setup:main',
            'odm-shell = odm_sdk.scripts.shell:main',
            'odm-import-data = odm_sdk.scripts.import_ODM_data:main',
            'odm-create-users = odm_sdk.scripts.users.create_users:main',
            'odm-update-template = odm_sdk.scripts.metainfo_templates.update_template:main',
            'odm-delete-template = odm_sdk.scripts.delete_study_or_template:main',
            'odm-update-dictionary = odm_sdk.scripts.dictionaries.load_init_share_dictionaries:main',
            'odm-curate-study = odm_sdk.scripts.study_management.create_curation_file:main',
            'odm-delete-study = odm_sdk.scripts.delete_study_or_template:main',
            'odm-share-study = odm_sdk.scripts.study_management.share_study_with_group:main',
            'odm-geo-prepare = odm_sdk.scripts.study_management.GEO_prepare:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],

    project_urls={
        'Documentation': 'https://genestack-client.readthedocs.io/en/stable/',
        'Source': 'https://github.com/genestack/python-client/',
        'Tracker': 'https://github.com/genestack/python-client/issues',
    },
)
