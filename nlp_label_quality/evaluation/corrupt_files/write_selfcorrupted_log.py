from tkinter import filedialog
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
import numpy as np
import os


class CorruptFileSystem:
    def __init__(self):
        self.change_archive_filename = None
        self.filename = None
        self.repaired_filename = None
        self.change_archive_filename = None
        self.log = None
        self.list_for_corruption = []
        self.conditions = []

    def get_repair_conditions(self):
        self.change_conditions_file = filedialog.askopenfilename(
            title='Select changes',
            filetypes=(('text files', "*.txt"),))
        file = open(self.change_conditions_file, 'r')
        lines = file.readlines()
        for line in lines:
            content = line.split(',')  # split on comma
            clean_condition = [element.strip('\n') for element in content]
            self.list_for_corruption.append(clean_condition)
        for element in self.list_for_corruption:
            print(element)

        print('Number of elements:', len(self.list_for_corruption))

    def update_corrupt_file(self):
        self.filename = filedialog.askopenfilename(title="Select a File ...",
                                                   filetypes=(
                                                       ("eventlog files", "*.xes"), ("eventlog files", "*.csv"),
                                                       ("all files", ".*")))
        file_str = os.path.basename(self.filename)
        initial_file_name = f'corr_{file_str}'
        self.repaired_filename = filedialog.asksaveasfilename(initialfile=initial_file_name,
                                                              defaultextension='.xes',
                                                              title='Save File after Repair',
                                                              filetypes=(
                                                                  ("eventlog files", "*.xes"),
                                                                  ("eventlog files", "*.csv"),
                                                                  ("all files", ".*")))
        print(self.repaired_filename)

        if self.repaired_filename:
            self.log = xes_importer.apply(self.filename)
            counter = 0
            changed = 0
            print(self.log.attributes.get('concept:name', 'concept:name not available'))
            for trace in self.log:
                for event in trace:
                    counter += 1
                    for condition in self.list_for_corruption:
                        if len(condition) != 3:  # skip when error in condition
                            continue
                        key1, original_value1, suggested_value1 = condition
                        # create the labels start and correct right in front; if a change was made, these are updated
                        event[f'start:{key1}'] = original_value1
                        event[f'correct:{key1}'] = original_value1
                        if event[key1] == original_value1:
                            selection = np.random.choice(2, 1, p=[0.992, 0.008])  # randomize changes
                            if selection == 1:
                                event[key1] = suggested_value1
                                changed += 1
                                event[f'start:{key1}'] = suggested_value1
                                event[f'correct:{key1}'] = original_value1

                            if counter % 5000 == 0:  # get feedback for user
                                print(f'{changed} elements were adapted.')

            try:
                self.log.attributes['synthetic:changes'] = f'{changed} elements in {counter} events were mainpulated: {self.list_for_corruption}'
            except TypeError:
                pass

            print(counter)
            print(changed)
            xes_exporter.apply(self.log, self.repaired_filename)
            print('Successful export.')
        else:
            print('No file to save was chosen.')


if __name__ == '__main__':
    corruption = CorruptFileSystem()
    corruption.get_repair_conditions()
    corruption.update_corrupt_file()
