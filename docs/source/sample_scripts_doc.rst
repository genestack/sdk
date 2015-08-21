Sample Scripts
##############

This section provides reusable examples of scripts that allow you to perform actions on Genestack that would be tedious to accomplish through the web interface, such as multiple file uploads with custom metadata.

Uploading multiple files with custom metainfo
---------------------------------------------

A typical situation when you want to upload data is that you have some raw sequencing files somewhere (on an FTP site, on your local computer, etc.) and a spreadsheet with information about these files, that you would want to record in Genestack.

So let's imagine that we have a comma-delimited CSV file with the following format:

.. code-block:: none

    name,organism,disease,link
    HPX12,Homo sapiens,lung cancer,ftp://my.ftp/raw_data/HPX12_001.fq.gz
    HPZ24,Homo sapiens,healthy,ftp://my.ftp/raw_data/HPZ24_001.fq.gz
    .........

Now let's write a Python script that uses the Genestack Client Library to upload these files to
a Genestack instance, with the right metainfo. The script will take as input the CSV file,
and create a Genestack Experiment with a Sequencing Assay for each row of the CSV file.

.. literalinclude:: sample_scripts/make_experiment_from_csv.py
    :linenos:
    :language: python

This script uses many features from the client library:

    * we start by adding arguments to the argument parser to process our metadata file
    * then we establish a connection to Genestack, and instantiate a ``DataImporter`` to be able to create our files on Genestack
    * we create the experiment where we will store our data
    * we parse the CSV file using a Python ``csv.DictReader``, create a new metainfo object for each row and a corresponding Sequencing Assay with that metainfo

We can then run the script like this:

.. code-block:: shell

    python make_experiment_from_csv.py --name "My experiment" --description "My description" my_csv_metadata_file.csv


The metainfo of each Sequencing Assay specified inside the CSV file needs to contain at least a ``name`` and valid ``link`` (either to a local or a remote file). By default, the experiment will be created inside the user's ``Imported Files`` folder on Genestack, since we haven't specified a folder.

.. note::

    One could easily extend this script to support two files per sample (in the case of paired-end reads).

Running a data analysis pipeline
--------------------------------

Generally, if you want to run multiple files through the same analysis pipeline, the easiest way to do it is using the Data Flow Editor through the web interface. This tool is powerful enough to cover most of the use cases you could think of.
However, some complex pipelines are not supported by the Data Flow Editor. In that case, you can write your own script to generate all the files on Genestack programatically.

Our script will take as input the Genestack accession of a folder containing Unaligned Reads files. It will then produce for each file :

    * a Mapped Reads file produced with Bowtie, possibly using a custom reference genome
    * a QC Report for the mapping
    * a Variant Calling file

To do this, we define a ``BatchFilesCreator`` class with some simple methods to create multiple files from a CLA. We also create a ``BowtieBatchFilesCreator`` inheriting from this class, that has additional logic to change the reference genome. You can easily adapt this logic to your own pipeline.

Here is the script:

.. literalinclude:: sample_scripts/run_vc_pipeline.py
    :linenos:
    :language: python

The script can then be called from a terminal with the following syntax:

.. code-block:: none

    python run_vc_pipeline.py -u <user_alias> --ref-genome <custom_ref_genome_accession> --name "My project name" <raw_reads_folder>

Note that the folder supplied as input to the script should **only** contain Unaligned Reads files.