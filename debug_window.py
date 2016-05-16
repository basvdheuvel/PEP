import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import sys
import fcntl
import os
import subprocess


class DebugWindow:
    """Create a Tk window for displaying debug messages.

    The `Window` class in this script is the actual window. By invoking this
    file directly, such a window is created. This window reads from stdin. This
    class does exactly that. It runs this script as a subprocess, linking its
    stdin to a writable buffer.
    """

    def __init__(self, title='State Machine'):
        """Initialize a debug window.

        Opens a Tk window in a subprocess, in text-mode which allows the stdin
        pipe to be used for text directly.

        Keyword arguments:
        title -- the window's initial title (default 'State Machine')
        """
        self.proc = subprocess.Popen(
            [sys.executable, os.path.realpath(__file__)],
            stdin=subprocess.PIPE, universal_newlines=True)

        self.set_title(title)

    def write(self, text):
        """Write a line to the window.

        The window might have been closed by the user or some different event.
        This is ignored.

        Arguments:
        text -- text excluding newline
        """
        try:
            self.proc.stdin.write(text + '\n')
            self.proc.stdin.flush()
        except BrokenPipeError:
            ...

    def set_title(self, title):
        """Set the window's title.

        Arguments:
        title -- the title
        """
        self.write('#' + title)

    def close(self):
        """Close the window's stdin pipe.

        This does not actually close the window, only the stream. The window is
        kept open so the user can analyse states even after a program is
        finished.
        """
        try:
            self.proc.stdin.close()
        except BrokenPipeError:
            ...


class Window(tk.Tk):
    """Show a Tk window with scrollable text from stdin.

    Checks stdin for a new line every one millisecond. If the line starts with
    a `#', the rest of the line is used as a new title for the window.
    Otherwise, the line is appended to the textfield, including the newline
    character.
    """

    def __init__(self):
        """Initialize the window.

        Creates a frame, holding a srollable textfield. Finally reading from
        stdin is initiated.
        """
        super().__init__()

        self.title('State Machine')

        self.frame = tk.Frame(self)
        self.frame.pack(fill='both', expand=True)

        self.text = ScrolledText(self.frame, wrap='word')
        self.text.configure(state='disabled')
        self.text.pack(side='top', fill='both', expand=True)
        self.text.bind('<1>', lambda ev: self.text.focus_set())

        self.after(1, self.do_read)

    def do_read(self):
        """Try to read a file from stdin."""
        line = sys.stdin.readline()

        if line is not None and line != '':
            self.process_line(line)

        self.after(1, self.do_read)

    def process_line(self, line):
        """Process a line for debug display.

        If a line starts with `#', change the window's title. Otherwise, write
        the line to the textbox.

        Arguments:
        line -- the line to be processed, including newline character
        """
        if line[0] == '#':
            self.title(line[1:].rstrip('\n'))

        else:
            self.write_text(line)

    def write_text(self, text):
        """Write text to the end of the textfield.

        Arguments:
        text -- the text to be added to the textfield.
        """
        self.text.configure(state='normal')

        self.text.insert('end', text)

        # Only autoscroll when at end.
        if self.text.vbar.get()[1] == 1.0:
            self.text.pos = self.text.index('end - 1 char')
            self.text.yview_pickplace('end')

        self.text.configure(state='disabled')


def make_nonblocking(fh):
    """Make a file nonblocking.

    TODO: Figure out how this actually works and explain.
    """
    if hasattr(fh, 'fileno'):
        fh = fh.fileno()
        fcntl.fcntl(fh, fcntl.F_SETFL,
                    os.O_NONBLOCK | fcntl.fcntl(fh, fcntl.F_GETFL))


def main():
    """Make stdin nonblocking and open a window."""
    make_nonblocking(sys.stdin)

    app = Window()
    app.mainloop()


if __name__ == '__main__':
    main()
