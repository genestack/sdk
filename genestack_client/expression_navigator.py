from genestack_client import Application, GenestackException


class _BaseExpressionNavigator(Application):
    def _create_file(self, groups, group_names=None, group_descriptions=None, organism=None,
                     normalised_input=None, options=None):
        assignments = [(group_id, accession) for group_id, group in enumerate(groups, 1) for accession in group]

        organism = organism or "unknown organism"
        group_names = group_names or ["Group %d" % i for i in range(1, len(groups) + 1)]
        group_names = ["Ungrouped"] + group_names
        group_descriptions = group_descriptions or ["No description provided" for _ in range(1, len(groups) + 1)]
        group_descriptions = ["Ungrouped"] + group_descriptions

        options = options or {}
        params = {
            'normalisedInputMode': bool(normalised_input),
            'accessionList': [acc for group_id, acc in assignments],
            'groupIdList': map(str, [group_id for group_id, acc in assignments]),
            'organism': organism,
            'groupsNameList': group_names,
            'groupsDescriptionList': group_descriptions,
            'programOptions': options,
        }
        if normalised_input:
            params['sourcesAccessions'] = normalised_input
        return self.invoke('createFile', params)


class ExpressionNavigatorforMicroarrays(_BaseExpressionNavigator):
    APPLICATION_ID = 'genestack/expressionNavigator-microarrays'

    def create_file(self, normalized_microarray_file, groups, microarray_annotation, control_group=None,
                    group_names=None, group_descriptions=None, organism=None):
        """
        Create an Expression Navigator file from a normalized microarray file.

        :param normalized_microarray_file: accession of normalized microarray file
        :param groups: list of lists of accessions of the source assays defining the groups
        to use for differential expression
        :param microarray_annotation: accession of the microarray annotation file
        :param control_group: index of the control group in ``groups`` (0-based)
        :type control_group: int
        :param group_names: list of group names
        :param group_descriptions: list of group descriptions
        :param organism: organism
        :return: accession of the created Expression Navigator file
        """

        options = {
            'controlGroupOption': {'value': str(control_group+1) if control_group is not None else "None"},
            'microarrayAnnotationSource': {'type': 'source', 'value': microarray_annotation}
        }
        return self._create_file(groups, group_names=group_names,
                                 group_descriptions=group_descriptions, organism=organism,
                                 normalised_input=[normalized_microarray_file], options=options)


class ExpressionNavigatorforGenes(_BaseExpressionNavigator):
    APPLICATION_ID = 'genestack/expressionNavigator'

    PKG_EDGER = "edgeR"
    PKG_DESEQ = "DESeq2"

    def create_file(self, groups, r_package=PKG_DESEQ, group_names=None,
                    group_descriptions=None, organism=None):
        """
        Create an expression navigator file from RNA-seq gene counts files.

        :param groups: list of lists of gene counts files accessions describing the groups
        to use for differential expression
        :param r_package: name of R package to use for differential expression (either ``edgeR`` or ``DESeq2``)
        :param group_names: names of the groups
        :param group_descriptions: descriptions of the groups
        :param organism: organism
        :return: accession of the created Expression Navigator file
        """

        if r_package not in {self.PKG_DESEQ, self.PKG_EDGER}:
            raise GenestackException("Invalid package option for differential expression '%s'" % r_package)
        options = {'package': {'value': r_package}}
        return self._create_file(groups, group_names=group_names,
                                 group_descriptions=group_descriptions, organism=organism,
                                 options=options)


class ExpressionNavigatorforIsoforms(_BaseExpressionNavigator):
    APPLICATION_ID = 'genestack/expressionNavigator-isoforms'

    def create_file(self, groups, fragment_bias_corr=True, multi_mapping_corr=True,
                    group_names=None, group_descriptions=None, organism=None):
        """
        Create an expression navigator file from RNA-seq isoform FPKM counts files.

        :param groups: list of lists of isoform counts files accessions describing the groups
        to use for differential expression
        :param fragment_bias_corr: apply correction for fragment bias
        :type fragment_bias_corr: bool
        :param multi_mapping_corr: apply correction for reads with multiple mappings
        :type multi_mapping_corr: bool
        :param group_names: names of the groups
        :param group_descriptions: descriptions of the groups
        :param organism: organism
        :return: accession of the created Expression Navigator file
        """

        options = {
            'fragmentBiasCorrectOption': {'value': 'Yes' if fragment_bias_corr else 'No'},
            'multiReadsCorrectOption': {'value': 'Yes' if multi_mapping_corr else 'No'}
        }
        return self._create_file(groups, group_names=group_names,
                                 group_descriptions=group_descriptions, organism=organism,
                                 options=options)
