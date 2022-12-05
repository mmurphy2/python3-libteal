#!/usr/bin/env python3
#
# Conversions to and from human-readable sizes.
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


import math

IEC = {
    'Ki': 10,
    'Mi': 20,
    'Gi': 30,
    'Ti': 40,
    'Pi': 50,
    'Ei': 60,
    'Zi': 70,
    'Yi': 80,
}

SI = {
    'k': 3,
    'M': 6,
    'G': 9,
    'T': 12,
    'P': 15,
    'E': 18,
    'Z': 21,
    'Y': 24,
}

BYTES = 1
BITS = 8


class DataSize:
    def __init__(self, start_size=0):
        '''
        Constructor.

        start_size   --  Initial size (in Bytes)
        '''
        self.size = start_size
    #
    def parse_size(self, size_string):
        '''
        Parses a human-readable size string and sets the size of the current
        object to the result.

        size_string   --   size string to parse (e.g. 125.2 K)
        '''
        accumulator = ''
        dp = False
        prefix = ''
        unit = BYTES

        # Iterate through the string, accumulating digits and an optional
        # decimal point. Stop accumulating when non-digit, non-whitespace
        # characters are found, and use these to find the prefix.
        for char in size_string:
            if len(prefix) == 0:
                if char.isdigit():
                    accumulator += char
                elif len(accumulator) > 0:
                    if char == '.' and not dp:
                        dp = True
                        accumulator += char
                    elif not char.isspace():
                        prefix = char
                    #
                #
            else:
                if char.isalpha():
                    prefix += char
                else:
                    # Assume this is the end of the size
                    break
        #########

        # Check for Bytes/bits
        if len(prefix) > 0:
            if prefix[-1] == 'b':
                prefix = prefix[:-1]
                unit = BITS
            elif prefix[-1] in ('B', 'o'):
                # Bytes/octets
                prefix = prefix[:-1]
        #####

        # Special hack for a capital K: replace with Ki. In the early days of
        # computing, K (capitalized) unambiguously distinguished the power of
        # two value (modern Kibi) from its SI equivalent (kilo).
        if prefix == 'K':
            prefix = 'Ki'
        #

        self.size = 0
        if len(accumulator) > 0:
            self.size = float(accumulator)
        #

        if prefix in IEC:
            self.size *= 2**IEC[prefix]
        elif prefix in SI:
            self.size *= 10**SI[prefix]
        #

        self.size = int(self.size)

        # Workaround for fractional bits and bits that don't align with
        # byte boundaries:
        if unit == BITS:
            total = self.size // BITS
            if self.size % BITS != 0:
                total += 1
            #
            self.size = total
        #

        return self.size
    #
    def human_size(self, prefixes=IEC, places=2, unit=BYTES, force=None):
        '''
        Returns a human-friendly string representation of the size.

        prefixes  --  Prefixes to use (SI or IEC)
        places    --  Number of decimal places for rounding (-1 to disable)
        unit      --  Output in BYTES or BITS
        force     --  Force output to a given prefix

        When forcing output to a given prefix, the prefix must be valid
        in the specified prefixes table. To force bytes or bits, set force
        to an empty string.
        '''
        log = math.log10 if prefixes == SI else math.log2
        base = 10 if prefixes == SI else 2
        suffix = 'b' if unit == BITS else 'B'

        magnitude = 1
        if self.size > 0:
            magnitude = log(self.size)
        #
        dividend = 1
        prefix = ''

        if force is not None:
            if force == '':
                pass   # Use the defaults and output in base units
            elif force in prefixes:
                prefix = force
                dividend = base**prefixes[force]
            else:
                raise ValueError('No matching forced prefix found')
            #
        else:
            for entry in prefixes:
                if magnitude < prefixes[entry]:
                    break
                #
                prefix = entry
                dividend = base**prefixes[entry]
            #
        #

        friendly = ''
        if prefix == '' and unit == BITS:
            # There are no fractional bits, so output based on an int
            friendly = str(self.size * unit)
        elif places >= 0:
            friendly = str(round((self.size * unit) / dividend, places))
        else:
            friendly = str((self.size * unit) / dividend)
        #

        friendly += ' ' + prefix + suffix
        return friendly
    #
#


def human_size(size_in_bytes, prefixes=IEC, places=2, unit=BYTES, force=None):
    '''
    Returns a string containing a human-readable size expression

    prefixes  --  Prefixes to use (SI or IEC)
    places    --  Number of decimal places for rounding (-1 to disable)
    unit      --  Output in BYTES or BITS
    force     --  Force output to a given prefix (e.g. 'MiB')

    Note that a forced prefix must be present in the corresponding prefixes
    table, or a ValueError will be raised. Valid IEC prefixes are Ki, Mi,
    Gi, Ti, Pi, Ei, Zi, and Yi. Valid SI prefixes are k, M, G, T, P, E, Z,
    and Y. Note the SI prefix "kilo" uses a lowercase k! The IEC equivalent
    to uppercase K is Ki. Set force to an empty string to force base units.
    '''
    return DataSize(size_in_bytes).human_size(prefixes, places, unit)
#

def get_size(size_string):
    '''
    Returns the number of bytes represented by the given human size string.
    '''
    return DataSize().parse_size(size_string)
#


if __name__ == '__main__':
    d = DataSize()
    quit = False
    while not quit:
        exp = input('Enter a size expression (q to quit): ')
        if exp == 'q':
            quit = True
        else:
            d.parse_size(exp)
            print(d.size)
            print(d.human_size())
            print(d.human_size(force='Mi'))
            print(d.human_size(prefixes=SI, places=-1, unit=BITS))
            print(d.human_size(places=1, unit=BITS, force=''))
        #
    #
#
