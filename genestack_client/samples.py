# coding=utf-8
from genestack_client import Application


class SampleLinker(Application):
    """
    Application for linking data files to samples.

    It operates with the following concepts:

    1. A study is a dataset (collection) of samples.
    2. A sample is a file that contains common metainfo that can be attached to files with data.
    3. When linking data files and samples, data files must be uploaded and put into an upload
       dataset. This dataset simplifies operations on these files in Genestack and provides data
       versioning. Upload dataset is linked to the study.
    4. When uploading files to the upload dataset, they are put inside this dataset and
       initialized. Each file's metainfo will contain a link to the according sample.

    A typical workflow might look like this:

    1. A study with samples is created via the Study Design application inside Genestack.
    2. Study number is generated and exported via the Study Design API.
    3. An upload dataset is created and linked to the provided study.
    4. Files with data are uploaded, linked to samples and initialized via the 'import_data' method.
    5. If some data files are considered corrupted or invalid, they can be removed using the
       'unlink_data' method.
    6. When all required data files are uploaded, data can be made visible to others by releasing
       the upload dataset using the 'release' method.

    NOTE: This API is currently in Beta stage and is a subject to change, so no backwards
    compatibility is guaranteed at this point.
    """

    APPLICATION_ID = 'genestack/sample-linker'

    def create_upload_dataset(self, study_number, file_type, **kwargs):
        """
        Create a dataset that will later be used to hold uploaded data files.

        This method accepts additional parameters required for creating files inside Genestack.
        These parameters depend on the file type:

        * For "MappedReadsCounts": name of the reference genome
          (specified by the "reference_genome" key).

        Example:

        .. code-block:: python

            sample_linker.create_upload_dataset(
                study_number=1,
                file_type='MappedReadsCounts',
                reference_genome='Homo sapiens / GRCh37 release 68'
            )

        :param study_number: number of the study that contains samples for uploaded files.
        :type study_number: int
        :param file_type: type of files that will be uploaded
               (only "MappedReadsCounts" are currently supported).
        :type file_type: str
        :param kwargs: additional options that are needed when creating a file. Options content
                       depends on the type of the created file.
        :return: accession of the created dataset
        :rtype: str
        """

        options = {
            key: value if isinstance(value, (list, tuple)) else [value]
            for key, value in kwargs.viewitems()
        }
        return self.invoke('createUploadDataset', study_number, file_type, options)

    def import_data(self, samples, upload_dataset_accession):
        """
        Create data files inside the upload dataset and link them to the specified samples.

        Created files are initialized upon creation.

        NOTE: This method can only handle 100 files at a time, so in case
        of uploading more files than that they must be uploaded in batches of this size.

        Example:

        .. code-block:: python

            sample_linker.import_data(
                samples={
                    'sampleId1': ['http://data_url1', 'http://data_url2'],
                    'sampleId2': ['http://more.data']
                },
                upload_dataset_accession='GSF000123'
            )

        This call will return the following dictionary:

        .. code-block:: python

            {
                'sampleId1': ['GSF0001', 'GSF0002'],
                'sampleId2': ['GSF0003']
            }

        :param samples: mapping from sample id to a list of URLs that point to data.
        :type samples: dict[str, list[str]]
        :param upload_dataset_accession: accession of the upload dataset that will hold the created
                                         data files.
        :type upload_dataset_accession: str
        :return: mapping from sample id to a list of accessions of the created data files.
        :rtype: dict[str, list[str]]
        """
        return self.invoke('importData', samples, upload_dataset_accession)

    def unlink_data(self, file_accessions, upload_dataset_accession):
        """
        Remove uploaded data files from the given dataset and unlink them from their samples.
        Links to samples are always removed but actual files may not be removed from the system.

        Removing a file that isn't present in the dataset is a no-op and will not throw an
        exception.

        :param file_accessions: accessions of data files that should be unlinked.
        :type file_accessions: list[str]
        :param upload_dataset_accession: accession of the upload dataset that holds the provided
                                         data files.
        :type upload_dataset_accession: str
        """
        return self.invoke('unlinkData', file_accessions, upload_dataset_accession)

    def release(self, group_name, upload_dataset_accession):
        """
        Release the provided dataset. Releasing a dataset means that all data files are ready
        and can be shared with the outer world.

        This method is idempotent and can be run multiple times in case of errors.

        :param group_name: name of the group that the provided dataset will be shared with.
        :type group_name: str
        :param upload_dataset_accession: accession of the dataset that holds the uploaded data
                                         files.
        :type upload_dataset_accession: str
        """
        return self.invoke('release', group_name, upload_dataset_accession)
