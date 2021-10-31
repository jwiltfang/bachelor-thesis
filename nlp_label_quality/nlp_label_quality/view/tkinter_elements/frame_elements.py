import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
from PIL import ImageTk, Image

from abc import ABC, abstractmethod
from .settings import _TITLE_FONT, _ACTIVE_BUTTON
from typing import List

import logging

logger = logging.getLogger(__name__)


class ABCReusableFrame(ABC, tk.Frame):
    def __init__(self, master: tk.Frame, controller: 'Controller', **kwargs):
        tk.Frame.__init__(self, master, **kwargs)
        self.controller = controller
        self._setup_frame()

    @abstractmethod
    def _setup_frame(self):
        pass

    def update_button(self, btn, state):
        button = getattr(self, btn)
        button.config(state=state)


class InformationContainer(ABCReusableFrame):
    def __init__(self, master: tk.Frame, controller: 'Controller', **kwargs):
        """
        Information container class that can be reused in different frames
        :param master:
        """
        super().__init__(master, controller, **kwargs)

    def _setup_frame(self):
        self.header_container = tk.Frame(self)
        self.current_file_label = tk.Label(self.header_container,
                                           text=('Current File: ' + str(self.get_filename())), anchor='w', pady=6)
        self.current_analysis_label = tk.Label(self.header_container,
                                               text=('Analysis step: ' + str(self.get_analysis_step_information())),
                                               anchor='w', pady=6)
        self.logo_container = tk.Frame(self)
        self.logo_panel = LogoPanel(self.logo_container, self.controller)
        # pack all elements down
        self.header_container.pack(side='left', anchor='w', fill='x', expand=True)
        self.current_file_label.pack(anchor='w', fill='x')
        self.current_analysis_label.pack(anchor='w', fill='x')
        self.logo_container.pack(side='left', expand=False)
        self.logo_panel.pack()

    def update_current_file_label(self, filename):
        self.current_file_label.config(text=('Current File: ' + str(filename)))

    def get_filename(self):
        return self.controller.get_filename()

    def get_analysis_step_information(self):
        step, total_steps = self.controller.get_analysis_step()
        return f'{step} out of possible {total_steps} steps done'


class LogoPanel(ABCReusableFrame):
    def __init__(self, master: tk.Frame, controller: 'Controller', **kwargs):
        """
        Logo class that can be reused in different frames
        :param master:
        """
        self.logo = Image.open('nlp_label_quality/view/tkinter_elements/icons/logo.PNG')
        super().__init__(master, controller, **kwargs)

    def _setup_frame(self):
        self.logo_resized = self.logo.resize((128, 72), Image.ANTIALIAS)
        self.logo = ImageTk.PhotoImage(self.logo_resized)
        self.logo_panel = tk.Label(self, image=self.logo)
        # pack the logo_panel within the master frame
        self.logo_panel.pack(anchor='w')


class ImportFileContainer(ABCReusableFrame):
    def __init__(self, master: tk.Frame, controller: 'Controller'):
        super().__init__(master, controller)

    def _setup_frame(self):
        self.import_file_button = tk.Button(self, text='Import Log File',
                                            command=self.import_file,
                                            activebackground=_ACTIVE_BUTTON)
        self.import_file_button.pack(anchor='w', fill='x')

    def import_file(self, *args):
        self.controller.handle_click_import_file()


class StartAnalysisContainer(ABCReusableFrame):
    def __init__(self, master: tk.Frame, controller: 'Controller', **kwargs):
        super().__init__(master, controller, **kwargs)

    def _setup_frame(self):
        self.start_analysis_description = tk.Label(self, text='Select model_glove and file pre-analysis.', anchor='w')
        self.start_analysis_button = tk.Button(self,
                                               text='Start Analysis',
                                               activebackground=_ACTIVE_BUTTON,
                                               command=self.start_analysis,
                                               state='disabled')
        self.progressbar_loadmodel = ttk.Progressbar(self, orient='horizontal', mode='indeterminate')

        # pack and align in frame
        self.start_analysis_description.pack(anchor='w', fill='x')
        self.start_analysis_button.pack(anchor='w', fill='x')

    def start_analysis(self):
        self.controller.handle_click_start_analysis()


class SelectAttributesContainer(ABCReusableFrame):
    def __init__(self, master: tk.Frame, controller: 'Controller', **kwargs):
        super().__init__(master, controller, **kwargs)

    def _setup_frame(self):
        self.selection_label = tk.Label(self, text='Please select the attributes that you want to correct.')
        self.selection_box = tk.Listbox(self, selectmode=tk.MULTIPLE, height=4)
        self.select_button = tk.Button(self, text='Confirm Selection', command=self.select_attributes, state='disabled')

        self.selection_label.pack(anchor='w', fill='x')
        self.selection_box.pack(anchor='w', fill='both', expand=True)
        self.select_button.pack(anchor='w', fill='x')

    def update_attributes(self):
        self.attributes = self.controller.get_relevant_attributes()
        for val in self.attributes:
            self.selection_box.insert(tk.END, val)

    def select_attributes(self):
        selected_ids = self.selection_box.curselection()  # returns tuple
        selected_attributes = [self.attributes[i] for i in selected_ids]
        logger.info(f'Attributes selected: {selected_attributes}')

        self.selection_label.config(text=f'Attributes Selected: {selected_attributes}')
        self.selection_box.pack_forget()
        self.select_button.pack_forget()

        self.controller.attributes_selected(selected_attributes)


class LegendContainer(ABCReusableFrame):
    def __init__(self, master: tk.Frame, controller: 'Controller'):
        self.legend_text = \
            'The upper screen shows all repair suggestions the tool has found in the last analysis iteration. ' \
            'Of all possible results, the one with similarity score below the critical threshold are discarded.\n' \
            'Please select all the values that apply to repair the event log you uploaded. Numerical values can be sorted manually by clicking on column title.\n\n' \
            'Tip for the easiest way to repair labeling anomalies with this tool:\n' \
            'Check the highest scores by sorting \'Sim_Score\' in descending order. If these results are not very useful and many suggestions are availabel for the same value, ' \
            'the user must sort \n the \'Original occurrence\' in ascending order because then all suggestions for the same incorrect label with low occurrence are compiled in one place.\n ' \
            'These are more likely to be anomalous and the user can choose the correct suggestion and delete the other repair suggestions for the same label value.\n\n' \
            'Explanations:\nTheoretical Assumption: Decreasing probability of correct assignment of Original Label if occurence is lower than Suggested Label.\n' \
            '\'Attribute\' -> attribute both labels are in\n' \
            '\'Sim_Score\' -> value the NLP methods calculated, \'Threshold\' -> critical threshold filter, ' \
            '\'Antonyms\' -> antonyms that both labels share; similarity very unlikely\n' \
            '\'Original_Label\' will be replaced by \'Suggested Label\' in repaired event eventlog\n' \
            '\'Orig_Anal_Value\' -> actually analysed value due to preprocessing and analysis configurations\n' \
            '\'Original Occurence\' -> total appearance of the original label within event log\n' \
            '\'Sim_model\' -> used model, \'model_name\' -> name, \'attr_property\' -> label property that was used, \'function\' -> used function to calculate similarity'

        super().__init__(master, controller)

    def _setup_frame(self):
        self.repair_message = tk.Label(self, anchor="w", justify='left',
                                       text="Please select all the values that apply to repair the event log you uploaded. Select the right lines with your mouse and hold STRG / CTRL for multi-selection.",
                                       pady=2, bg='#0078d7', fg='white', relief='raised', bd=2)
        self.legend_title = tk.Label(self, text='Legend of used expressions above:', font=_TITLE_FONT,
                                     anchor='w')
        self.repair_choice_legend = tk.Label(self, anchor='w', justify='left', text=self.legend_text)
        # pack elements and align
        self.repair_message.pack(anchor='w', fill='both')
        self.legend_title.pack(anchor='w', fill='x')
        self.repair_choice_legend.pack(anchor='w', fill='x')


class TreeviewSelection(ABCReusableFrame):
    def __init__(self, master: tk.Frame, controller: 'Controller', **kwargs):
        super().__init__(master, controller, **kwargs)
        self._build_tree()
        self.treeview_headers = []
        self.repair_ids = []

    def _setup_frame(self):
        # create a treeview with dual scrollbars
        self.tree_container = tk.Frame(self)
        self._create_treeview(self.tree_container)
        # button container that includes all actions regarding the treeview to select results and repair log
        self.bottom_button_container = tk.Frame(self)
        # buttons to delete elements and not bother with anymore
        self.delete_entire_list_button = tk.Button(self.bottom_button_container, text='Delete Entire List',
                                                   activebackground=_ACTIVE_BUTTON,
                                                   command=self.delete_entire_list)
        self.delete_selection_button = tk.Button(self.bottom_button_container, text='Delete Selection',
                                                 activebackground=_ACTIVE_BUTTON, command=self.delete_selection)
        self.clear_selection_button = tk.Button(self.bottom_button_container, text='Clear Selection',
                                                activebackground=_ACTIVE_BUTTON,
                                                command=self.clear_selection)

        self.select_all_button = tk.Button(self.bottom_button_container, text='Select All',
                                           activebackground=_ACTIVE_BUTTON, command=self.select_all)
        self.selection_to_repair_button = tk.Button(self.bottom_button_container, text='Selection to Repair',
                                                    activebackground=_ACTIVE_BUTTON, command=self.select_to_repair)
        self.run_repair_button = tk.Button(self.bottom_button_container, text='Run Repair',
                                           activebackground=_ACTIVE_BUTTON,
                                           command=self.run_repair, state='disabled')
        self.run_analysis_button = tk.Button(self.bottom_button_container, text='Run Next Analysis',
                                             activebackground=_ACTIVE_BUTTON,
                                             command=self.run_next_analysis)
        self.export_button = tk.Button(self.bottom_button_container, text='Export Log Now',
                                       activebackground=_ACTIVE_BUTTON,
                                       command=self.export_log, state='disabled')

        # alignment of treeview
        self.tree_container.pack(fill='both', expand=True)
        self.tree.grid(column=0, row=0, sticky='nsew')
        self.vsb.grid(column=1, row=0, sticky='ns')
        self.hsb.grid(column=0, row=1, sticky='ew')
        self.tree_container.grid_columnconfigure(0, weight=1)
        self.tree_container.grid_rowconfigure(0, weight=1)

        # button container below the treeview for further action
        self.bottom_button_container.pack(anchor='w', fill='x')

        self.delete_entire_list_button.pack(side='left')
        self.delete_selection_button.pack(side='left')
        self.clear_selection_button.pack(side='left')

        self.export_button.pack(side='right')
        self.run_analysis_button.pack(side='right')
        self.run_repair_button.pack(side='right')
        self.selection_to_repair_button.pack(side='right')
        self.select_all_button.pack(side='right')

    def update_treeview(self, repair_dict):
        for key, result_value_dict in repair_dict.items():
            sim_value = result_value_dict.get('sim_score')
            threshold = result_value_dict.get('threshold')
            values_per_line = list(result_value_dict.values())
            tag = self._get_tag_for_treeview_line(sim_value, threshold)
            self.tree.insert(parent='', index='end', iid=key, values=values_per_line, tags=tag)

    def _get_tag_for_treeview_line(self, sim_value, threshold):
        """
        Color support to make the information more readable
        :param sim_value:
        :return:
        """
        max_threshold = 1
        green_area = max_threshold - threshold
        tag = self.tag_prios[-1]  # originally lowest tag
        for tag_name in self.tag_prios:
            if sim_value > max_threshold:
                tag = (tag_name,)
                return tag
            else:
                max_threshold -= green_area / len(self.tag_prios)
        return tag

    def delete_entire_list(self, *args):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def clear_selection(self):
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def delete_selection(self):
        for selected_item in self.tree.selection():
            self.tree.delete(selected_item)

    def select_all(self):
        self.tree.selection_set(self.tree.get_children())

    def get_indices_for_repair(self):
        repair_ids = self.tree.selection()
        for element in repair_ids:
            self.tree.detach(element)
        return repair_ids

    def run_repair(self):
        self.controller.handle_click_run_repair()
        self.repair_ids = []  # reset ids # TODO

    def return_final_repair_ids(self):
        final_repair_ids = []
        for repair_list in self.repair_ids:
            final_repair_ids.extend(repair_list)
        return final_repair_ids

    def run_next_analysis(self):
        self.controller.handle_click_run_next_analysis()

    def select_to_repair(self):
        rep_ids = self.get_indices_for_repair()
        if rep_ids:
            self.repair_ids.append(rep_ids)
        else:
            pass
        print(self.repair_ids)
        self.update_button('run_repair_button', 'normal')
        self.update_button('run_analysis_button', 'disabled')
        self.update_button('export_button', 'disabled')

    def export_log(self):
        self.controller.handle_click_export_file()

    def check_treeview_content(self):
        """
        If no elements are in the treeview, all other buttons regarding the treeview should be off.
        :return:
        """
        if not self.tree.get_children():
            buttons_to_disable = ['delete_entire_list_button', 'delete_selection_button', 'clear_selection_button',
                                  'run_repair_button', 'selection_to_repair_button', 'select_all_button']
            for btn in buttons_to_disable:
                self.update_button(btn, 'disabled')

    def _create_treeview(self, master: tk.Frame):
        """
        Creation and adaption of treeview bundled in this function for better resuability
        (has to be implemented for each frame as the packing on the interface happens within the function
        """
        self.treestyle = ttk.Style()
        self.treestyle.theme_use('clam')
        self.treestyle.configure('Treeview', background='white', rowheight=20,
                                 fieldbackground='lightgrey')
        self.treestyle.map('Treeview', background=[('selected', '#0078d7')])

        self.treeview_headers = self.controller.get_treeview_headers()
        self.tree = ttk.Treeview(master, columns=self.treeview_headers, show="headings",
                                 selectmode='extended')  # displaycolumns=self.treeview_headers[:]
        self.vsb = ttk.Scrollbar(master, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(master, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.tag_colors = ['lightgreen', '#cfe9b5', '#ebebd3', '#f2efec', 'white', '#f6f8f4', '#e4f6f4', '#dfcff8',
                           'lightpink']
        self.tag_prios = ['prio8', 'prio7', 'prio6', 'prio5', 'prio4', 'prio3', 'prio2', 'prio1', 'prio0']
        for tag_name, color in zip(self.tag_prios, self.tag_colors):
            self.tree.tag_configure(tag_name, background=color)
        # self.tree.tag_configure('high', background='lightgreen')
        # self.tree.tag_configure('middle', background='white')
        # self.tree.tag_configure('low', background='lightpink')

        self.tree.focus()

    def _build_tree(self):
        for col in self.treeview_headers:
            if col in ['sim_score', 'suggested occurence', 'original occurence']:
                # numeric columns can be sorted by values
                self.tree.heading(col, text=col.title(), anchor='w', command=lambda c=col: self.sortby(c, 1))
            else:
                self.tree.heading(col, text=col.title(), anchor='w')
            # adjust the column's width to the header string
            self.tree.column(col)

    def sortby(self, col, descending, *args):
        """sort tree contents when a column header is clicked on"""
        # grab values to sort
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        # if the data to be sorted is numeric change to float
        data = self.change_numeric(data)
        # now sort the data in place
        data.sort(reverse=descending)
        for ix, item in enumerate(data):
            self.tree.move(item[1], '', ix)
        # switch the heading so that it will sort in the opposite direction
        self.tree.heading(col, command=lambda c=col: self.sortby(c, not descending))

    def change_numeric(self, data):
        """if the data to be sorted is numeric change to float"""
        new_data = []
        if self.is_numeric(data[0][0]):
            # change child to a float
            for child, col in data:
                new_data.append((float(child), col))
            return new_data
        return data

    @staticmethod
    def is_numeric(s):
        """test if a string is numeric"""
        for c in s:
            if c in "1234567890-.":
                return True
            else:
                return False
