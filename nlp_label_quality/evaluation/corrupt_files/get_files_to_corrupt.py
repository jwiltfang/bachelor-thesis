import logging
import time
import datetime
from typing import Dict, List
import numpy as np
import warnings
import os

warnings.filterwarnings("ignore", category=RuntimeWarning)
logger = logging.getLogger(__name__)
np.set_printoptions(precision=10, linewidth=np.inf)

from pm4py.algo.filtering.log.attributes import attributes_filter
import pm4py
from pm4py.objects.log.importer.xes import importer as xes_importer
from tkinter import filedialog

useless_attributes = ['time:timestamp', 'id']


def _import_file():
    import_filename = filedialog.askopenfilename(
        title="Select a File ... for Corrupting labels",
        filetypes=(("eventlog files", "*.xes"), ("all files", ".*")))  # no csv at the moment("eventlog files", "*.csv")
    log = import_eventlog(import_filename)
    return import_filename, log


def import_eventlog(file_location):
    """
    Import eventlog

    :param (str) file_location: model_file to the eventlog_file (only supports xes at this point)

    :return (log) eventlog: uploaded event log file
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


def _filter_events_and_attribute_content(attribute_content):
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
                if not isinstance(k, bool) and not isinstance(k, int) and not isinstance(k, float) and not isinstance(k, datetime.datetime):
                    new_values[k.strip()] = values[k]  # strip key to get rid of leading and trailing whitespace
        filtered_attribute_content[key] = new_values

    return filtered_attribute_content


def write_file_for_update(import_filename, filtered_attribute_content, counter=2, keys_to_filter=None):
    if keys_to_filter is None:
        keys_to_filter = ['concept:name']
    file_str = os.path.basename(import_filename).split('.')[0]
    file_dir = os.path.abspath("test/data/eventlogs/0_evaluation/condition_files")
    change_archive_filename = filedialog.asksaveasfilename(
        initialfile=f'{counter}_cond_{file_str}.txt',
        initialdir=file_dir,
        defaultextension='.txt', title='Save Changes after repair',
        filetypes=(('text', '*.txt'), ('all files', '.*')))
    f = open(change_archive_filename, 'w')
    for key, values in filtered_attribute_content.items():
        for value in values:
            for i in range(counter):
                if keys_to_filter:
                    for attribute in keys_to_filter:
                        if key == attribute:
                            f.write(f'{key},{value},{value}\n')
                        else:
                            pass
                else:
                    f.write(f'{key},{value},{value}\n')

    f.close()


if __name__ == '__main__':
    import_filename, log = _import_file()
    filtered_attribute_content = preprocess_log(log)
    write_file_for_update(import_filename, filtered_attribute_content, keys_to_filter=['concept:name'])
