#!/usr/bin/env python3
#
# Color printing using ANSI terminal escape sequences.
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

# TODO: migrate from tealpkg into libteal (need to refactor a bit)

import shutil
import sys


class ColorPrinter:
    __instance = None

    @staticmethod
    def get_instance():
        if ColorPrinter.__instance is None:
            ColorPrinter.__instance = ColorPrinter()
        #
        return ColorPrinter.__instance
    #
    def __init__(self):
        self.font_map = {
            'reset': 0,
            'bold': 1,
            'faint': 2,
            'italic': 3,
            'underline': 4,
            'slow-blink': 5,
            'fast-blink': 6,
            'reverse': 7,
            'conceal': 8,
            'strikethrough': 9,
            'primary-font': 10,
            'alt1-font': 11,
            'alt2-font': 12,
            'alt3-font': 13,
            'alt4-font': 14,
            'alt5-font': 15,
            'alt6-font': 16,
            'alt7-font': 17,
            'alt8-font': 18,
            'alt9-font': 19,
            'fraktur': 20,
            'bold-off': 21,
            'normal': 22,
            'italic-off': 23,
            'underline-off': 24,
            'blink-off': 25,
            'inverse-off': 27,
            'conceal-off': 28,
            'strikethrough-off': 29,
        }
        self.colormap = {
            'black': 0,
            'red': 1,
            'green': 2,
            'yellow': 3,
            'blue': 4,
            'magenta': 5,
            'cyan': 6,
            'white': 7,
            'gray': 8,
            'bright-red': 9,
            'bright-green': 10,
            'bright-yellow': 11,
            'bright-blue': 12,
            'bright-magenta': 13,
            'bright-cyan': 14,
            'bright-white': 15,
        }
        self.styles = { 'default': ('default', 'default', ['reset']) }
        self.use_color = False
        self.color_streams = [ sys.stdout, sys.stderr ]
        self.last_was_status = False
        self.quiet = False
    #
    def map_font(self, font_name, value):
        self.font_map[font_name] = value
    #
    def map_color(self, color_name, value):
        self.colormap[color_name] = value
    #
    def add_style(self, name, foreground, background, *fonteffects):
        self.styles[name] = (foreground, background, fonteffects)
    #
    def set_color(self, fgcolor, bgcolor, *fonteffects, stderr=False):
        stream = sys.stdout
        if stderr:
            stream = sys.stderr
        #

        fgcode = '39'
        if fgcolor in self.colormap:
            fgcode = '38;5;' + str(self.colormap[fgcolor]) + ';'
        #

        bgcode = '49'
        if bgcolor in self.colormap:
            bgcode = '48;5;' + str(self.colormap[bgcolor])
        #

        fontcodes = ''
        for effect in fonteffects:
            if effect in self.font_map:
                fontcodes += str(self.font_map[effect]) + ';'
            #
        #

        print('\033[0;' + fontcodes + fgcode + bgcode + 'm', end='', file=stream)
    #
    def cprint(self, *args, style='default', sep=' ', end='\n', stderr=False, file=sys.stdout, \
               flush=False, is_status=False):
        if self.quiet and not stderr:
            return
        #

        pushed = False
        use_color = self.use_color

        stream = file
        if stderr:
            stream = sys.stderr
        #

        if stream not in self.color_streams or not stream.isatty():
            use_color = False
        #

        if use_color and style in self.styles:
            fgcolor, bgcolor, fonteffects = self.styles[style]
            self.set_color(fgcolor, bgcolor, *fonteffects, stderr=stderr)
            pushed = True
        #

        if is_status and self.last_was_status:
            if stream.isatty():
                print(end='\r', file=stream)
            else:
                print(file=stream)
            #
        elif self.last_was_status:
            print(file=stream)
        #

        print(*args, sep=sep, end=end, file=stream, flush=flush)

        if pushed:
            fgcolor, bgcolor, fonteffects = self.styles['default']
            self.set_color(fgcolor, bgcolor, *fonteffects, stderr=stderr)
        #

        self.last_was_status = is_status
    #
    def get_width(self):
        return shutil.get_terminal_size().columns
    #
    def write_status(self, message, style='default'):
        if not self.quiet:
            spaces = max(0, get_width() - len(message) - 1)
            if not sys.stdout.isatty():
                spaces = 0
            #
            self.cprint(message, spaces * ' ', style=style, sep='', end='', is_status=True)
        #
    #
    def clear_status(self):
        if not self.quiet and self.last_was_status:
            self.write_status('')
            if sys.stdout.isatty():
                print(end='\r')
            #
        #
        self.last_was_status = False
    #
#


def get_printer():
    return ColorPrinter.get_instance()
#

def cprint(*args, style='default', sep=' ', end='\n', stderr=False, file=sys.stdout, flush=False):
    inst = get_printer()
    inst.cprint(*args, style=style, sep=sep, end=end, stderr=stderr, file=file, flush=flush)
#

def get_width():
    inst = get_printer()
    return inst.get_width()
#

def write_status(message, style='default'):
    inst = get_printer()
    inst.write_status(message, style)
#

def clear_status():
    inst = get_printer()
    inst.clear_status()
#
