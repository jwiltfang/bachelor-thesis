from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter

from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.algo.filtering.log.variants import variants_filter

import pm4py
from tkinter import filedialog
import logging
import time
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filemode='a')
logging.getLogger().addHandler(logging.StreamHandler())
logging.disabled = False


def import_eventlog(filename):
    tic = time.perf_counter()
    # variant = xes_importer.Variants.ITERPARSE
    # parameters = {variant.value.Parameters.MAX_TRACES: 100}
    # eventlog = xes_importer.apply(filename, variant=variant, parameters=parameters)
    eventlog = xes_importer.apply(filename)

    toc = time.perf_counter()
    logging.info(f"Import event eventlog in {toc - tic:0.4f} seconds")
    return eventlog


def filter_eventlog(log):
    # filter a log on a specified set of variants
    filtered_log = variants_filter.filter_log_variants_percentage(log, percentage=0.1)
    # filtered_log = pm4py.filter_variants_percentage(log, threshold=0.1)
    # filtered_log = pm4py.filter_event_attribute_values(log, attribute_key, values, level='case', retain=True)
    return filtered_log


def export_eventlog(log_to_export, filename):
    xes_exporter.apply(log_to_export, filename)


def main():
    filename = filedialog.askopenfilename(
        title="Select a File ...",
        filetypes=(
            ("eventlog files", "*.xes"), ("eventlog files", "*.csv"),
            ("all files", ".*")))

    file_str = os.path.basename(filename)

    log = import_eventlog(filename)
    filtered_log = filter_eventlog(log)
    filtered_filename = filedialog.asksaveasfilename(
        initialfile=f'filt_{file_str}',
        defaultextension='.xes',
        title='Save File after Repair',
        filetypes=(
            ("eventlog files", "*.xes"),
            ("eventlog files", "*.csv"),
            ("all files", ".*")))
    export_eventlog(filtered_log, filtered_filename)


if __name__ == '__main__':
    main()
