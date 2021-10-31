from nlp_label_quality.analysis import analysis_utils
from nlp_label_quality.custom_errors import IncorrectOptionTypeError, IncorrectOptionInputError, \
    IncorrectSingleOptionError, IncorrectMultipleOptionsError

from typing import List, Dict, Tuple, Any, Union
from nlp_label_quality.analysis.attribute_value import Attribute, AttributeValue
from nlp_label_quality.analysis.nlp_models import GloVeModel, SpaCyModel

import numpy as np
from abc import ABC, abstractmethod
import time
import logging

logger = logging.getLogger(__name__)


class Analysis(ABC):
    def __init__(self, name: str, controller: 'Controller') -> None:
        self.name = name
        self.controller = controller

    @abstractmethod
    def start(self, attribute_content):
        pass


class AnalysisModule(Analysis):
    """
    AnalysisModule correcting grammatical and synonymous errors

    Parameters
    ----------
    nlp
        spacy Model
    glove
        KeyedVectors model
    name
        name of this analysis instance
    options
        configuration options for the analysis
    thresholds
        configuration under which the results are filtered
    controller
        main controller for the full program
    """

    def __init__(self,
                 name: str,
                 controller: 'Controller',
                 nlp: SpaCyModel,
                 glove: GloVeModel,
                 options: Union[List[str], List[List[str]]],  # both single options and multiple options have to work
                 thresholds: Union[float, List[float]]) -> None:  # accordingly thresholds as well
        super().__init__(name, controller)
        self.nlp = nlp
        self.glove = glove
        self.options = options
        self.thresholds = thresholds

        self.attributes = []
        self.treeview_headers = self.controller.get_treeview_headers()
        self.antonym_library = analysis_utils.get_antonyms_from_verbocean()

    def start(self,
              attribute_content: Dict[str, Dict[str, int]]) -> Dict[int, Dict[str, Union[str, int, float]]]:
        """
        Fully automatic process to use AnalysisModule for grammar analysis

        Parameters
        ----------
        attribute_content
            content to be analyzed {attr1: {'attr_value1': count, ...}, attr2: ...}

        Returns
        -------
        repair_dict
            repair_dict is passed to treeview for selection of useful results
        """
        tic = time.perf_counter()
        self._initialize_attributes(attribute_content)
        repair_dict = self.get_results_per_analysis(self.name, self.attributes, self.options, self.thresholds)
        toc = time.perf_counter()
        logger.info(f'AnalysisModule took {toc - tic} seconds for syntax analysis.')
        return repair_dict

    def _initialize_attributes(self, attribute_content: Dict[str, Dict[str, int]]) -> None:
        """
        Initialize attribute content as Attribute classes containing AttributeValue classes itself for deeper analysis


        Parameters
        ----------
        attribute_content
            content to be analyzed {attr1: {'attr_value1': count, ...}, attr2: ...}
        """
        tic = time.perf_counter()
        for attr, values in attribute_content.items():
            self.attributes.append(Attribute(attr, values, self.nlp, self.glove))
        toc = time.perf_counter()
        logger.info(f'AttributeValue instances were initialized in {toc - tic} seconds')

    def get_results_per_analysis(self,
                                 name: str,
                                 attributes: List[Attribute],
                                 options: Union[List[str], List[List[str]]],
                                 thresholds: Union[float, List[float]]) -> Dict[int, Dict[str, Union[str, int, float]]]:
        """
        Generate the similarity matrices, return the results and filter them
         -> preparation for frontend to show results in readable manner

        Parameters
        ----------
        name
            name of analysis step
        attributes
            list of all attributes that were filtered from original log
        options
            configuration options to build matrices
        thresholds
            values to filter matrices by

        Returns
        -------
        repair_selection_dict
            result selection filtered with thresholds and prepared to be used in
        """
        bool_mulitple_options = self._check_content_of_options(options)
        analysis_utils.generate_sim_matrices(bool_mulitple_options, attributes, name, options)
        # get the just created matrices to work with them
        all_sim_matrices = {attribute: attribute.matrix_content for attribute in self.attributes}

        if bool_mulitple_options:
            max_matrices = self.generate_max_matrix_per_attribute()
            logger.info('For the combination of analysis modules, the options cannot be output and the threshold is fixed.')
            repair_selection_dict = analysis_utils.get_result_selection(bool_mulitple_options, max_matrices,
                                                                        ['combined_options', 'max_combined', 'spacy_lemmas', 'max'], 0.75,
                                                                        self.treeview_headers, self.antonym_library)

        else:
            repair_selection_dict = analysis_utils.get_result_selection(bool_mulitple_options, all_sim_matrices,
                                                                        options, thresholds,
                                                                        self.treeview_headers, self.antonym_library)

        return repair_selection_dict

    @staticmethod
    def _check_content_of_options(options: Union[List[str], List[List[str]]]) -> bool:
        """
        Check if options are correct and assign corresponding function to build matrices

        Parameters
        ----------
        options
            options to build matrices

        Returns
        -------
        bool_mulitple_options
            true if it has multiple correct options; false if it is only a single correct option
        """
        if isinstance(options, list):  # check general list type
            multiple = True
            for option in options:
                if isinstance(option, list):  # check if options are multiple or single
                    if len(option) == 4:  # check length for individual option
                        if all(isinstance(item, str) for item in option):  # check if all options only contain strings
                            continue
                        else:
                            raise IncorrectOptionInputError(option)
                    else:
                        raise IncorrectMultipleOptionsError(options, option)
                else:
                    multiple = False
                    break
            if multiple:
                logger.info(f'options combined {len(options)} multiple configurations')
                for option in options:
                    logger.info(f'{option}')
                return True
            else:
                if len(options) == 4:  # check length for individual option
                    if all(isinstance(item, str) for item in options):  # check if all options only contain strings
                        logger.info(f'options of single configuration {options}')
                        return False
                    else:
                        raise IncorrectOptionInputError(options)
                if len(options) != 4:
                    raise IncorrectSingleOptionError(options)
        else:
            raise IncorrectOptionTypeError(options)

    def generate_max_matrix_per_attribute(self) -> Dict[Attribute, Dict[str, List[np.ndarray]]]:
        """
        Return the matrix where from all models only the highest values are saved, only works after all matrices were calculated

        Returns
        -------
        max_matrices
            collection of max_matrix for each attribute
        """
        max_matrices = {}
        for attribute in self.attributes:  # this and the next line would have to change
            dim = len(attribute.attr_values)  # shape for the zeros matrix
            max_matrix = np.zeros((dim, dim))
            result_matrix = {}
            for name, matrices in attribute.matrix_content.items():
                for i, matrix in enumerate(matrices):
                    max_matrix = np.maximum(max_matrix, matrix)
                result_matrix['max_matrix'] = [max_matrix]  # line only necessary to make it work with get_result_selectioin

            max_matrices[attribute] = result_matrix
        return max_matrices

    # all_sim_matrices = {attribute: attribute.matrix_content for attribute in self.attributes}
    # self.matrix_content: Dict[str, List[np.ndarray]] = {}
