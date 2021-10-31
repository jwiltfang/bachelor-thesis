import tkinter as tk
from .frames import *
from .menubar import Menubar


class Window(tk.Tk):
    """
    Implementation for a basic tkinter main window

    Handles the general functions regarding the entire window, its properties, short-cuts etc.
    """

    def __init__(self, controller):
        tk.Tk.__init__(self)
        self.controller = controller

        self.standard_size = '1000x1000'
        self.standard_title = 'Process Event Log Repair Engine'

        self.attributes('-fullscreen', False)
        self.fullScreenState = False
        self.iconphoto(False, tk.PhotoImage(file=r'nlp_label_quality/view/tkinter_elements/icons/icon.png'))

        self.geometry(self.standard_size)
        self.title(self.standard_title)

        # hotkeys for application
        self.bind("<F11>", self.toggle_full_screen)
        self.bind("<Escape>", self.quit_full_screen)
        self.config(menu=Menubar(self, controller))

        self.frame = None
        self.switch_frame(StartFrame)

    def switch_frame(self, frame_class):
        """
        Destroys the current top frame and builds the next one on top

        :param frame_class:
        """
        new_frame = frame_class(self, self.controller)
        if self.frame is not None:
            self.frame.destroy()
        self.frame = new_frame
        self.frame.pack(fill='both', expand=True)
        self.controller.frame = new_frame

    def toggle_full_screen(self, *args):  # should these be implemented by controller or not
        if not self.fullScreenState:
            self.geometry(self.standard_size)
        self.fullScreenState = not self.fullScreenState
        self.attributes("-fullscreen", self.fullScreenState)

    def quit_full_screen(self, *args):
        self.fullScreenState = False
        self.attributes("-fullscreen", self.fullScreenState)
        self.geometry(self.standard_size)
