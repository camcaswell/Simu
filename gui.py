from world import World
from critter import Critter
from food import Food
import load_extensions
from custom_widgets import *

import tkinter as tk
import tkinter.ttk as ttk
from random import randint
from math import sqrt
from time import sleep
from types import MethodType

class MainWindow(tk.Tk):

    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 840

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Current Extensions
        self.gui_world = GUI_World(World)
        default_species = GUI_Species(Critter)
        default_species.icon_color.set('maroon')
        self.gui_species = {Critter: default_species}
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
        self.world_box = tk.LabelFrame(self.extensions_panel, text="WORLD", padx=2, pady=2, height=20, bg='blue')
        self.world_box.grid(row=0, column=0, sticky='ew', padx=(10, 5))
        world_view = self.gui_world.get_view(self.world_box)
        #world_view.grid(row=0, column=0, padx=5, sticky='nsew')
        world_view.pack(expand=True, fill='both')

        self.critter_views = tk.LabelFrame(self.extensions_panel, text="SPECIES", padx=2, pady=2, height=20, bg='red')
        self.critter_views.grid(row=1, column=0, sticky='nsew', padx=(10,5), pady=10)

        self.food_views = tk.LabelFrame(self.extensions_panel, text="FOOD", padx=2, pady=2, height=20, bg='green')
        self.food_views.grid(row=2, column=0, sticky='nsew', padx=(10,5))
        food_label = tk.Label(self.food_views, text="Sorts of food here")
        food_label.pack()

        # Critter Tab
        critter_tab = tk.Frame(notebook, bg='tan', bd=10)
        notebook.add(critter_tab, text="Critters")

        load_critter_button = StyledButton(critter_tab, text="Load New Species", command=lambda: self.species_popup())
        load_critter_button.grid()

        for species in set(self.gui_species.values()):
            self.show_species_view(species)
    def species_popup(self):
        options = load_extensions.load_critter()
        popup = tk.Toplevel()
        popup.minsize(350, 100)
        popup.title("Choose Critter")
        popup.rowconfigure(0, weight=1)
        popup.columnconfigure(0, weight=1)
        popup_frame = tk.Frame(popup, bg='tan')
        popup_frame.grid(row=0, column=0, sticky='nsew')
        popup_frame.columnconfigure(0, weight=1)
        if options:
            for i, (name, cls) in enumerate(options.items()):
                button = StyledButton(popup_frame, text=f"   {name}   ", relief='ridge', pady=10, command=lambda cls=cls: self.species_popup_click(cls, popup))
                button.grid(row=i, column=0, padx=20, pady=(20,0), sticky='ew')
            button.grid(row=i, column=0, padx=20, pady=(20,20))    # redoing last one to get padding at the end
        else:
            item = tk.Label(popup_frame, text="No Critter extensions found in that file")

    def species_popup_click(self, cls, popup):
        new_species = GUI_Species(cls)
        self.gui_species[cls] = new_species
        self.show_species_view(new_species)
        popup.destroy()

    def show_species_view(self, species):
        view = species.get_view(self.critter_views)
        view.grid(sticky='ew')

    # Map Control

    def load_world(self):
        self.pause()
        world = self.world_state = self.gui_world.start_new()
        world.set_up_food()
        for species_base, species_guirep in self.gui_species.items():
            critters = [species_base(world, age=randint(0,species_base.MAX_AGE)) for _ in range(species_guirep.init_pop.get())]
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
            sleep(0.05)

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
        gui_rep = self.gui_species[type(critter)]
        color = gui_rep.icon_color.get()
        canvas = self.map_panel.canvas
        diam = critter.reach
        x,y = critter.loc
        x -= diam/2
        y -= diam/2
        canvas.create_rectangle(x, y, x+diam, y+diam, fill=color, outline=color, tags='critter')
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
        self.view = None
        self.panel = None

    def start_new(self):
        return self.base(self.size.get())   # food drops go here

    def get_view(self, parent):
        if self.view is None:
            view = StyledViewFrame(parent)
            bg = view.cget('bg')
            name_label = tk.Label(view, textvariable=self.name, bg=bg)
            size_entry = LabeledEntry(view, labeltext="Size", var=self.size, bg=bg)
            desc_label = tk.Label(view, textvariable=self.desc, bg=bg)

            name_label.grid(row=0, column=0, sticky='w')
            size_entry.grid(row=1, column=0, sticky='w')
            desc_label.grid(row=2, column=0, sticky='w')

            self.view = view
        return self.view

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
        self.init_pop = tk.IntVar()
        self.init_pop.set(0)
        self.view = None
        self.panel = None

        self.icon_color = tk.StringVar()
        self.icon_color.set('')
        def color_set_callback(var, indx, mode):
            if self.view is not None:
                self.color_icon_view.configure(bg=var.get())
            if self.panel is not None:
                self.color_icon_panel.configure(bg=var.get())
        self.icon_color.trace_add('write', color_set_callback)


    def get_panel(self, parent, *args, **kwargs):
        panel = tk.Frame(parent, *args, **kwargs)


    def get_view(self, parent):
        if self.view is None:
            view = StyledViewFrame(parent)
            bg = view.cget('bg')
            self.color_icon_view = tk.Frame(view, width=15,  height=15, bg=self.icon_color.get())
            name_label = tk.Label(view, textvariable=self.name, bg=bg)
            init_pop_entry = LabeledEntry(view, labeltext="Pop.", var=self.init_pop, bg=bg)
            desc_label = tk.Label(view, textvariable=self.desc, bg=bg)

            view.columnconfigure(1, weight=1)
            self.color_icon_view.grid(row=0, column=0, sticky='w')
            name_label.grid(row=0, column=1, sticky='w')
            init_pop_entry.grid(row=1, column=0, columnspan=2, sticky='w')
            desc_label.grid(row=2, column=0, columnspan=2, sticky='w')

            self.view = view
        return self.view

def launch():
    root = MainWindow()
    root.mainloop()

if __name__=='__main__':
    launch()