import pm4py
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter

import pandas as pd
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter


from typing import Union
import time
import logging
logger = logging.getLogger(__name__)


def import_eventlog(file_location: str) -> Union[None, pm4py.objects.log.log.EventLog]:
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
    tic = time.perf_counter()
    if file_location.endswith('.xes'):
        eventlog = _import_xes(file_location)
    elif file_location.endswith('.csv'):
        eventlog = _import_csv(file_location)
    else:
        eventlog = None
    toc = time.perf_counter()
    logger.info(f"Import eventlog in {toc - tic} seconds: {file_location}")
    return eventlog


def _import_xes(file_location: str) -> pm4py.objects.log.log.EventLog:
    return xes_importer.apply(file_location)


def _import_csv(file_location: str, sep: str = ',') -> pm4py.objects.log.log.EventLog:
    log_csv = pd.read_csv(file_location, sep=sep)
    log_csv = dataframe_utils.convert_timestamp_columns_in_df(log_csv)
    return log_converter.apply(log_csv)


def export_eventlog(repaired_log: pm4py.objects.log.log.EventLog, new_filename: str) -> None:
    """
    Export event log in .xes format after the necessary changes have been done

    Parameters
    ----------
    repaired_log
        eventlog to be exported
    new_filename
        filepath where the repaired event log is meant to be saved
    """
    try:
        tic = time.perf_counter()
        if new_filename.endswith('.xes'):
            _export_xes(repaired_log, new_filename)
        elif new_filename.endswith('.csv'):
            _export_csv(repaired_log, new_filename)
        else:
            pass
        toc = time.perf_counter()
        logger.info(f'The event log was exported and saved at {new_filename} in {toc-tic} seconds.')
    except FileNotFoundError as fe:
        pass


def _export_xes(repaired_log: pm4py.objects.log.log.EventLog, new_filename: str) -> None:
    xes_exporter.apply(repaired_log, new_filename)


def _export_csv(repaired_log: pm4py.objects.log.log.EventLog, new_filename: str) -> None:
    dataframe = log_converter.apply(repaired_log, variant=log_converter.Variants.TO_DATA_FRAME)
    dataframe.to_csv(new_filename)


if __name__ == '__main__':
    import_eventlog('test')
