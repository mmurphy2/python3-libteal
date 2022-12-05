#!/usr/bin/env python3
#
# Implements various prompts for terminal-driven applications.
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


# TODO: need more prompt types. Also need to add colorprint support, once
#       that code has been refactored.

def prompt_yes_no(message, default=None):
    '''
    Asks the user a yes/no question and repeats until the user gives a valid
    answer. Returns True if the user picked the "yes" response or False if
    the user picked the "no" response.

    message    --  Message to display when prompting
    default    --  Default if Enter is pressed without typing anything

    If the default is None, the user must answer y/n (or yes/no). A default
    of True means the user can just press Enter for "yes", while a default
    of False means the user can just press Enter for "no".
    '''
    result = False
    ready = False

    yes = 'y'
    no = 'n'
    if default is not None:
        if default:
            yes = 'Y'
        else:
            no = 'N'
        #
    #

    while not ready:
        ask = input(message + ' [' + yes + '/' + no +'] ').lower()
        if ask in ('y', 'yes'):
            ready = True
            result = True
        elif ask in ('n', 'no'):
            ready = True
        elif default is not None and ask == '':
            result = default
            ready = True
        #
    #

    return result
#


if __name__ == '__main__':
    print(prompt_yes_no('Are you human?'))
    print(prompt_yes_no('Are you a robot?', default=False))
    print(prompt_yes_no('Are you carbon-based?', default=True))
#
