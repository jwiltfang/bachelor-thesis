import pm4py
from pm4py.algo.filtering.log.attributes import attributes_filter

from nlp_label_quality.model import repair, file_utils
from nlp_label_quality.analysis.attribute_value import Attribute

from typing import List, Dict, Union

from abc import ABC, abstractmethod
from os import path

import time
import logging
from dateutil.parser import parse

logger = logging.getLogger(__name__)


class Model(ABC):
    """Abstract Base Class as an interface for different DataModel implementations"""
    # no abstract methods needed yet because programme does not enforce complete loose coupling


class TkDataModel(Model):
    """
    Concrete Implementation for DataModel in MVC architecture

    Parameters
    ----------

    """
    _filename: str
    log: pm4py.objects.log.log.EventLog
    relevant_attributes: List[str]
    selected_attributes: List[str]
    attribute_content: Dict[str, Dict[str, int]]
    attributes: List['Attribute']

    _analysis_step: int
    analysis_options: List[Union[List[str], List[List[str]]]]
    analysis_thresholds: List[float]
    repair_ids: List[int]
    repair_dict: Dict[int, Dict[str, Union[float, int, str]]]  # repair_ids as key and necessary values saved in list
    treeview_headings: List[str]

    log_was_changed: bool

    def __init__(self) -> None:
        # basic data
        self.models_loaded = False
        self.nlp = None
        self.glove = None
        # log data to analyse
        self._filename = ''
        # noinspection PyTypeChecker
        self.log = None
        self.attributes_list = []
        self.attributes_not_used = ['time:timestamp', 'id']
        self.relevant_attributes = []
        self.selected_attributes = []
        self.attribute_content = {}
        self.attributes = []

        # list of options [model, name, attribute to look for, function], '_' placeholder
        # analysis options # TODO select these options on StartFrame
        self._analysis_step = 0
        self.analysis_options = [['leven', 'gram_lev', 'processed_value', '_'],
                                 ['leven', 'gram_lev2', 'processed_value', '_'],
                                 ['leven', 'gram_lev3', 'processed_value', '_'],
                                 [['open', 'sem_glove', 'glove_tokens', 'calc_similarity_list'],
                                  ['open', 'sem_glove2', 'glove_tokens', 'calc_similarity_difference_list'],
                                  ['open', 'sem_glove3', 'glove_tokens', 'calc_combine_max_list']],
                                 ['open', 'glove_final', 'glove_tokens', 'calc_combine_filter_list'],
                                 [['spacy', 'sem_sp', 'spacy_tokens', 'calc_similarity_list'],
                                  ['spacy', 'sem_sp2', 'spacy_lemmas', 'calc_similarity_difference_list'],
                                  ['spacy', 'sem_sp3', 'spacy_lemmas', 'calc_combine_max_list']],
                                 ['spacy', 'spacy_final', 'spacy_tokens', 'calc_combine_filter_list'],
                                 ['leven', 'gram_final', 'processed_value', '_']]
        self.analysis_thresholds = [0.5, 0.25, 0.15, 0.7, 0.5, 0.7, 0.5, 0.15]
        assert (len(self.analysis_options) == len(self.analysis_thresholds)), 'The number of analyses does not fit the number of thresholds'

        # other working options
        # [['leven', 'grammar', 'processed_value', '_'],  # ideal threshold at 0.3 for first test
        #  ['leven', 'grammar_v2', 'processed_value', '_'],
        #  [['open', 'test_gl_list_logging', 'glove_tokens', 'test_calc_list_combine_logging'],
        #   ['spacy', 'test_sp_list_logging', 'spacy_lemmas', 'test_calc_list_combine_logging'],
        #   ['open', 'sem_dif_tokens_glove', 'glove_tokens', 'calc_similarity_difference_list'],
        #   ['spacy', 'sem_dif_tokens_spacy', 'spacy_tokens', 'calc_similarity_difference_list']],
        #  # values below 0.7 complete trash
        #  ['open', 'test_min', 'glove_tokens', 'test_calc_combine_min'],
        #  ['open', 'test_avg', 'glove_tokens', 'test_calc_combine_avg'],
        #  ['open', 'test_filter', 'glove_tokens', 'test_calc_list_combine_logging'],
        # [['leven', 'grammar', 'processed_value', '_'],
        #  ['open', 'sem_dif_tokens_glove', 'glove_tokens', 'calc_similarity_difference_list'],
        #  ['spacy', 'sem_dif_tokens_spacy', 'spacy_tokens', 'calc_similarity_difference_list'],
        #  ['open', 'sem_tokens_glove', 'glove_tokens', 'calc_similarity_list'],
        #  ['spacy', 'sem_tokens_spacy', 'spacy_tokens', 'calc_similarity_list'],
        #  ['tfidf', 'sem_tfidf', 'glove_tokens', '_'],
        #  ['open', 'test_tokens2', 'glove_tokens', 'calc_similarity_list'],
        #  ['open', 'test_dif_tokens', 'glove_tokens', 'calc_similarity_difference_list'],
        #  ['spacy', 'test_spacy2', 'spacy_tokens', 'calc_similarity_list'],
        #  ['spacy', 'test_dif_spacy', 'spacy_tokens', 'calc_similarity_difference_list']]
        # self.analysis_thresholds = [0.01, 0.1, 0.1, .81, .82, .84, .89, .854, .98, .87]

        # data for repair process
        self.repair_ids = []
        self.repair_dict = {}
        self.treeview_headers = ['attribute', 'sim_score', 'threshold', 'antonyms', 'original_value', 'suggested_value',
                                 'orig_anal_value', 'sugg_anal_value', 'original occurence', 'suggested occurence',
                                 'sim_model', 'model_name', 'attr_property', 'function']
        # export data
        self.log_was_changed = False

    def repair_log(self):
        repaired_log = repair.repair_log(self.log, self.repair_ids, self.repair_dict)
        # reset for next repair
        self.log = repaired_log
        self.preprocess_log()
        self.log_was_changed = True
        logger.info('Log was updated with selected repair suggestions.')

    def reset_repair_data(self):
        self.repair_ids = []
        self.repair_dict = {}

    def extend_repair_ids(self, new_repair_ids):
        self.repair_ids.extend(new_repair_ids)

    def delete_used_repair_ids(self, used_repair_ids):
        for item in used_repair_ids:
            self.repair_ids.remove(item)

    def import_log(self):
        self.log = file_utils.import_eventlog(self._filename)

    def export_log(self, export_filename):
        file_utils.export_eventlog(self.log, export_filename)

    def filter_for_attributes(self, attribute_not_for_analysis: List[str] = None):
        self._get_all_attributes_and_remove_irrelevant(attribute_not_for_analysis)

    def preprocess_log(self):
        """
        Fully automatic preprocessing of the log and prefiltering to only work on relevant data
        """
        self._read_attribute_content()
        self._filter_events_and_attribute_content()

    @property
    def analysis_step(self):
        return self._analysis_step

    @analysis_step.setter
    def analysis_step(self, next_step):
        if next_step > self._analysis_step:
            if next_step > 0:
                self._analysis_step = next_step

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, new_filename: str):
        if new_filename == '':
            self._filename = new_filename
        else:
            if path.exists(new_filename) and path.isfile(new_filename):
                file_ending = new_filename.split('.')[-1].lower()
                if file_ending == 'xes':
                    self._filename = new_filename
                    logger.info(f'File "{self._filename}" was uploaded.')
                else:
                    logger.error(
                        f'The data type .{file_ending} cannot be handled by this program. Please upload a .xes or .csv file.')
            else:
                logger.error(f'The file {new_filename} could not uploaded')

    @staticmethod
    def is_date(string, fuzzy=False):
        """
        Return whether the string can be interpreted as a date.

        :param string: str, string to check for date
        :param fuzzy: bool, ignore unknown tokens in string if True
        """
        try:
            parse(string, fuzzy=fuzzy)
            return True
        except ValueError:
            return False

    def _get_all_attributes_and_remove_irrelevant(self, attribute_not_for_analysis):
        """
        Retrieves all attributes present in log and removes irrelevant attributes that are selected with original

        :param (List[str]) attribute_not_for_analysis: additional attributes that shall not be analyzed
        """
        if attribute_not_for_analysis is None:
            attribute_not_for_analysis = []
        self.attributes_not_used.extend(attribute_not_for_analysis)
        self.attributes_list = pm4py.get_attributes(self.log)
        for attribute in self.attributes_list:
            test_values = attributes_filter.get_attribute_values(self.log, attribute, parameters=None)
            first_test_value = list(test_values)[0]
            if isinstance(first_test_value, str):
                if not first_test_value.isnumeric() and not self.is_date(first_test_value):
                    if attribute.split(':')[0] not in ['correct', 'start', 'an']:
                        continue
            self.attributes_not_used.append(attribute)

            # if not first_test_value.isnumeric():
            #     if not isinstance(first_test_value, str) or attribute.split(':')[0] in ['correct', 'start']:
            #         # filter that only alphabetical str values are presented to user; others can not be analysed by NLP
            #         self.attributes_not_used.append(attribute)
        self.relevant_attributes = [attribute for attribute in self.attributes_list if
                                    attribute not in self.attributes_not_used]
        logger.info(f'Attributes ({self.attributes_not_used} stripped); relevant: {self.relevant_attributes} ')

    def insert_eval_labels(self):
        """
        Insert attributes after selection for use in tool to be able to evaluate the progress of the tool afterwards, comparing values that were inside before and what it became after repair
        :return:
        """
        for trace in self.log:
            for event in trace:
                for attr in self.selected_attributes:
                    if event.get(attr, False):
                        event[attr] = event[attr].strip()  # strip labels from whitespaces
                        if f'start:{attr}' not in event.keys():  # only insert start variable if it is not available before
                            event[f'start:{attr}'] = event[attr]
                    else:
                        continue
        logger.info('Evaluation labels <key=\'start:{attr}\', value=\'**start_label**\'> were inserted.')

    def _read_attribute_content(self):
        """
        Read content for each attribute and get individual values to store in a dict with the key 'attribute'
        """
        self.attribute_content = {}  # filter for nan and empty strings not possible with pm4py filter
        # retrieve all other attribute_values
        for attribute in self.selected_attributes:
            self.attribute_content[attribute] = attributes_filter.get_attribute_values(self.log, attribute)

    def _filter_events_and_attribute_content(self):
        """
        Semantic augmentation by Rebmann et al. introduces many empty strings or NaN values that are filtered in order
        to increase computing speed
        """
        from numpy import nan
        tic = time.perf_counter()
        filtered_attribute_content = {}
        for key, values in self.attribute_content.items():
            new_values = {}
            for k in values.keys():
                if str(k) != 'nan' and str(k) != '' and k != nan:  # solution works but not the best
                    if not isinstance(k, bool):
                        new_values[k.strip()] = values[k]  # strip key to get rid of leading and trailing whitespace
            filtered_attribute_content[key] = new_values
        self.attribute_content = filtered_attribute_content
        toc = time.perf_counter()
        logger.info(f'Attribute content filtered in {toc - tic} seconds.')

    def __repr__(self):
        return 'Data Model'

    def __str__(self):
        return 'Data Model'
