# coding=utf-8
from genestack_client import Application


class StudyDesign(Application):
    """
    API for working with studies and administrating the Study Design application.

    Study Design is an application for describing studies and samples using Genestack metainfo
    mechanism.
    """
    APPLICATION_ID = 'genestack/study-design'

    def get_study_info(self, study_accession):
        """
        Get information about the given study from the project management point of view.

        :param study_accession: study accession
        :type study_accession: str
        :return: dictionary with the following entries:

            * ``studyNumber``: number of study unique for the organization (int or *None* if no
              study number has been generated),
            * ``studyStatus``: current workflow step (str),
            * ``approved``: mark of passed curator's review (bool),
            * ``hasApprovalButton``: mark of *Approve/Disapprove* button visibility in UI (bool),
            * ``approvalButtonHidden``: *true* if *Approve/Disapprove* button was hidden via
              the :meth:`set_approval_button_visibility` method, *false* otherwise (bool),
            * ``linkedDataset``: accession of the most recently created dataset with expression data
              that is linked to this study and can be opened in the Expression Repository
              application or *None* if no datasets can be found (str).

        :rtype: dict
        """
        return self.invoke('getStudyInfo', study_accession)

    def set_study_status(self, study_accession, new_status):
        """
        Update status of the given study.

        Status is a name of a project workflow stage as it is going to be displayed in the Study
        Design UI, e.g. "*Draft*", "*Waiting for review*", etc.

        :param study_accession: study accession
        :type study_accession: str
        :param new_status: status name
        :type new_status: str
        """
        self.invoke('setStudyStatus', study_accession, new_status)

    def set_study_approval_status(self, study_accession, approved):
        """
        Change approval status of the given study.

        :param study_accession: study accession
        :type study_accession: str
        :param approved: *true* if this study should be approved, *false* otherwise
        :type approved: bool
        """
        self.invoke('setStudyApprovalStatus', study_accession, approved)

    def set_curators_group_name(self, group_name):
        """
        Change name of the current organization's curators group.

        Curators group members have the ability to approve/disapprove studies through the UI.
        However, all users are still able to do that using the :meth:`set_study_approval_status`
        method.

        :param group_name: name of the curators group. If *None* - curators group setting will be
               unset.
        :type group_name: str
        """
        self.invoke('setCuratorsGroupName', group_name)

    def set_approval_button_visibility(self, study_accession, visible):
        """
        Show/hide study approval button in Study Design UI for the given study.

        The button is shown by default, but it is only visible for the members of the curators group
        which have editor access to a study. Approval status can be changed using the
        :meth:`set_study_approval_status` method by any user, regardless of the button
        visibility.

        :param study_accession: study accession
        :type study_accession: str
        :param visible: *true* if button should be visible, *false* otherwise
        :type visible: bool
        """
        self.invoke('setApprovalButtonVisibility', study_accession, visible)
