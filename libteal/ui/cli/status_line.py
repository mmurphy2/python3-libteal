#!/usr/bin/env python3
#
# Implements a bottom status line using ANSI terminal control sequences.
#
# Copyright 2021-2022 Coastal Carolina University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#


# TODO: refactor for libteal
# TODO: make into a context manager (and trap SIGWINCH)
# TODO: evaluate whether or not to generalize to a top and bottom line

import shutil


class StatusLine:
    def __init__(self):
        self.enabled = False
        self.quiet = False
        self.last_height = 0
        self.last_width = 0
    #
    def check_size(self):
        size = shutil.get_terminal_size()
        if size.lines != self.last_height or size.columns != self.last_width:
            self.disable()
            self.enable()
        #
    #
    def enable(self):
        if not self.enabled and not self.quiet:
            self.enabled = True
            size = shutil.get_terminal_size()
            self.last_width = size.columns
            height = size.lines
            self.last_height = height
            print('\n\n')   # 2 sacrifical blank lines to be eaten during the split
            print('\033[0;', height - 2, 'r', sep='', end='')   # split the screen, leaving the bottom 2 lines for status
            print('\033[', height - 1, ';1H', sep='', end='')   # move to the first line of the status bar
            cprint('\u2500' * (size.columns), style='separator', end='\n')  # produce the separator
            print('\033[1F', end='')      # move back up above the status bar
    #####
    def disable(self):
        if self.enabled and not self.quiet:
            size = shutil.get_terminal_size()
            print('\033[s', end='')  # save the cursor
            print('\033[', size.lines - 1, ';1H', sep='', end='') # move to the separator line
            print(' ' * size.columns, end='')   # clear the separator
            print('\033[1E', end='')  # move down to the status line
            print(' ' * size.columns, end='')   # clear the status line
            print('\033[;r\033[u', end='') # end the split, then restore the cursor
            self.enabled = False
    #####
    def enter(self):
        if self.enabled and not self.quiet:
            self.check_size()
            size = shutil.get_terminal_size()
            print('\033[', size.lines, ';1H', sep='', end='')   # Move to the status line (bottom line)
    #####
    def leave(self):
        if self.enabled and not self.quiet:
            print('\033[2F', end='')   # Move up 2 lines (to the line before the status line)
    #####
#
