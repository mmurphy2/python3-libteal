#!/usr/bin/env python3
#
# Implements a text-based progress bar in the terminal.
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

# TODO: migrate into libteal (needs refactoring)
# TODO: make the progress bar variable width
# TODO: adjust progress bar character


from .colorprint import cprint, get_width


class ProgressBar:
    '''
    Implements a console-based progress bar, which takes the form of either a
    spinner or a 20-segment text bar.

    label    --   label to display before the progress information
    quiet    --   suppresses all output if True
    '''
    def __init__(self, label='', quiet=False, spinner_style='spinner', progress_style='progress', \
                 percent_style='percent', label_style='label', success_style='success', \
                 error_style='error'):
        '''
        Constructor.

        label   --  label to display to the left of the progress bar (may be truncated
                    if necessary)
        '''
        self.spinner = ('-', '\\', '|', '/')
        self.spindex = 0
        self.label = label
        self.quiet = quiet
        self.spinner_style = spinner_style
        self.progress_style = progress_style
        self.percent_style = percent_style
        self.label_style = label_style
        self.success_style = success_style
        self.error_style = error_style
    #
    def print_spin(self):
        '''
        Displays the spinner, which is used when the total is not known.
        '''
        if not self.quiet:
            cprint(self.spinner[self.spindex], style=self.spinner_style, end='')
            self.spindex = (self.spindex + 1) % len(self.spinner)
        #
    #
    def print_bar(self, progress, total):
        '''
        Displays the progress bar, which is a 20-segment text bar in the form [===>       ].

        progress    --  progress thus far (as a raw number)
        total       --  final number to be reached when progress is 100%
        '''
        if not self.quiet:
            pct = 0
            if total > 0:
                pct = int(round(progress / total, 2) * 100)
            #
            steps = pct // 5
            blanks = min(20 - steps, 19)
            eqs = max(steps - 1, 0)
            cprint('[', eqs * '=', '>', blanks * ' ', ']', style=self.progress_style, sep='', end=' ')
        #
    #
    def print_percent(self, progress, total):
        '''
        Displays a percentage of total progress.

        progress    --  numerical value indicating progress thus far
        total       --  numerical value indicating the progress value at 100%
        '''
        if not self.quiet:
            if total == 0:
                cprint('----', end='')
            else:
                pct = int(round(progress / total, 2) * 100)
                if pct < 100:
                    cprint(end=' ')
                #
                cprint(pct, '%', style=self.percent_style, sep='', end='')
            #
        #
    #
    def print_label(self):
        '''
        Displays the label, followed by enough spaces to put the progress bar and
        percentage output on the right side of the screen. The label may be truncated
        to fit.
        '''
        if not self.quiet:
            width = get_width()
            avail_space = width - 29
            text = self.label[0:avail_space]
            padding = (avail_space - len(text)) * ' '
            cprint(text, padding, style=self.label_style, sep='', end=' ')
        #
    #
    def print_progress(self, progress, total):
        '''
        Displays current progress. If total is 0, progress is displayed as a spinner.
        Otherwise, progress is displayed using a 20-segment text progress bar, followed
        by the actual percentage. The progress display is preceeded by a label, and a
        carriage return is sent to the terminal at the end of the line, so that the
        next update overwrites the current one.

        progress   --   progress thus far (as a numerical value, such as the number of
                        bytes transferred)
        total      --   total number of units (e.g. bytes to be transferred) for the job
        '''
        if not self.quiet:
            self.print_label()
            if total == 0:
                self.print_spin()
            else:
                self.print_bar(progress, total)
                self.print_percent(progress, total)
            #
            cprint('\r', end='')
        #
    #
    def print_complete(self, message='Done', success=True, on_success='Complete', on_failure='Failed'):
        '''
        Displays a completed operation message, with a success or failure condition.
        This display consists of the label, a custom message, the success or failure
        word, followed by a newline.

        message     --  text of the message to display
        success     --  True iff the operation was successful
        on_success  --  word to use for a successful operation
        on_failure  --  word to use for a failed operation
        '''
        if not self.quiet:
            self.print_label()
            if success:
                spacing = max(26 - len(on_success) - len(message), 0) * ' '
                cprint(on_success, spacing, message, style=self.success_style)
            else:
                spacing = max(26 - len(on_failure) - len(message), 0) * ' '
                cprint(on_failure, spacing, message, style=self.error_style)
            #
        #
    #
#
