import logging
import time
from typing import Dict, List
import numpy as np
import warnings
import os


warnings.filterwarnings("ignore", category=RuntimeWarning)
logger = logging.getLogger(__name__)
np.set_printoptions(precision=10, linewidth=np.inf)

from pm4py.algo.filtering.log.attributes import attributes_filter
import pm4py
from pm4py.objects.log.log import EventLog
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from tkinter import filedialog

useless_attributes = ['time:timestamp', 'id']


def _import_file():
    import_filename = filedialog.askopenfilename(title="Select a File ...",
                                                 filetypes=(("eventlog files", "*.xes"), ("all files", ".*")))
    log = import_eventlog(import_filename)
    return import_filename, log


def import_eventlog(file_location: str) -> EventLog:
    """
    Import eventlog

    Parameters
    ----------
    file_location
        model_file to the eventlog_file (only supports xes at this point)

    Returns
    -------
    eventlog
        uploaded event log file
    """
    try:
        tic = time.perf_counter()
        eventlog = xes_importer.apply(file_location)
        toc = time.perf_counter()
        logger.info(f"Import event eventlog in {toc - tic} seconds: {file_location}")
        return eventlog
    except FileNotFoundError as fe:
        logger.error(fe)
        logger.info('File could not be found.')
    except (AttributeError, TypeError) as ae:
        logger.error(ae)
        logger.info('Please upload a valid file (IEEE XES standard).')
    except Exception as e:
        logger.error(e)


def preprocess_log(log, attribute_not_for_analysis: List[str] = None):
    """
    Fully automatic preprocessing of the log and prefiltering to only work on relevant data
    """
    relevant_attributes = _get_all_attributes_and_remove_irrelevant(log, attribute_not_for_analysis)
    attribute_content = _read_attribute_content(log, relevant_attributes)
    filtered_attribute_content = _filter_events_and_attribute_content(attribute_content)
    return filtered_attribute_content
    # write_file_for_update(filtered_attribute_content)


def _get_all_attributes_and_remove_irrelevant(log, attribute_not_for_analysis):
    """
    Retrieves all attributes present in log and removes irrelevant attributes that are selected with original

    :param (List[str]) attribute_not_for_analysis: additional attributes that shall not be analyzed
    """
    if attribute_not_for_analysis is None:
        attribute_not_for_analysis = []
    useless_attributes.extend(attribute_not_for_analysis)
    attributes_list = pm4py.get_attributes(log)
    relevant_attributes = [attribute for attribute in attributes_list if attribute not in useless_attributes]
    return relevant_attributes


def _read_attribute_content(log, relevant_attributes):
    """
    Read content for each attribute and get individual values to store in a dict with the key 'attribute'
    """
    attribute_content = {}  # filter for nan and empty strings not possible with pm4py filter
    # retrieve all other attribute_values
    for attribute in relevant_attributes:
        attribute_content[attribute] = attributes_filter.get_attribute_values(log, attribute)
    return attribute_content


def _filter_events_and_attribute_content(attribute_content) -> Dict[str, Dict[str, int]]:
    """
    Semantic augmentation by Rebmann et al. introduces many empty strings or NaN values that are filtered in order
    to increase computing speed
    """
    from numpy import nan
    filtered_attribute_content = {}
    for key, values in attribute_content.items():
        new_values = {}
        for k in values.keys():
            if str(k) != 'nan' and str(k) != '' and k != nan:  # solution works but not the best
                if not isinstance(k, bool):
                    new_values[k.strip()] = values[k]  # strip key to get rid of leading and trailing whitespace
        filtered_attribute_content[key] = new_values
    print(filtered_attribute_content)
    return filtered_attribute_content


def get_conditions_against_pollution(attribute_content):
    conditions = []
    for key, values in attribute_content.items():
        for value in values.keys():
            corrected_value = _correct_value(value)
            conditions.append([key, value, corrected_value])
    print(conditions)
    return conditions


def _correct_value(value: str = 'Declaration final_approved by supervisor'):
    """
    only works for values from originals/2020...
    """
    import re
    index_by = re.search(r"\b(by)\b", value)
    if index_by:
        corrected_value = value[:index_by.start()].strip()
        print(value, corrected_value)
        return corrected_value
    else:
        return value


def strip_pollution_through_conditions(import_filename, log, conditions):
    filename = os.path.basename(import_filename)
    file_str = f'no_pollution_{filename}'
    repaired_filename = filedialog.asksaveasfilename(initialfile=file_str,
                                                     defaultextension='.xes', title='Save File after Repair',
                                                     filetypes=(
                                                         ("eventlog files", "*.xes"), ("eventlog files", "*.csv"),
                                                         ("all files", ".*")))
    counter = 0
    changed = 0
    for trace in log:
        for event in trace:
            counter += 1
            for condition in conditions:
                key1, original_value1, suggested_value1 = condition
                if event[key1] == original_value1:
                    event[key1] = suggested_value1
                    changed += 1

    xes_exporter.apply(log, repaired_filename)
    print(changed, counter)
    print('Successful export.')


if __name__ == '__main__':
    import_filename, log = _import_file()
    filtered_attribute_content = preprocess_log(log)
    conditions = get_conditions_against_pollution(filtered_attribute_content)
    strip_pollution_through_conditions(import_filename, log, conditions)
