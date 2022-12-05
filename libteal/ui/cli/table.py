#!/usr/bin/env python3
#
# Outputs visually appealing tables in the terminal.
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


from .colorprint import cprint, get_width


class Row:
    def __init__(self):
        self.columns = []   # (text, style, align)
    #
    def add_column(self, text, style='default', align='left'):
        self.columns.append( (text, style, align) )
    #
    def render_column(self, number, width):
        if number < len(self.columns):
            text, style, align = self.columns[number]

            if len(text) > width:
                text = textwrap.shorten(text, width)
            #

            padding = max(width - len(text), 0)
            lpad = 0
            rpad = padding  # left alignment

            if align == 'right':
                lpad = padding
                rpad = 0
            elif align == 'center':
                lpad = padding // 2
                rpad = lpad
                if padding % 2 == 1:
                    # Odd width: put the extra space on the right
                    rpad += 1
            #####

            cprint(lpad * ' ', text, rpad * ' ', sep='', style=style, end='')
        #
    #
#


class Table:
    def __init__(self, separator_style='default'):
        self.get_width = get_width
        self.columns = []        # column number: { 'width': w, 'spacing': s, 'proportional': p }
        self.min_width = 0
        self.rows = []
        self.separator_style = separator_style
        self.propcount = 0
    #
    def add_column(self, width, spacing=1, proportional=True):
        self.columns.append({'width': width, 'spacing': spacing, 'proportional': proportional})
        self.min_width += width + spacing
        if proportional:
            self.propcount += 1
        #
    #
    def add_row(self):
        row = Row()
        self.rows.append(row)
        return row
    #
    def add_separator(self):
        self.rows.append('-')
    #
    def render(self):
        width = get_width()
        if self.propcount > 0 and width > self.min_width:
            avail = width - self.min_width
            add = avail // self.propcount
        #

        # Leave a blank line prior to the start of the table
        cprint()

        for row in self.rows:
            if row == '-':
                cprint(width * '\u2500', style=self.separator_style)
            else:
                index = 0
                for entry in self.columns:
                    cwidth = entry['width']
                    spacing = entry['spacing']

                    if entry['proportional']:
                        cwidth += add
                    #
                    row.render_column(index, cwidth)
                    cprint(' ' * spacing, sep='', end='')
                    index += 1
                #
                cprint()
        #####
    #
#
