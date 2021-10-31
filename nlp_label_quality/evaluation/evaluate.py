from pm4py.algo.filtering.log.variants import variants_filter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter

import logging
from tkinter import filedialog
import os


logger = logging.getLogger(__name__)


def main_evaluate(log, attribute_keys):
    general_information, log = evaluate_log_general(log, attribute_keys)

    evaluation_results = {}
    for attribute in attribute_keys:
        print(f'New analysis - {attribute}')
        attr_combinations, correct_combinations = evaluate_log(log, attribute)

        confusion_matrix = get_confusion_matrix(attr_combinations, correct_combinations)
        confusion_results = calculate_confusion_metrics(confusion_matrix)

        attr_results = {
            'matrix': confusion_matrix,
            'scores': confusion_results}
        evaluation_results[attribute] = attr_results

    return general_information, evaluation_results, log


def evaluate_log_general(log, attributes):
    traces, correct_traces = 0, 0
    events, correct_events = 0, 0
    attr_count, incorrect_attributes = 0, 0
    dict_incorrect_attributes = {attribute: 0 for attribute in attributes}

    for trace in log:
        traces += 1
        trace_incorrect = False
        for event in trace:
            events += 1
            errors_per_event = 0
            event_incorrect = False
            for attribute in attributes:
                attr_count += 1
                attr_incorrect = False
                # correct individual error for log B
                # wrong_string = 'Release Purchase Requisition'
                # if event.get(f'{attribute}') == wrong_string:
                #     event[f'correct:{attribute}'] = wrong_string
                #     event[f'start:{attribute}'] = wrong_string
                # correct individual error for log C_Corr
                # if not event.get(f'start:{attribute}', False):
                #    event[f'start:{attribute}'] = event.get(attribute)
                try:
                    label_dict = {'correct': event.get(f'correct:{attribute}').strip(),
                                  'final': event.get(attribute).strip()}
                    if label_dict.get('correct') != label_dict.get('final'):
                        attr_incorrect = True
                        errors_per_event += 1
                        if attribute in dict_incorrect_attributes:  # check which attribute has how many errors
                            dict_incorrect_attributes[attribute] += 1

                    if attr_incorrect and errors_per_event == 1:
                        event_incorrect = True
                except AttributeError:
                    print(event)
            incorrect_attributes += errors_per_event
            if event_incorrect:
                trace_incorrect = True
            else:
                correct_events += 1
        if trace_incorrect:
            pass
        else:
            correct_traces += 1
        # trace is correct when all events are correct
        # event is correct when all labels are correct
    general_information = {
        'traces': traces,
        'correct_traces': correct_traces,
        # 'incorrect_trace': traces - correct_traces,
        'events': events,
        'correct_events': correct_events,
        # 'incorrect_events': events - correct_events,
        'attribute_count': attr_count,
        'incorrect_attributes': incorrect_attributes,
        'inc_attr_dict': dict_incorrect_attributes
    }

    return general_information, log


def evaluate_log(log, attribute):
    attr_combinations = {}
    correct_combinations = {}

    wrong_counter = 0
    for trace in log:
        for event in trace:
            # print(event, event.keys(), event.values())
            try:
                label_dict = {'start': event.get(f'start:{attribute}').strip(),
                              'correct': event.get(f'correct:{attribute}').strip(),
                              'final': event.get(attribute).strip()}
                start_label, correct_label, final_label = label_dict['start'], label_dict['correct'], label_dict[
                    'final']
                if start_label not in attr_combinations.keys():
                    attr_combinations[start_label] = {'correct': correct_label, 'final': final_label}
                if correct_label not in correct_combinations.keys():
                    correct_combinations[correct_label] = [start_label]
                else:
                    if start_label not in correct_combinations.get(correct_label):
                        correct_combinations[correct_label].append(start_label)
            except AttributeError:
                # print(event)
                wrong_counter += 1
                continue
            # print(label_dict)

    # print(attr_combinations)
    print('wrong events without a label:', wrong_counter)
    return attr_combinations, correct_combinations


def get_confusion_matrix(attr_combinations, correct_combinations):
    tp = [[event_start, event_values] for event_start, event_values in attr_combinations.items() if
          event_values.get('correct') == event_start and event_start == event_values.get('final')]
    fp = [[event_start, event_values] for event_start, event_values in attr_combinations.items() if
          event_values.get('correct') != event_start and event_start == event_values.get('final')]
    fn = [[event_start, event_values] for event_start, event_values in attr_combinations.items() if
          event_values.get('correct') == event_start and event_start != event_values.get('final')]
    tn = [[event_start, event_values] for event_start, event_values in attr_combinations.items() if
          event_values.get('correct') != event_start and event_start != event_values.get('final')]

    # tnpp means the labels were completely corrected, tnpn are only partially corrected (correct meaning but not to the final label)
    tnpp, tnpn, tnn = [], [], []
    tn_start_values = [event_start for event_start, event_values in tn]
    for event_start, event_values in attr_combinations.items():
        if event_start in tn_start_values:
            if event_values.get('final') == event_values.get('correct'):
                tnpp.append([event_start, event_values])
            elif event_values.get('final') in correct_combinations[event_values.get('correct')]:
                tnpn.append([event_start, event_values])
            else:  # relabeled to a wrong label
                tnn.append([event_start, event_values])

    if fp:
        print(f'fp: - {len(fp)} not corrected although it was false {fp}')
    if fn:
        print(
            f'fn: - {len(fn)} corrected although it was correct {fn}')  # all parts that were not even corrected (high probability that it was not shown to user)
    if tnn:
        print(f'tnn: - {len(tnn)} corrected but to the wrong value {tnn}')  # all incorrect corrections
    # print('tnpp:', tnpp)  # all right corrections
    # print('tnpn:', tnpn)  # all only partial right corrections
    confusion_matrix = {
        'total': len(tp) + len(fn),
        'tp': len(tp),
        'fp': len(fp),
        'fn': len(fn),
        'tn': len(tn),
        'tnn': len(tnn),
        'tnpp': len(tnpp),
        'tnpn': len(tnpn)
    }
    return confusion_matrix


def calculate_confusion_metrics(confusion_matrix):
    # caution that each value is taken the right way
    total, tp, fp, fn, tn, tnn, tnpp, tnpn = confusion_matrix.values()
    # classical scores
    accuracy = _calc_container(_accuracy, tp, tn, fp, fn)
    precision = _calc_container(_precision, tp, tn, fp, fn)
    recall = _calc_container(_recall, tp, tn, fp, fn)
    f1 = 2 * precision * recall / (precision + recall)
    # self-developed scores to measure interactivity
    if tn != 0:
        tn_accuracy = tnpp / tn
        print('TN_Accuracy:', tn, tnpp, tn_accuracy)
    else:
        tn_accuracy = 0

    confusion_results = {'accuracy': accuracy,
                         'precision': precision,
                         'recall': recall,
                         'f1': f1,
                         'tn_accuracy': tn_accuracy}
    return confusion_results


def _accuracy(tp, tn, fp, fn):
    return (tp + tn) / (tp + fp + fn + tn)


def _precision(tp, tn, fp, fn):
    return tp / (tp + fp)


def _recall(tp, tn, fp, fn):
    return tp / (tp + fn)


def _calc_container(func, tp, tn, fp, fn):
    try:
        result = func(tp, tn, fp, fn)
    except ZeroDivisionError:
        result = 0
    return result


def evaluate_log_one_by_one(initial_dir, attribute_keys, title, export=False):
    log_file = filedialog.askopenfilename(
        initialdir=initial_dir,
        title=title,
        filetypes=(("eventlog files", "*.xes"), ("all files", ".*")))

    log_to_evaluate = os.path.basename(initial_dir)
    print(f'Log to evaluate: {log_to_evaluate}, {attribute_keys[log_to_evaluate]}')

    log = xes_importer.apply(log_file)
    general_results, eval_result, log = main_evaluate(log, attribute_keys[log_to_evaluate])
    print('GENERAL:', log_to_evaluate, general_results)

    if export:
        xes_exporter.apply(log, log_file)
    results = {
        'general': general_results,
        'quantitative': eval_result
    }
    return results


if __name__ == '__main__':
    # VERY IMPORTANT ---------------------------------------------------------------------------------------------------
    initial_dir = filedialog.askdirectory()
    attribute_keys = {'log_a': ['concept:name', 'org:role', 'org:resource'],
                      'log_b': ['concept:name'],
                      'log_c': ['concept:name', 'doctype', 'subprocess'],
                      'log_d': ['concept:name']}

    print('\nnew anaylsis: corrupt analysis')
    eval_result_corrupt = evaluate_log_one_by_one(initial_dir, attribute_keys, 'Select original corrupted file')
    print('\nnew anaylsis: grammar analysis')
    eval_result_gram = evaluate_log_one_by_one(initial_dir, attribute_keys, 'Select repaired grammar file')
    print('\nnew anaylsis: semantic analysis')
    eval_result_sem = evaluate_log_one_by_one(initial_dir, attribute_keys, 'Select repaired semantic file')

    evaluation_results = {
        'corrupt': eval_result_corrupt,
        'gram': eval_result_gram,
        'sem1': eval_result_sem
    }

    for evaluation, values in evaluation_results.items():
        print(evaluation, values['general'])

    for evaluation, values in evaluation_results.items():
        for attribute, results in values['quantitative'].items():
            print(evaluation, attribute, results.get('matrix'))

    for evaluation, values in evaluation_results.items():
        for attribute, results in values['quantitative'].items():
            print(evaluation, attribute, results.get('scores'))
