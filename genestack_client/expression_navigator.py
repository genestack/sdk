import sys

from genestack_client import Application, GenestackException


class _BaseExpressionNavigator(Application):
    def _create_file(self, groups, organism=None, normalized_input=None, options=None,
                     # TODO: remove normalised_input argument.
                     # This argument is deprecated, use normalized_input instead.
                     # We perform renaming in a scope of global 's' -> 'z' refactoring (american style english).
                     normalised_input=None):

        # TODO: reomve this after removing the normalised_input argument
        if normalized_input and normalised_input:
            raise GenestackException('Both normalized_input and normalised_input are not allowed')
        normalized_input = normalized_input or normalised_input

        assignments = [(group_id, accession) for group_id, group in enumerate(groups, 1)
                       for accession in group['accessions']]
        organism = organism or "unknown organism"

        group_names = [group.get("name") or "Group %d" % i for i, group in enumerate(groups, 1)]
        group_names = ["Ungrouped"] + group_names
        group_descriptions = [group.get("description") or "No description provided" for group in groups]
        group_descriptions = ["Ungrouped"] + group_descriptions

        options = options or {}
        params = {
            'accessionList': [acc for group_id, acc in assignments],
            'groupIdList': map(str, [group_id for group_id, acc in assignments]),
            'organism': organism,
            'groupsNameList': group_names,
            'groupsDescriptionList': group_descriptions,
            'programOptions': options,
        }

        if normalized_input:
            params['sourcesAccessions'] = normalized_input
        return self.invoke('createFile', params)

    def get_differential_expression_stats(self, accessions_to_queries):
        """
        Get differential expression statistics from files.
        This method returns a dictionary where values are list of statistics dictionaries.
        Each statistics dictionary has the following structure: (all fields are always present)

            - pValue
            - logFoldChange
            - adjustedPValue
            - genomeFeature (dict):

                - featureType
                - featureId
                - subregions (list)  (``[]`` if unavailable)
                - featureName
                - location (dict):

                    - to (``-1`` if unavailable)
                    - from (0-based, ``-1`` if unavailable)
                    - contigName (``''`` if unavailable)
                    - normalizedContigName (``''`` if unavailable)

                - parentId  (``None`` if unavailable)
                - attributes (dict) (``{}`` if unavailable)

            - contrastLevel

        :param accessions_to_queries: a dictionary whose keys are accessions of differential expression files,
                                      and whose values are ``GenomeQuery`` objects
        :type accessions_to_queries: dict[GenomeQuery]
        :return: dictionary whose keys are file accessions and values are lists of dictionaries with the format
                 described above
        :rtype: dict[list[dict]]
        """
        return self.invoke('getDifferentialExpressionStats', {acc: query.get_map() for acc, query in
                                                              accessions_to_queries.iteritems()})


class ExpressionNavigatorforMicroarrays(_BaseExpressionNavigator):
    APPLICATION_ID = 'genestack/expressionNavigator-microarrays'

    def create_file(self, groups, normalized_microarray_file, microarray_annotation, organism=None):
        """
        Create an Expression Navigator file from a normalized microarray file.
        Each group is described by a dictionary with the following keys:

            - ``accessions``: list of accessions of the source microarray files for this group
            - ``name`` (optional): group name
            - ``description`` (optional): group description
            - ``is_control`` (optional): boolean value indicating whether the group is a control group

        :param groups: list of dictionaries describing the groups for differential expression.
                       See above for the dictionary structure.
        :param normalized_microarray_file: accession of normalized microarray file
        :param microarray_annotation: accession of the microarray annotation file
        :param organism: organism
        :return: accession of the created Expression Navigator file
        """
        control_group = None
        for i, group in enumerate(groups, 1):
            if group.get("is_control"):
                control_group = str(i)
                break
        options = {
            'controlGroupOption': {'value': control_group or "None"},
            'microarrayAnnotationSource': {'type': 'source', 'value': microarray_annotation}
        }
        return self._create_file(groups, organism=organism, normalized_input=[normalized_microarray_file],
                                 options=options)


class ExpressionNavigatorforGenes(_BaseExpressionNavigator):
    APPLICATION_ID = 'genestack/expressionNavigator'

    PKG_EDGER = "edgeR"
    PKG_DESEQ = "DESeq2"

    def create_file(self, groups, r_package=PKG_DESEQ, organism=None):
        """
        Create an expression navigator file from RNA-seq gene counts files.
        Each group is described by a dictionary with the following keys:

            - ``accessions``: list of accessions of the raw gene counts files for this group
            - ``name`` (optional): group name
            - ``description`` (optional): group description

        :param groups: list of dictionaries describing the groups for differential expression.
                       See above for the dictionary structure.
        :param r_package: name of R package to use for differential expression (either ``edgeR`` or ``DESeq2``)
        :param organism: organism
        :return: accession of the created Expression Navigator file
        """
        if r_package not in {self.PKG_DESEQ, self.PKG_EDGER}:
            raise GenestackException("Invalid package option for differential expression '%s'" % r_package)
        options = {'package': {'value': r_package}}
        return self._create_file(groups, organism=organism, options=options)


class ExpressionNavigatorforIsoforms(_BaseExpressionNavigator):
    APPLICATION_ID = 'genestack/expressionNavigator-isoforms'

    def create_file(self, groups, fragment_bias_corr=True, multi_mapping_corr=True, organism=None):
        """
        Create an expression navigator file from RNA-seq isoform FPKM counts files.
        Each group is described by a dictionary with the following keys:

            - ``accessions``: list of accessions of the isoform counts files for this group
            - ``name`` (optional): group name
            - ``description`` (optional): group description

        :param groups: list of dictionaries describing the groups for differential expression.
                       See above for the dictionary structure.
        :param fragment_bias_corr: apply correction for fragment bias
        :type fragment_bias_corr: bool
        :param multi_mapping_corr: apply correction for reads with multiple mappings
        :type multi_mapping_corr: bool
        :param organism: organism
        :return: accession of the created Expression Navigator file
        """
        options = {
            'fragmentBiasCorrectOption': {'value': 'Yes' if fragment_bias_corr else 'No'},
            'multiReadsCorrectOption': {'value': 'Yes' if multi_mapping_corr else 'No'}
        }
        return self._create_file(groups, organism=organism, options=options)
