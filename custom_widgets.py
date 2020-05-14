import tkinter as tk
import tkinter.ttk as ttk
from math import inf as INF

class OptionsPopup(tk.Toplevel):
    def __init__(self, options):
        pass

class ScalingCanvas(tk.Frame):
    '''
        A Canvas that enforces a 1:1 aspect ratio as it scales.
    '''
    def __init__(self, parent, *args, **kwargs):
        bg = parent.cget('bg')
        super().__init__(parent, bg=bg)
        self.border_frame = tk.Frame(self, bg=bg, relief='ridge', bd=2)    # exists to create border without screwing up canvas coordinates
        kwargs = {'highlightthickness': 0, **kwargs}
        self.canvas = tk.Canvas(self.border_frame, *args, **kwargs)
        self.border_frame.grid(row=0, column=0)
        self.canvas.grid(row=0, column=0)

        self.canvas.old_width = self.winfo_width()
        self.canvas.old_height = self.winfo_height()

        self.bind('<Configure>', lambda event: self.resize(event))

    def resize(self, event):
        other_widgets = [w for w in self.grid_slaves() if w is not self.border_frame]
        adj_height = event.height - sum([w.winfo_reqheight() for w in other_widgets])   #assuming other widgets are stacked vertically
        new_size = min(event.width, adj_height)
        self.border_frame.configure(width=new_size, height=new_size)
        bd = int(self.border_frame.cget('bd'))
        self.canvas.configure(width=new_size-2*bd, height=new_size-2*bd)
            scale = (new_size-2*bd) / self.canvas.old_width
            self.canvas.old_width = new_size-2*bd
            self.canvas.scale('all', 0, 0, scale, scale)

class LabeledEntry(tk.Frame):
    '''
        An Entry widget next to a Label widget.
    '''
    def __init__(self, parent, labeltext, var, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        label = tk.Label(self, text=labeltext, bg='light yellow', width=12, anchor='w')
        entry = tk.Entry(self, width=10, textvariable=var)
        label.grid(row=0, column=0)
        entry.grid(row=0, column=1)

class StyledNotebook(ttk.Notebook):
    '''
        A Notebook with a standardized appearance.
    '''
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
        style.configure('TNotebook', background='#73543F')
        style.configure('TNotebook.Tab', background='light yellow', foreground='black', borderwidth=2)

        kwargs = {**kwargs, 'style': 'TNotebook'}
        super().__init__(parent, **kwargs)

class StyledButton(tk.Button):
    '''
        A Button with a standardized appearance.
    '''
    def __init__(self, parent, *args, **kwargs):
        kwargs = {'bg':'light yellow', 'activebackground':'orange', **kwargs}
        super().__init__(parent, *args, **kwargs)

class BoundedFrame(tk.Frame):
    '''
        Expands to given dimensions but no further.

        To bind other functions to Configure events, append them to config_callbacks.
    '''
    def __init__(self, parent, *args, maxw=INF, maxh=INF, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.maxw = maxw
        self.maxh = maxh

        self.bind('<Configure>', lambda event: self.on_config(event))
        self.config_callbacks = [lambda event: self.resize(event)]

    def on_config(self, event):
        for func in self.config_callbacks:
            func(event)

    def resize(self, event):
        w = min(self.maxw, event.width)
        h = min(self.maxh, event.height)
        self.configure(width=w, height=h)
        if self.winfo_manager() == 'grid':
            kwargs = {**self.grid_info(), 'sticky': ''}
            if event.width < self.maxw:
                kwargs['sticky'] += 'ew'
            if event.height < self.maxh:
                kwargs['sticky'] += 'ns'
            self.grid(**kwargs)
        elif self.winfo_manager() == 'pack':
            kwargs = {**self.pack_info(), 'expand': True}
            exp_x = ('x' if event.width<self.maxw else '')
            exp_y = ('y' if event.height<self.maxh else '')
            if exp_x and exp_y:
                kwargs['fill'] = 'both'
            elif not (exp_x or exp_y):
                kwargs['fill'] = 'none'
            else:
                kwargs['fill'] = exp_x+exp_y
            self.pack(**kwargs)
        else:
            raise Exception("This widget should be packed or gridded.")

class CompositeContainer():
    '''
        A class for custom widgets that need to act as a fully-capable container but also
        include other components outside the container.

        General widget methods are routed to the exterior frame, all others to the interior.

        Keyword arguments are passed to exterior, background color is also sent to interior.

        If you want intermediate widgets between exterior and interior, just overwrite 
        self.interior so it has the proper parentage.

        Does not support multiple inheritance.
    '''

    def __init__(self, parent, *args, intclass=tk.Frame, extclass=tk.Frame, **kwargs):
        bg = kwargs.pop('bg', kwargs.pop('background', None))
        self.exterior = extclass(parent, *args, bg=bg, **kwargs)
        self.interior = intclass(self.exterior, bg=bg)

    def __getattr__(self, name):
        if name in list(self.__dict__) + dir(object) + ['__dict__']:
            return getattr(self, name)
        elif name in dir(tk.Widget):
            return getattr(self.exterior, name)
        elif name in dir(self.interior):
            return getattr(self.interior, name)
        else:
            raise AttributeError(name)

class ScrollFrame(CompositeContainer):
    '''
        A Frame with a vertical scroll bar.
    '''
    def __init__(self, parent, *args, scrollside='right', **kwargs):
        super().__init__(parent, *args, **kwargs)
        bg = kwargs.get('bg', kwargs.get('background', None))
        self.canvas = tk.Canvas(self.exterior, bd=0, bg=bg, highlightthickness=0)
        self.scrollbar_box = tk.Frame(self.exterior, bg=bg)
        self.scrollbar_box.pack_propagate(False)
        self.scrollbar = tk.Scrollbar(self.scrollbar_box, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        contentcol = (0 if scrollside=='right' else 1)
        self.canvas.grid(row=0, column=contentcol, sticky='nsew')
        self.scrollbar_box.grid(row=0, column=1-contentcol)  # height to be set by resize event method
        self.scrollbar.pack(expand=True, fill='y')
        self.exterior.columnconfigure(contentcol, weight=1)
        self.exterior.rowconfigure(0, weight=1)

        self.interior = tk.Frame(self.canvas, bg=bg)     # recreated so that it has canvas as parent
        self.interior_id = self.canvas.create_window(0, 0, window=self.interior, anchor='nw')

        self.interior.bind('<Configure>', lambda event: self.reset_scrollregion(event))
        self.exterior.bind('<Configure>', lambda event: self.resize(event))

    def reset_scrollregion(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def resize(self, event):
        if (max_desired := self.interior.winfo_reqheight()) > event.height:
            new_height = event.height
            self.scrollbar.pack(expand=True, fill='y')
        else:
            new_height = max_desired
            self.scrollbar.pack_forget()
        new_height = min(self.interior.winfo_reqheight(), event.height)
        self.canvas.configure(height=new_height, width=self.interior.winfo_reqwidth())
        self.scrollbar_box.configure(height=new_height, width=self.scrollbar.winfo_reqwidth())

class BoundedScrollFrame(CompositeContainer):
    '''
        A Frame with a vertical scroll bar.

        Setting maxw and maxh will limit how far it expands.

        maxh clamps to the height of the content inside.
    '''
    def __init__(self, parent, *args, scrollside='right', maxw=INF, maxh=INF, **kwargs):
        super().__init__(parent, *args, extclass=BoundedFrame, maxw=maxw, maxh=maxh, **kwargs)
        bg = kwargs.get('bg', kwargs.get('background', None))
        self.canvas = tk.Canvas(self.exterior, bd=0, bg=bg, highlightthickness=0)
        self.scrollbar_box = tk.Frame(self.exterior, bg=bg)
        self.scrollbar_box.pack_propagate(False)
        self.scrollbar = tk.Scrollbar(self.scrollbar_box, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        contentcol = (0 if scrollside=='right' else 1)
        self.canvas.grid(row=0, column=contentcol, sticky='ew')
        self.scrollbar_box.grid(row=0, column=1-contentcol)  # height to be set by resize event method
        self.scrollbar.pack(expand=True, fill='y')
        self.exterior.columnconfigure(contentcol, weight=1)
        self.exterior.rowconfigure(0, weight=1)

        self.interior = tk.Frame(self.canvas, bg=bg)     # recreated so that it has canvas as parent
        self.interior_id = self.canvas.create_window(0, 0, window=self.interior, anchor='nw')

        self.interior.bind('<Configure>', lambda event: self.reset_scrollregion(event))
        self.exterior.config_callbacks.append(lambda event: self.resize(event))

    def reset_scrollregion(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def resize(self, event):
        self.exterior.maxh = min(self.exterior.maxh, self.interior.winfo_reqheight())
        if (max_desired := self.interior.winfo_reqheight()) > event.height:
            new_height = event.height
            self.scrollbar.pack(expand=True, fill='y')
        else:
            new_height = max_desired
            self.scrollbar.pack_forget()
        new_height = min(self.interior.winfo_reqheight(), event.height)
        self.canvas.configure(height=new_height, width=self.interior.winfo_reqwidth())
        self.scrollbar_box.configure(height=new_height, width=self.scrollbar.winfo_reqwidth())