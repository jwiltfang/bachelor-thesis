from abc import abstractmethod, ABC

import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
from PIL import ImageTk, Image

from typing import List
from .frame_elements import *
from .settings import _TITLE_FONT, _ACTIVE_BUTTON


class WindowFrame(tk.Frame, ABC):
    def __init__(self, master: tk.Tk, controller: 'Controller'):
        tk.Frame.__init__(self, master)
        self.controller = controller
        self._setup_frame()
        self._orient_frame()
        self.statusbar.pack(side='bottom', anchor='sw', fill='x')

    @abstractmethod
    def _setup_frame(self):
        """initialize elements that will be placed within the frame"""
        pass

    @abstractmethod
    def _orient_frame(self):
        """alignment and packing of frame elements"""
        pass

    def update_button(self, element, btn: str, state: str):
        element_in_frame = getattr(self, element)
        element_in_frame.update_button(btn, state)

    def update_statusbar(self, status):
        self.statusbar.config(text=status)


class StartFrame(WindowFrame):
    def __init__(self, master, controller):
        """
        Initializes frame to have something to show while nlp_models are loading and user can already select the log

        :param master:
        :param controller:
        """
        super().__init__(master, controller)

    def _setup_frame(self):
        self.main_frame = tk.Frame(self)
        self.information_container = InformationContainer(self.main_frame, self.controller,  bd=2, relief='raised')
        self.import_file_container = ImportFileContainer(self.main_frame, self.controller)
        self.select_attributes_container = SelectAttributesContainer(self.main_frame, self.controller)
        self.start_analysis_container = StartAnalysisContainer(self.main_frame, self.controller)
        self.statusbar = tk.Label(self, bd=2, relief='ridge', anchor='sw', bg='gray', fg='white')
        self.update_statusbar('Waiting for file upload ...')

    def _orient_frame(self):
        self.main_frame.pack(anchor='nw', fill='both', expand=True)
        self.information_container.pack(anchor='nw', fill='both')
        self.import_file_container.pack(anchor='nw', fill='x')
        self.select_attributes_container.pack(anchor='nw', fill='both', expand=True)
        self.start_analysis_container.pack(side='bottom', anchor='sw', fill='x')

    def update_information_container(self, filename):
        self.information_container.update_current_file_label(filename)

    def update_select_analysis(self):
        self.update_button('import_file_container', 'import_file_button', 'disabled')
        self.select_attributes_container.update_attributes()


class RepairSelectFrame(WindowFrame):
    def __init__(self, master, controller):
        """
        Includes all relevant information that is included within the frame by default and initializes the first instance with its parent class
        :param master:
        :param controller:
        """
        # important information that might be changed during the build should be palced above the super()
        super().__init__(master, controller)

    def _setup_frame(self):
        """
        Main function to setup the frame for RepairSelectFrame, inlcuding all containers and their packing
        """
        self.main_frame = tk.Frame(self)
        self.information_container = InformationContainer(self.main_frame, self.controller,  bd=2, relief='raised')
        self.treeview_selection = TreeviewSelection(self.main_frame, self.controller)
        self.legend_container = LegendContainer(self.main_frame, self.controller)
        self.statusbar = tk.Label(self, bd=2, relief='ridge', anchor='sw', bg='gray', fg='white')
        self.update_statusbar('Please select lines to be repaired or skip to next step ...')

    def _orient_frame(self):
        self.main_frame.pack(fill='both', expand=True)
        self.information_container.pack(anchor='nw', fill='x')
        self.treeview_selection.pack(anchor='nw', fill='both', expand=True)
        self.legend_container.pack(anchor='nw', fill='both')

    def update_treeview(self, result_dict):
        self.treeview_selection.update_treeview(result_dict)

    def check_treeview_content(self):
        self.treeview_selection.check_treeview_content()

    def get_repair_ids(self):  # deprecated
        return self.treeview_selection.get_indices_for_repair()

    def get_final_repair_ids(self):
        return self.treeview_selection.return_final_repair_ids()
