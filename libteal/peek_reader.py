#!/usr/bin/env python3
#
# Implements a file-like overlay object for reading the current contents of
# a read-write file that is already open.
#
# Copyright (c) 2022 Coastal Carolina University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


# TODO: docstrings


from io import IOBase, SEEK_SET, SEEK_CUR, SEEK_END
from os import pread


class PeekReader(IOBase):
    def __init__(self, base_fh_or_fd):
        IOBase.__init__(self)
        self.fh = None
        self.fd = None
        self.is_closed = True
        if type(base_fh_or_fd) is int:
            self.fd = base_fh_or_fd
            self.is_closed = False
        else:
            self.fh = base_fh_or_fd
            self.fd = self.fh.fileno()
            self.is_closed = False
        #
        self.position = 0
    #
    def close(self):
        self.is_closed = True
    #
    def fileno(self):
        return self.fd
    #
    def flush(self):
        pass
    #
    def isatty(self):
        return False
    #
    def readable(self):
        return not self.is_closed
    #
    def read(self, size=65536):
        if not self.is_closed:
            raw = pread(self.fd, size, self.position)
            self.position += len(raw)
        else:
            raise ValueError('Attempted to read from closed file')
        #
        return raw
    #
    def read_to(self, size=-1, sentinel=None):
        happy = False
        full = b''

        while not happy:
            rsize = 65536 if size < 0 else size
            chunk = self.read(rsize)

            if len(chunk) == 0:
                # At EOF: nothing to do
                happy = True
            elif sentinel is not None and sentinel in chunk:
                parts = chunk.partition(sentinel)
                full += parts[0] + sentinel
                self.position -= len(parts[2])
                happy = True
            else:
                if size > 0:
                    size -= len(chunk)
                #
                full += chunk
            #
        #

        return full
    #
    def readline(self, size=-1):
        return str(self.read_to(size=size, sentinel=b'\n'), 'utf-8')
    #
    def readlines(self, hint=-1):
        return str(self.read_to(size=hint), 'utf-8').splitlines()
    #
    def seek(self, offset, whence=SEEK_SET):
        if whence == SEEK_CUR:
            self.position = self.position + offset
        elif whence == SEEK_END:
            if self.fh:
                self.position = self.fh.tell() + offset
            else:
                self.position = self.position + offset
            #
        else:
            # SEEK_SET
            self.position = offset
        #
    #
    def seekable(self):
        return not self.is_closed
    #
    def tell(self):
        return self.position
    #
    def writable(self):
        return False
    #
#


if __name__ == '__main__':
    import tempfile

    tf = tempfile.TemporaryFile()
    tf.write(b'Hello\nWorld\n1234\n')
    tf.flush()

    p = PeekReader(tf)
    print(p.read())
    p.seek(0)
    print(p.readline(), end='')
    print(p.tell())
    p.seek(0)
    print(p.readlines())

    p.close()
    tf.close()
#
