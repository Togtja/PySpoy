import tkinter as tk

#import PySpoyLogic as pyspoy

window = tk.Tk()
window.title("PySpoy: Global Spotify hotkeys")

def handle_keypress(event):
    """Print the character associated to the key pressed"""
    print(event)

# Bind keypress event to handle_keypress()
window.bind("<Key>", handle_keypress)

window.mainloop()