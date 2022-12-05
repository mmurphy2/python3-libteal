#!/usr/bin/env python3
#
# Parses a human string expression of time to obtain seconds.
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

LEAPYEAR = 31622400
YEAR = 31536000
MONTH = 2592000
FORTNIGHT = 1209600
WEEK = 604800
WORKWEEK = 432000
DAY = 86400
HOUR = 3600
MINUTE = 60
SECOND = 1


DEFAULT_UNIT_MAP = {
    'leapyear': LEAPYEAR,
    'leapyears': LEAPYEAR,
    'l': LEAPYEAR,
    'year': YEAR,
    'years': YEAR,
    'y': YEAR,
    'month': MONTH,
    'months': MONTH,
    'b': MONTH,
    'fortnight': FORTNIGHT,
    'fortnights': FORTNIGHT,
    'f': FORTNIGHT,
    'week': WEEK,
    'weeks': WEEK,
    'w': WEEK,
    'workweek': WORKWEEK,
    'workweeks': WORKWEEK,
    'o': WORKWEEK,
    'day': DAY,
    'days': DAY,
    'd': DAY,
    'hour': HOUR,
    'hours': HOUR,
    'h': HOUR,
    'minute': MINUTE,
    'minutes': MINUTE,
    'm': MINUTE,
    'second': SECOND,
    'seconds': SECOND,
    's': SECOND,
}

COLONS = [ DAY, HOUR, MINUTE, SECOND ]


class TimeParser:
    def __init__(self):
        self.unit_map = dict(DEFAULT_UNIT_MAP)
        self.colons = list(COLONS)
    #
    def resolve_unit(self, unit):
        '''
        Resolves a supported time unit to the corresponding number of seconds.
        Raises a ValueError if the time unit is invalid.
        '''
        result = None
        if unit in self.unit_map:
            result = self.unit_map[unit]
        else:
            raise ValueError('Unknown time unit: ' + unit)
        #

        return result
    #
    def get_seconds(self, timestr):
        '''
        Returns the total number of seconds represented by the given time string.
        Raises a ValueError if the time string is invalid. Valid components of
        time strings are decimal digits (0-9), whitespace, or time unit values.
        A single decimal point may be present between groups of decimal digits.

        Supported time units are as follows:

        Long             Char      Meaning
        ---------------------------------------------------
        leapyear         l         366 days
        year             y         365 days
        month            b          30 days
        fortnight        f          14 days
        week             w           7 days
        workweek         o           5 days
        day              d          24 hours
        hour             h          60 minutes
        minute           m          60 seconds
        second           s         base unit

        An alternate supported format is a colon-separated value, where the
        form is days:hours:minutes:seconds, with days, hours, and minutes (and
        their corresponding colons) optional. A mixed format is also possible,
        although caution is advised since expressions can become difficult to
        understand and may yield unexpected results. For example, "5:12:05:02 1d"
        is really 6 days, 12 hours, 5 minutes, and 2 seconds.

        In both formats, whitespace separates quantities that should be added
        together. Thus, the expression "4 4" yields 8 seconds. It is recommended
        that users list units after each numeric value to make inputs clear.

        A numeric value without a time unit implies seconds.

        timestr   --   input time string
        '''
        total = 0
        accumulator = ''
        value = 0
        unit_mode = False
        space_mode = False

        total_colons = timestr.count(':')
        if total_colons > len(self.colons):
            raise ValueError('Time strings may have a maximum of ' + str(len(self.colons)) + ' colons')
        #

        colon = len(self.colons) - total_colons - 1
        for char in timestr.lower():
            if not unit_mode:
                if char.isdigit() or char == '.':
                    if space_mode and len(accumulator) > 0:
                        total += float(accumulator)
                        value = 0
                        accumulator = char
                        space_mode = False
                    else:
                        accumulator += char
                    #
                else:
                    if len(accumulator) > 0:
                        value = float(accumulator)
                    #

                    if char == ':':
                        total += value * self.colons[colon]
                        colon += 1
                        value = 0
                        accumulator = ''
                        space_mode = False
                    elif char.isspace():
                        space_mode = True
                    else:
                        accumulator = char
                        space_mode = False
                        unit_mode = True
                #####
            else:
                if char.isalpha():
                    accumulator += char
                else:
                    unit = self.resolve_unit(accumulator)
                    total += value * unit
                    value = 0
                    unit_mode = False
                    if char.isdigit():
                        accumulator = char
                    #
                    else:
                        accumulator = ''
                    #
        #############

        if unit_mode:
            # Ended on a unit or potential unit
            unit = self.resolve_unit(accumulator)
            total += value * unit
        else:
            # Any number left in the accumulator is treated as seconds
            if len(accumulator) > 0:
                total += float(accumulator)
        #####

        return total
    #
    def add_unit(self, unit_name, unit_spec):
        '''
        Adds a custom time unit to the TimeParser. This unit can be defined
        in terms of existing (or default) time units.

        unit_name   --  Name of the new time unit
        unit_spec   --  Specification of the new time unit

        The unit_spec is parsed with get_seconds() to resolve it to a
        representative number of seconds. Note that it is a good idea
        to add both the singular and plural forms of custom units, since
        users are not necessarily consistent in their usage.

        If the unit_name already exists in the TimeParser, calling this
        method overrides the unit_name with a new definition for the unit.
        '''
        seconds = self.get_seconds(unit_spec)
        self.unit_map[unit_name] = seconds
    #
    def del_unit(self, unit_name):
        '''
        Removes a unit from the TimeParser.

        unit_name   --  Name of the unit to remove
        '''
        del self.unit_map[unit_name]
    #
#


if __name__ == '__main__':
    p = TimeParser()
    p.add_unit('test', '2 weeks')
    run = True
    while run:
        timestr = input('Enter time string (q to quit): ')
        if timestr == 'q':
            run = False
        else:
            try:
                value = p.get_seconds(timestr)
                print(value)
            except Exception as e:
                print(e)
#############
