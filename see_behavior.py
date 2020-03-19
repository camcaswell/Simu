import tkinter as tk
import threading

WINDOW_BUFFER = 10


def run():
    window = tk.Tk()
    window.title("Simu")

    canvas = tk.Canvas(window, width=1000+WINDOW_BUFFER, height=1000+WINDOW_BUFFER)
    canvas.pack()





    window.mainloop()