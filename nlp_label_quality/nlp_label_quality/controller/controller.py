from abc import ABC, abstractmethod

from nlp_label_quality.model.model import Model
from nlp_label_quality.view.view import View
from nlp_label_quality.analysis.analysis import AnalysisModule
from nlp_label_quality.analysis.nlp_models import GloVeModel, SpaCyModel
from nlp_label_quality.view.tkinter_elements.frames import *

from typing import ClassVar
from tkinter import filedialog
import time
import logging
import os

logger = logging.getLogger(__name__)


class Controller(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def start(self):
        pass


class TkEventController(Controller):
    """
    Controller responsible for all main functionality of the programme, conntecting both the front end (View) and the backend(Model)
    The parameter Analysis is responsible for all calculations and filtering methods to return meaningful results

    For better extendibility and easier access and implementation of different methods, ABC are used to pass as an argument to make sure all parts can work with each other

    TkEventController is ideally implemented to work with TkDataModel and TkView

    Parameters
    ----------
    model
        Data Model
    view
        front-end package
    analysis
        analysis module (TODO should be made modular for different interactive analysis modules)
    nlp

    """

    def __init__(self, model: Model, view: View) -> None:
        self.model = model
        self.view = view
        self._frame = None
        self.analysis = None
        self.nlp = None
        self.glove = None

    def start(self):
        self.view.setup(self)
        self.view.start_main_loop()  # main function that keeps the frontend running and reactive

    def handle_click_restart(self):
        self.view.root.destroy()
        self.start()

    def handle_click_import_file(self):
        if not isinstance(self.view.root.frame, StartFrame):  # switch frames if it is not on the start page
            logger.info('Restart View for new Analysis')
            self.view.root.switch_frame(StartFrame)
        self._import_file()

    def handle_click_start_analysis(self):
        self.frame.update_statusbar('Please wait until analysis has finished ...')
        self.model.insert_eval_labels()
        self._setup_models()  # one time setup for NLP models
        self.run_next_analysis()

    def handle_click_run_repair(self):
        final_repair_ids = self.frame.get_final_repair_ids()
        self.model.extend_repair_ids(final_repair_ids)
        logger.info(f'Run repair on {self.model.repair_ids}')
        self.frame.check_treeview_content()
        self.frame.update_statusbar('Selection was registered and log is being repaired.')
        self._update_log()

    def handle_click_run_next_analysis(self):
        self.run_next_analysis()

    def handle_click_export_file(self):
        self._export_file()

    def run_next_analysis(self):
        # only the first analysis is run
        option_index = self.model.analysis_step
        if option_index < len(self.model.analysis_options):
            # reset old repair data
            self.model.reset_repair_data()
            self.analysis = AnalysisModule(str(option_index), self, self.nlp, self.glove,
                                              self.model.analysis_options[option_index],
                                              self.model.analysis_thresholds[option_index])

            self.model.repair_dict = self.analysis.start(self.model.attribute_content)
            self.view.root.switch_frame(RepairSelectFrame)
            self.view.root.frame.update_treeview(self.model.repair_dict)
            if self.model.log_was_changed:
                self.frame.update_button('treeview_selection', 'export_button', 'normal')
            self.model.analysis_step += 1
        else:
            self.frame.update_button('treeview_selection', 'run_analysis_button', 'disabled')

    def _update_log(self):
        self.model.repair_log()
        self.frame.update_button('treeview_selection', 'export_button', 'normal')
        self.frame.update_button('treeview_selection', 'run_analysis_button', 'normal')

    def _export_file(self):
        initial_export_name = os.path.basename(self.model.filename).split('.')[0]
        export_filename = filedialog.asksaveasfilename(initaldir=None,
                                                       initialfile=f'rep_{initial_export_name}',
                                                       defaultextension='.xes',
                                                       title='Save File after Repair',
                                                       filetypes=(("eventlog files", "*.xes"), (
                                                           "all files", ".*")))  # no cvs ("eventlog files", "*.csv")
        if export_filename:
            self.frame.update_statusbar('Exporting ...')
            self.model.export_log(export_filename)
        else:
            logger.error('No file to export the log was selected')

    def _import_file(self):
        import_filename = filedialog.askopenfilename(initialdir=None,
                                                     title="Select a File ...",
                                                     filetypes=(("eventlog files", "*.xes"), ("all files",
                                                                                              ".*")))  # no csv at the moment("eventlog files", "*.csv")
        if import_filename:
            self.model.filename = import_filename
            self.frame.update_information_container(self.model.filename)
            self.model.import_log()
            self.model.filter_for_attributes()
            self.frame.update_select_analysis()
            self.frame.update_statusbar('Please select the relevant_attributes')
            self.frame.update_button('select_attributes_container', 'select_button', 'normal')
        else:
            logger.error('No file was uploaded')

    def attributes_selected(self, selected_attributes):
        if selected_attributes:
            self.model.selected_attributes = selected_attributes
            self.model.preprocess_log()
            self.frame.update_statusbar('Analysis ready to go ...')
            self.frame.update_button('start_analysis_container', 'start_analysis_button', 'normal')

    def _setup_models(self):
        if not self.model.models_loaded:
            tic = time.perf_counter()
            self.nlp = SpaCyModel('spacy')
            self.glove = GloVeModel('glove')
            self.model.models_loaded = True
            toc = time.perf_counter()
            logger.info(f'Models setup in {toc - tic} seconds')
        else:
            pass

    def get_filename(self):
        return self.model.filename

    def get_treeview_headers(self):
        return self.model.treeview_headers

    def get_analysis_step(self):
        step = self.model.analysis_step
        total_steps = len(self.model.analysis_options)
        return step, total_steps

    def get_relevant_attributes(self):
        return self.model.relevant_attributes

    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, new_frame):
        self._frame = new_frame

    def __repr__(self):
        return f'TkEventController({self.model!r}, {self.view!r}'

    def __str__(self):
        return f'TkEventController: Model, View'
