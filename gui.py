from world import World
from critter import Critter
from food import Food

import tkinter as tk
import tkinter.ttk as ttk
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

    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 840

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # CONTROL STATE
        self._running = False
        self._world = None
        self._world_size = tk.IntVar()
        self._world_size.set(400)

        self._start_pop = tk.IntVar()
        self._start_pop.set(50)

        # OTHER
        self.world_canvas = None

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
        main_tab = tk.Frame(notebook, bg='tan', bd=10)
        notebook.add(main_tab, text="Main")

        # World Canvas
        world_panel = ScalingCanvas(main_tab, bg='light yellow')
        self.world_canvas = world_panel.canvas

        # Entry Panel
        right_panel = tk.Frame(main_tab, bg='saddle brown', relief='ridge', bd=2)

        size_entry = LabeledEntry(right_panel, labeltext="World size", var=self._world_size)
        start_pop_entry = LabeledEntry(right_panel, labeltext="Initial pop.", var=self._start_pop)

        size_entry.grid(row=0, column=0, sticky='nw', padx=2, pady=(2,1))
        start_pop_entry.grid(row=1, column=0, sticky='nw', padx=2, pady=(1,2))

        # Button Panel
        bot_panel = tk.Frame(main_tab, bg='saddle brown', relief='ridge', bd=2)

        self.load_button = tk.Button(bot_panel, text="Load world", bg='light yellow', activebackground='orange', command=lambda: self.load_world())
        self.play_button = tk.Button(bot_panel, text="▶", bg='light yellow', activebackground='orange', command=lambda: self.play_pause())
        step_button = tk.Button(bot_panel, text="▶❚", bg='light yellow', activebackground='orange', command=lambda: self.next_frame())
        test_button = tk.Button(bot_panel, text="test", bg='light yellow', activebackground='orange', command=lambda: self.test())

        self.load_button.grid(row=0, column=0, padx=(2,10), pady=2)
        self.play_button.grid(row=0, column=1, pady=2)
        step_button.grid(row=0, column=2, pady=2)
        test_button.grid(row=0, column=3, padx=(10,2), pady=2)

        # Main Tab Layout
        main_tab.rowconfigure(1, weight=1)
        main_tab.columnconfigure(1, weight=1)

        world_panel.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew", padx=1, pady=1)
        bot_panel.grid(row=2, column=0, padx=1, pady=1)
        right_panel.grid(row=0, column=2, padx=1, pady=1)

        # Critter Tab
        critter_tab = tk.Frame(notebook, bg='tan', bd=10)
        notebook.add(critter_tab, text="Critters")

    def load_world(self):
        self.pause()
        world = self._world = World(size=self._world_size.get())
        world.set_up_food()
        critters = [Critter(world, age=randint(0,Critter.MAX_AGE)) for _ in range(self._start_pop.get())]
        world.add_critters(critters)
        self.draw_world()

    def draw_world(self):
        world = self._world
        canvas = self.world_canvas
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
        self.world_canvas.create_rectangle(x, y, x+diam, y+diam, fill='red', outline='red', tags='critter')
        self.world_canvas.create_circle(x, y, critter.per_food, tags='critter')

    def draw_food(self, food):
        radius = sqrt(food.amount_left)/3
        x,y = food.loc
        self.world_canvas.create_circle(x, y, radius, fill='green', outline='green', tags='food')

    def play_pause(self):
        if self._running:
            self.pause()
        elif self._world is None:
            self.load_button.flash()
        else:
            self.play()

    def play(self):
        self._running = True
        self.play_button.configure(text="❚❚")
        while self._running:
            self.step()
            time.sleep(0.05)

    def pause(self):
        self._running = False
        self.play_button.configure(text="▶")

    def next_frame(self):
        if self._world is None:
            self.load_button.flash()
            return
        self.step()

    def step(self):
        self._world.step()
        self.draw_world()
        self.world_canvas.update()

    def test(self):
        pass



class ScalingCanvas(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        bg = parent.cget('bg')
        super().__init__(parent, bg=bg)
        self.border_frame = tk.Frame(self, bg=bg, relief='ridge', bd=2)    # exists to create border without screwing up canvas coordinates
        self.border_frame.grid_propagate(False)
        self.canvas = tk.Canvas(self.border_frame, *args, highlightthickness=0, **kwargs)
        self.border_frame.grid(row=0, column=0, sticky='nsew')
        self.canvas.grid(row=0, column=0, sticky='nsew')

        def resize(event):
            if event.width != self.old_width or event.height != self.old_height:
                new_size = min(event.width, event.height)
                self.border_frame.configure(width=new_size, height=new_size)
                bd = int(self.border_frame.cget('bd'))
                self.canvas.configure(width=new_size-2*bd, height=new_size-2*bd)
                scale = (new_size-2*bd) / self.canvas.old_width
                self.canvas.old_width = new_size-2*bd
                self.canvas.scale('all', 0, 0, scale, scale)
        self.bind('<Configure>', resize)

class LabeledEntry(tk.Frame):
    def __init__(self, parent, labeltext, var, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        label = tk.Label(self, text=labeltext, bg='light yellow', width=12, anchor='w')
        entry = tk.Entry(self, width=10, textvariable=var)
        label.grid(row=0, column=0)
        entry.grid(row=0, column=1)

class StyledNotebook(ttk.Notebook):

    def __init__(self, parent, *args, **kwargs):
        style = ttk.Style()
        style.element_create('Plain.Notebook.tab', 'from', 'default')
        style.layout('TNotebook.Tab',
            [('Plain.Notebook.tab', {'children':
                [('Notebook.padding', {'side': 'top', 'children':
                    [('Notebook.focus', {'side': 'top', 'children':
                        [('Notebook.label', {'side': 'top', 'sticky': ''})],
                    'sticky': 'nsew'})],
                'sticky': 'nsew'})],
            'sticky': 'nsew'})])
        style.configure('TNotebook', background='saddle brown')
        style.configure('TNotebook.Tab', background='light yellow', foreground='black', borderwidth=2)

        super().__init__(parent, style='TNotebook')


def launch():
    root = MainWindow()
    root.mainloop()

if __name__=='__main__':
    launch()