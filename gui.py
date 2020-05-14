from world import World
from critter import Critter
from food import Food
from custom_widgets import *

import tkinter as tk
import tkinter.ttk as ttk
from random import randint
from math import sqrt
import time
from types import MethodType

class MainWindow(tk.Tk):

    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 840

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Current Extensions
        self.gui_world = GUI_World(World)
        self.gui_species = [GUI_Species(Critter)]
        #self.gui_foods = [GUI_Food(Food)]

        # Control state
        self.world_state = None
        self.running = False

        # Initial size and placement
        monitor_width = self.winfo_screenwidth()
        monitor_height = self.winfo_screenheight()
        x = monitor_width - self.WINDOW_WIDTH - 25
        y = 10
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x}+{y}")
        self.title("Simu")
        self.create_widgets()

    def create_widgets(self):
        # Notebook
        notebook = StyledNotebook(self)
        notebook.place(relwidth=1, relheight=1)

        # Main Tab
        main_tab = tk.Frame(notebook, bg='#556144', bd=5)
        notebook.add(main_tab, text="Main")

        # Main Tab Layout
        main_tab.rowconfigure(0, weight=1)
        main_tab.columnconfigure(0, weight=1)

        self.extensions_panel = ScrollFrame(main_tab, bg='#73543F', relief='ridge', bd=2, width=50, pady=10)
        self.map_panel = WorldMap(main_tab, bg='#9CB466')

        self.map_panel.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.extensions_panel.grid(row=0, column=1, sticky='n', padx=2, pady=2)

        # Map Control

        self.map_controls = tk.Frame(self.map_panel, bg='#73543F', relief='ridge', bd=2)
        self.map_controls.grid(row=1, column=0, sticky='nw', pady=(4,0))

        self.load_button = StyledButton(self.map_controls, text="Load world", command=lambda: self.load_world())
        self.play_button = StyledButton(self.map_controls, text="▶", command=lambda: self.play_pause())
        self.step_button = StyledButton(self.map_controls, text="▶❚", command=lambda: self.next_frame())
        self.test_button = StyledButton(self.map_controls, text="test", command=lambda: self.test())

        self.load_button.grid(row=0, column=0, padx=(2,10), pady=2)
        self.play_button.grid(row=0, column=1, pady=2)
        self.step_button.grid(row=0, column=2, pady=2)
        self.test_button.grid(row=0, column=3, padx=(10,2), pady=2)

        # Extensions Panel
        self.world_view = tk.LabelFrame(self.extensions_panel, text="World", height=20, bg='blue')
        self.world_view.grid(row=0, column=0, sticky='ew', padx=(10, 5))
        world_label = tk.Label(self.world_view, text="World size or whatever")
        world_label.pack()

        self.critter_views = tk.LabelFrame(self.extensions_panel, text="Species", bg='red', height=20)
        self.critter_views.grid(row=1, column=0, sticky='nsew', padx=(10,5), pady=10)

        for species in self.gui_species:
            self.show_species_view(species)

        self.food_views = tk.LabelFrame(self.extensions_panel, text="Food", height=20, bg='green')
        self.food_views.grid(row=2, column=0, sticky='nsew', padx=(10,5))
        food_label = tk.Label(self.food_views, text="Sorts of food here")
        food_label.pack()

        # Critter Tab
        critter_tab = tk.Frame(notebook, bg='tan', bd=10)
        notebook.add(critter_tab, text="Critters")

    def load_world(self):
        self.pause()
        world = self.world_state = self.gui_world.start_new()
        world.set_up_food()
        for species in self.gui_species:
            critters = [species(world, age=randint(0,species.MAX_AGE)) for _ in range(species.init_pop.get())]
            world.add_critters(critters)
        self.draw_world()

    def play_pause(self):
        if self.running:
            self.pause()
        elif self.world_state is None:
            self.load_button.flash()
        else:
            self.play()

    def play(self):
        self.running = True
        self.play_button.configure(text="❚❚")
        while self.running:
            self.step()
            time.sleep(0.05)

    def pause(self):
        self.running = False
        self.play_button.configure(text="▶")

    def next_frame(self):
        self.pause()
        if self.world_state is None:
            self.load_button.flash()
            return
        self.step()

    def step(self):
        self.world_state.step()
        self.draw_world()
        self.map_panel.canvas.update()

    # Map Drawing

    def draw_world(self):
        world = self.world_state
        canvas = self.map_panel.canvas
        canvas.delete('critter')
        canvas.delete('food')
        for food in world.all_food:
            self.draw_food(food)
        for critter in world.all_critters:
            self.draw_critter(critter)
        scale = canvas.winfo_width() / world.size
        canvas.scale('all', 0, 0, scale, scale)

    def draw_critter(self, critter):
        canvas = self.map_panel.canvas
        diam = critter.reach
        x,y = critter.loc
        x -= diam/2
        y -= diam/2
        canvas.create_rectangle(x, y, x+diam, y+diam, fill='red', outline='red', tags='critter')
        canvas.create_circle(x, y, critter.per_food, tags='critter')

    def draw_food(self, food):
        canvas = self.map_panel.canvas
        radius = sqrt(food.amount_left)/3
        x,y = food.loc
        canvas.create_circle(x, y, radius, fill='green', outline='green', tags='food')

    def test(self):
        print(self.extensions_panel.scrollbar_box.winfo_width())

class WorldMap(ScalingCanvas):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        def create_circle(self, x0, y0, r, **kwargs):
            return self.create_oval(x0-r, y0-r, x0+r, y0+r, **kwargs)
        self.canvas.create_circle = MethodType(create_circle, self.canvas)

class GUI_World():
    '''
        Represents a World subclass loaded into the GUI and possibly modified via the GUI
    '''
    def __init__(self, world_base):
        self.base = world_base
        self.desc = tk.StringVar()
        self.desc.set(self.base.DESCRIPTION)
        self.name = tk.StringVar()
        self.name.set(world_base.__name__)
        self.size = tk.IntVar()
        self.size.set(self.base.SIZE)

    def start_new(self):
        return self.base(self.size.get())   # food drops go here

class GUI_Species():
    '''
        Represents a Critter subclass loaded into the GUI and possibly modified via the GUI
    '''
    def __init__(self, species_base):
        self.base = species_base
        self.desc = tk.StringVar()
        self.desc.set(species_base.DESCRIPTION)
        self.name = tk.StringVar()
        self.name.set(species_base.__name__)
        self.icon_color = ''                # use StringVar trace?
        self.init_pop = tk.IntVar()
        self.init_pop.set(0)
        self.view = None
        self.panel = None

    def get_panel(self, parent, *args, **kwargs):
        panel = tk.Frame(parent, *args, **kwargs)


    def get_view(self, parent, *args, **kwargs):
        if self.view is None:
            view = tk.Frame(parent, *args, **kwargs)
            color_frame = tk.Frame(view, bg=self.icon_color)
            name_label = tk.Label(view, textvariable=self.name)
            init_pop_entry = tk.Entry(view, textvariable=self.init_pop)
            desc_label = tk.Label(view, textvariable=self.desc)

            color_frame.grid(row=0, column=0)
            name_label.grid(row=0, column=1, sticky='nsew')
            init_pop_entry.grid(row=0, column=2)
            desc_label.grid(row=1, column=0, columnspan=3)

            self.view = view
        return self.view

def hier_c(widget, depth=0):
    name = str(widget).split('.')[-1]
    print('\t'*depth, name)
    for child in widget.children.values():
        hier_c(child, depth+1)

def hier_s(widget, depth=0):
    name = str(widget).split('.')[-1]
    print('\t'*depth, name)
    for slave in slaves(widget):
        hier_s(slave, depth+1)

def slaves(widget):
    return widget.grid_slaves() + widget.pack_slaves() + widget.place_slaves()

def launch():
    root = MainWindow()
    root.mainloop()

if __name__=='__main__':
    launch()