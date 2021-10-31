import tkinter as tk
from abc import ABC, abstractmethod


class ABCTopLevel(ABC, tk.Toplevel):
    def __init__(self, master, controller):
        tk.Toplevel.__init__(self, master)
        self.controller = controller
        self._setup_frame()

    @abstractmethod
    def _setup_frame(self):
        pass

    def run_and_restrict(self):
        """
        Functions to grab focus from main window, so there can be no changes while the toplevel is open and multiple instances are not possible
        """
        self.grab_set()
        self.focus_set()
        self.mainloop()
        self.grab_release()


class TutorialTopLevel(ABCTopLevel):
    def __init__(self, master, controller):
        self.description_text = "The used references will be added in the future."
        super().__init__(master, controller)

    def _setup_frame(self):
        self.title('Tutorial')
        self.topl_frame = tk.Frame(self)

        self.description = tk.Text(self.topl_frame)
        self.description.insert(tk.END, self.description_text)

        self.label = tk.Label(self, text='(C) Copyright by University of Bayreuth')

        self.topl_frame.pack(anchor='w', fill='x', expand=True)
        self.description.pack(fill='both')
        self.label.pack()


class AboutTopLevel(ABCTopLevel):
    def __init__(self, master, controller):
        self.description_text = \
            "This project was created as part of a bachelor thesis \"Application of Natural Language " \
            "Processing for Detection and Interactive Repair of Labeling Anomalies in Event Logs\" at the University of " \
            "Bayreuth with the Chair BWL VII and the Professorships DEM, NIM, WPM.\n" \
            "The scope of the project was to establish a repair engine to clean labeling anomalies " \
            "within process event logs using Natural Language Processing (NLP) methods."

        super().__init__(master, controller)

    def _setup_frame(self):
        self.title('About the project')
        # self.resizable(True, False)
        self.topl_frame = tk.Frame(self)

        self.description = tk.Text(self.topl_frame)
        self.description.insert(tk.END, self.description_text)

        self.label = tk.Label(self, text='(C) Copyright by University of Bayreuth')
        # pack all elements in order
        self.topl_frame.pack(anchor='w', fill='both', expand=True)
        self.description.pack(fill='both')
        self.label.pack()


class ReferencesTopLevel(ABCTopLevel):
    def __init__(self, master, controller):
        self.description_text = "The used references will be added in the future."
        super().__init__(master, controller)

    def _setup_frame(self):
        self.title('References')
        self.topl_frame = tk.Frame(self)

        self.description = tk.Text(self.topl_frame)
        self.description.insert(tk.END, self.description_text)

        self.label = tk.Label(self, text='(C) Copyright by University of Bayreuth')
        # pack all elements in order
        self.topl_frame.pack(anchor='w', fill='both', expand=True)
        self.description.pack(fill='both')
        self.label.pack()



