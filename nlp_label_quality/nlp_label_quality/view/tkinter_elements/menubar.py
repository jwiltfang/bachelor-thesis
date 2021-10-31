import tkinter as tk
from .toplevels import TutorialTopLevel, AboutTopLevel, ReferencesTopLevel


class Menubar(tk.Menu):
    def __init__(self, master, controller):
        tk.Menu.__init__(self, master)
        self.controller = controller

        # FILEMENU cascade
        self.filemenu = tk.Menu(self, tearoff=False)
        self.add_cascade(label="File", menu=self.filemenu)
        self.filemenu.add_separator()
        # close window and program
        self.filemenu.add_command(label="Exit", accelerator="Alt+F4", command=quit)

        # HELPMENU cascade
        self.helpmenu = tk.Menu(self, tearoff=False)
        self.add_cascade(label="Help", menu=self.helpmenu)
        # show tutorial toplevel
        self.helpmenu.add_command(label="Tutorial", command=self.tutorial, accelerator="Strg+T")
        self.bind_all('<Control-t>', self.tutorial)

        self.helpmenu.add_separator()
        # show about toplevel
        self.helpmenu.add_command(label="About", command=self.about)
        # show references toplevel
        self.helpmenu.add_command(label="Libraries", command=self.references)

    def tutorial(self, *args):
        self.tutorial_toplevel = TutorialTopLevel(self, self.controller)
        self.tutorial_toplevel.run_and_restrict()

    def about(self, *args):
        self.about_toplevel = AboutTopLevel(self, self.controller)
        self.about_toplevel.run_and_restrict()

    def references(self, *args):
        self.references_toplevel = ReferencesTopLevel(self, self.controller)
        self.references_toplevel.run_and_restrict()
