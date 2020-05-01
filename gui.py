from world import World
from critter import Critter
from food import Food

import tkinter as tk
from random import randint
from math import sqrt
import time


# Monkey patching

def _create_circle(self, x0, y0, r, **kwargs):
    return self.create_oval(x0-r, y0-r, x0+r, y0+r, **kwargs)
tk.Canvas.create_circle = _create_circle

temp = tk.Widget.__init__
def _new_init(self, *args, **kwargs):
    temp(self, *args, **kwargs)
    self.old_width = self.winfo_width()
    self.old_height = self.winfo_height()
tk.Widget.__init__ = _new_init

class MainWindow(tk.Tk):

    WINDOW_WIDTH = 600
    WINDOW_HEIGHT = 800

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # CONTROL STATE
        self._world_size = tk.IntVar()
        self._world_size.set(400)

        self._start_pop = tk.IntVar()
        self._start_pop.set(50)

        # OTHER
        self._world_canvas = None

        # Initial size and placement
        monitor_width = self.winfo_screenwidth()
        monitor_height = self.winfo_screenheight()
        x = monitor_width - self.WINDOW_WIDTH - 25
        y = 10
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x}+{y}")
        self.title("Simu")
        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main = tk.Frame(self, bg='light gray', bd=15)
        main.place(relwidth=1, relheight=1)

        # World Canvas
        W = 400
        H = 400
        world_panel = tk.Frame(main, bg='pink')
        world_canvas = tk.Canvas(world_panel, bg='light yellow', height=H, width=W, highlightthickness=0)
        maintain_aspect(world_panel, world_canvas)
        self._world_canvas = world_canvas

        # Entry Panel
        right_panel = tk.Frame(main, bg='dark gray', relief='sunken')

        size_entry = LabelEntry(right_panel, labeltext="World size", var=self._world_size)
        start_pop_entry = LabelEntry(right_panel, labeltext="Initial pop.", var=self._start_pop)

        size_entry.grid(row=0, column=0, sticky='nw')
        start_pop_entry.grid(row=1, column=0, sticky='nw')

        # Button Panel
        bot_panel = tk.Frame(main, bg='dark gray')

        load_button = tk.Button(bot_panel, text="Load world", command=lambda: self.load_world())
        run_button = tk.Button(bot_panel, text="Run", command=lambda: self.run())
        step_button = tk.Button(bot_panel, text="Step", command=lambda: self.step())

        load_button.grid(row=0, column=0, sticky='nw')
        run_button.grid(row=0, column=1, sticky='nw')
        step_button.grid(row=0, column=2, sticky='nw')

        # MAIN LAYOUT
        main.rowconfigure(1, weight=1)
        main.columnconfigure(1, weight=1)

        world_panel.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew")
        bot_panel.grid(row=2, column=0, sticky='nw')
        right_panel.grid(row=0, column=2, sticky='nw')


    def load_world(self):
        world = self._world = World(size=self._world_size.get())
        world.set_up_food()
        critters = [Critter(world, age=randint(0,Critter.MAX_AGE)) for _ in range(self._start_pop.get())]
        world.add_critters(critters)
        self.draw_world()

    def draw_world(self):
        world = self._world
        canvas = self._world_canvas
        canvas.delete('critter')
        canvas.delete('food')
        for food in world.all_food:
            self.draw_food(food)
        for critter in world.all_critters:
            self.draw_critter(critter)
        scale = canvas.winfo_width() / world.size
        canvas.scale('all', 0, 0, scale, scale)

    def draw_critter(self, critter):
        diam = critter.reach
        x,y = critter.loc
        x -= diam/2
        y -= diam/2
        self._world_canvas.create_rectangle(x, y, x+diam, y+diam, fill='red', outline='red', tags='critter')

    def draw_food(self, food):
        radius = sqrt(food.amount_left)/3
        x,y = food.loc
        self._world_canvas.create_circle(x, y, radius, fill='green', outline='green', tags='food')

    def run(self):
        while True:
            self.step()
            time.sleep(0.05)

    def step(self):
        self._world.step()
        self.draw_world()
        self._world_canvas.update()




def maintain_aspect(container, content):

    def resize(event):

        if event.serial < 100 and container.old_width == 1 and container.old_height == 1:
            new_size = min(event.width, event.height)
            content.configure(width=new_size, height=new_size)
            content.old_width = new_size
            content.old_height = new_size
            return  # dodge a Configure event that occurs when the window opens

        if event.width != container.old_width or event.height != container.old_height:
            new_size = min(event.width, event.height)
            scale = new_size / content.old_width
            content.scale('all', 0, 0, scale, scale)
            content.configure(width=new_size, height=new_size)
            content.old_width = new_size
            content.old_height = new_size

    content.grid(row=0, column=0, sticky='nsew')
    container.bind('<Configure>', resize)

class LabelEntry(tk.Frame):
    def __init__(self, parent, labeltext, var, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        label = tk.Label(self, text=labeltext)
        entry = tk.Entry(self, textvariable=var)
        label.grid(row=0, column=0)
        entry.grid(row=0, column=1)



if __name__=='__main__':
    root = MainWindow()
    root.mainloop()