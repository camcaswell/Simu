import tkinter as tk

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

        # Initial size and placement
        monitor_width = self.winfo_screenwidth()
        monitor_height = self.winfo_screenheight()
        x = monitor_width - self.WINDOW_WIDTH - 25
        y = 10
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{x}+{y}")

        # Main frame
        main = tk.Frame(self, bg='light gray', bd=15)
        main.place(relwidth=1, relheight=1)

        # WIDGETS

        # World canvas
        W = 400
        H = 400
        world_holder = tk.Frame(main, bg='pink')

        world_canvas = tk.Canvas(world_holder, bg='light yellow', height=H, width=W, highlightthickness=0)
        world_canvas.grid(row=0, column=0, sticky='nsew')
        maintain_aspect(world_holder, world_canvas)

        myo = world_canvas.create_oval(100, 200, 120, 240)
        world_canvas.create_circle(100, 20, 20, fill='red')

        # Buttons
        button = tk.Button(main, text="move pls", relief='raised', command=lambda: print('button pressed'))
        f0 = tk.Button(main, bg='purple', text='113241234')
        f1 = tk.Button(main, bg='blue', text='2123423')
        f2 = tk.Button(main, bg='orange', text='3234')

        # LAYOUT
        main.rowconfigure(3, weight=1)  #expansion row depends on how many buttons in adjacent column shouldn't be affected
        main.columnconfigure(1, weight=1)

        # World map
        world_holder.grid(row=0, column=0, rowspan=4, columnspan=2, sticky="nsew")

        # Bottom buttons
        button.grid(row=4, column=0)

        # Right buttons
        f0.grid(row=0, column=2, sticky='nw')
        f1.grid(row=1, column=2, sticky='nw')
        f2.grid(row=2, column=2, sticky='nw')

def maintain_aspect(container, content):

    def resize(event):

        print("resize called")

        if event.serial < 100 and container.old_width == 1 and container.old_height == 1:
            new_size = min(event.width, event.height)
            content.configure(width=new_size, height=new_size)
            content.old_width = new_size
            content.old_height = new_size
            return  # dodge a Configure event that occurs when the window opens

        if event.width != container.old_width or event.height != container.old_height:
            print(event.serial)

            new_size = min(event.width, event.height)
            scale = new_size / content.old_width

            content.scale('all', 0, 0, scale, scale)

            content.configure(width=new_size, height=new_size)
            content.old_width = new_size
            content.old_height = new_size

    container.bind('<Configure>', resize)


root = MainWindow()
root.mainloop()