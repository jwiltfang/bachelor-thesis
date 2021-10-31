import logging
import time
from typing import List, Dict, Union
from pm4py.objects.log.log import EventLog
logger = logging.getLogger(__name__)


def repair_log(log: EventLog,
               repair_ids: List[int],
               repair_dict: Dict[int, Dict[str, Union[float, int, str]]]) -> EventLog:
    """
    Repair log based on selected conditions
    -> Conditions are being sorted by occurence and update the log to an ideally better standard

    Parameters
    ----------
    log
        original event log
    repair_ids
        all ids that have to be changed now
    repair_dict
        set of possible

    Returns
    -------
    repaired_log
        log where all selected conditions where repaired
    """
    conditions = get_repair_conditions(repair_ids, repair_dict)
    repair_conditions = sort_conditions_by_occurence(conditions)
    repaired_log = update_events(log, repair_conditions)
    return repaired_log


def get_repair_conditions(repair_ids: List[int], repair_dict: Dict[int, Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Return pre-filtered repair conditions
    """
    conditions = []
    for rep_id in repair_ids:
        conditions.append(repair_dict[int(rep_id)])
    return conditions


def sort_conditions_by_occurence(conditions: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Sort conditions by occurence -> conditions with low frequency of the original value are sorted in ascending order
    and then those conditions are sorted by suggested frequency in ascending order
    => maximizing aggregation
    """
    sorted_conditions = sorted(sorted(conditions, key=lambda x: x.get('original occurence')), key=lambda x: x.get('suggested occurence'))
    return sorted_conditions


def update_events(log: EventLog, conditions: List[Dict[str, str]]) -> EventLog:
    """
    Update the event log with the repair conditions
    -> additional attribute labels simplify the evaluation of the event log
    """
    changed_entries, changed_events = 0, 0
    tic = time.perf_counter()
    analysis_name = conditions[0].get('model_name')
    # collect all changes based on one analysis step, easier to evaluate instead of searching for the events
    log.attributes[f'an:{analysis_name}:changes'] = conditions
    for trace in log:
        for event in trace:
            event_changed = False

            for condition in conditions:
                attr_name = condition.get('attribute')
                orig_value = condition.get('original_value')
                sugg_value = condition.get('suggested_value')
                analysis_name = condition.get('model_name')

                if event.get(attr_name) == orig_value:
                    event[attr_name] = sugg_value
                    event[f'an:{analysis_name}:{attr_name}'] = sugg_value
                    event_changed = True
                    changed_entries += 1

            if event_changed:
                changed_events += 1
    toc = time.perf_counter()
    logger.info(f'The repair has changed {changed_entries} entries in {changed_events} events in {toc-tic} seconds.')
    # evaluate the log right here
    return log


