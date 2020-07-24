from critter import Critter
from food import Food
from world import World
from biology import BioAssumptions

import tkinter as tk
from tkinter.filedialog import askopenfilename
import os
import sys

def load_extension():
    cwd = os.path.dirname(__file__)
    ext_directory = os.path.join(cwd, 'User-Created Extensions')
    sys.path.insert(0, ext_directory)

    tk.Tk().withdraw()
    full_path = askopenfilename(initialdir=sys.path[0], filetypes=[("Python", '*.py')])
    filename = os.path.basename(full_path)

    extension = __import__(filename.replace('.py', ''))
    return extension

def load_critter():
    extension = load_extension()
    return {cls.__name__ : cls
                for cls in extension.__dict__.values()
                if isinstance(cls, type) and issubclass(cls, Critter) and cls is not Critter
            }

def load_food():
    extension = load_extension()
    return {cls.__name__ : cls
                for cls in extension.__dict__.values()
                if isinstance(cls, type) and issubclass(cls, Food) and cls is not Food
            }

def load_world():
    extension = load_extension()
    return {cls.__name__ : cls
                for cls in extension.__dict__.values()
                if isinstance(cls, type) and issubclass(cls, World) and cls is not World
            }

def load_bioassumptions():
    extension = load_extension()
    return {cls.__name__ : cls
                for cls in extension.__dict__.values()
                if isinstance(cls, type) and issubclass(cls, BioAssumptions) and cls is not BioAssumptions
            }