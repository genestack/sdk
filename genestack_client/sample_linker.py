# coding=utf-8
from genestack_client import Application


class SampleLinker(Application):
    APPLICATION_ID = 'genestack/sample-linker'

    def create_upload_dataset(self, study_number, file_type, **kwargs):
        """
        Create a dataset that will later be used to hold uploaded data files.

        :param study_number: number of the study that contains samples for uploaded files.
        :type study_number: int
        :param file_type: type of files that will be uploaded
                          (only "MappedReadsCounts" are currently supported).
        :type file_type: str
        :param kwargs: additional options that are needed when creating a file. Options content
                       depends on the type of the created file:
                         - For "MappedReadsCounts": name of the reference genome
                         (specified by the "reference_genome" key).
        :return: accession of the created dataset
        :rtype: str
        """

        options = {
            key: value if isinstance(value, (list, tuple)) else [value]
            for key, value in kwargs.viewitems()
        }
        return self.invoke('createUploadDataset', study_number, file_type, options)

    def link_data(self, samples, upload_dataset_accession):
        """
        Create data files inside the upload dataset and links them to the specified samples.

        :param samples: mapping from sample id to a list of URLs that point to data.
        :type samples: dict
        :param upload_dataset_accession: accession of the upload dataset that will hold the created
                                         data files.
        :type upload_dataset_accession: str
        :return: mapping from sample id to a list of accessions of the created data files.
        :rtype: dict
        """
        return self.invoke('linkData', samples, upload_dataset_accession)

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
