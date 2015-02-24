Importers
*********


First step you need connection::

    >>> from genestack import get_connection
    >>> connection = get_connection()

To import data instantiate data importer with connection::

    >>> from genestack import DataImporter
    >>> importer = DataImporter(connection)

Create experiment in ``Imported files``::

    >>> experiment = importer.create_experiment(name='Sample of paired-end reads from A. fumigatus WGS experiment',
    ... description='A segment of a paired-end whole genome sequencing experiment of A. fumigatus')


Add sequencing assay for experiment. Use local files as sources::


    >>> assay = importer.create_sequencing_assay(experiment,
    ...                                          name='Test paired-end sequencing of A. fumigatus',
    ...                                          links=['ds1.gz', 'ds2.gz'],
    ...                                          organism='Aspergillus fumigatus',
    ...                                          method='genome variation profiling by high throughput sequencing')
    Uploading ds1.gz - 100.00%
    Uploading ds2.gz - 100.00%

To find out file in system print result::

    >>> print 'Successfully load assay with accession', assay, 'to experiment', experiment
    Successfully load assay with accession GSF000002 to experiment GSF000001

Start file initialization::

    >>> from genestack import FileInitializer
    >>> initializer = FileInitializer(connection)
    >>> initializer.initialize([assay])
    >>> print 'Start initialization of', assay
    Start initialization of GSF000002

As result you will have:

   - ``Experiment`` folder in ``Imported files``
   - ``Sequencing assay`` file in experiment
   - Two ``Raw Upload`` files in ``Uploaded files`` folder. This is your local files located on genestack storage.
     You can remove them after initialization of assay.


Supported url formats
=====================
   There is no difference between file and gzipped file for system, both packed and unpacked files will produce same result.
   if protocol is not specified ``file://`` will be used

* ``file://``:
    - ``test.txt.gz``
    - ``file://test.txt``

* ``ftp://``
    - ``ftp://server.com/file.txt``

* ``http://`` ``https://``
    - ``http://server.com/file.txt``

* ``ascp://``
    - ``ascp://<user>@<server>:file.txt``
