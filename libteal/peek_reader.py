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


from io import IOBase, SEEK_SET, SEEK_CUR, SEEK_END
from os import pread


class PeekReader(IOBase):
    '''
    Implements a file-like object for reading the contents of files that are
    already opened in read-write mode (i.e. opened with the w+b flag). Such
    files include those produced by the tempfile module when using default
    settings. Unlike simply opening and reading the contents of the file
    from disk, the PeekReader reuses the file descriptor with the os.pread()
    method. Content that has been written to the file by another process
    or thread can be read without changing the write offset.
    '''
    def __init__(self, base_fh_or_fd, text=True):
        '''
        Constructor.

        base_fh_or_fd   --  File object or file descriptor
        text            --  Convert bytestrings to Unicode

        Note that, if a file-like object is passed for the base_fh_or_fd,
        this object MUST support the fileno() method and have a valid file
        descriptor. The "peek reading" is done using os.pread, which is a
        wrapper on pread(2) declared in the C unistd.h header.

        Optionally, the read(), readline(), and readlines() methods can
        return Unicode strings instead of bytestrings, if the text
        argument is True (the default).
        '''
        IOBase.__init__(self)

        self.fh = None
        self.fd = None
        self.is_closed = True
        self.text = text

        if type(base_fh_or_fd) is int:
            self.fd = base_fh_or_fd
            self.is_closed = False
        else:
            self.fh = base_fh_or_fd
            self.fd = self.fh.fileno()
            self.is_closed = False
        #

        # We have to maintain our own offset, since the underlying file is
        # potentially in use already for writing
        self.position = 0
    #
    def close(self):
        '''
        Closes the PeekReader, which prevents further reading of the file.
        This operation does NOT close the underlying file descriptor, since
        that may still be in use by the writer thread or process. The
        internal references to the file handle and/or descriptor are cleared,
        so as not to interfere with regular garbage collection of the
        actual file object used by the writer.
        '''
        self.is_closed = True
        self.fh = None
        self.fd = None
    #
    def fileno(self):
        '''
        Returns the file descriptor number to which this instance is bound,
        if any. If no instance is bound, returns None.
        '''
        return self.fd
    #
    def flush(self):
        '''
        Does nothing, since writing is not supported.
        '''
        pass
    #
    def isatty(self):
        '''
        Returns False, since the PeekReader does not implement a tty.
        '''
        return False
    #
    def readable(self):
        '''
        Returns True iff the PeekReader is open with a file descriptor set.
        Note that corner cases may arise (e.g. when attached to a file
        belonging to another process) in which reading is not actually
        possible.
        '''
        return not self.is_closed
    #
    def _read(self, size=65536):
        '''
        Reads at most size bytes from the file descriptor. This is the
        private implementation that returns a bytestring.
        '''
        if not self.is_closed:
            raw = pread(self.fd, size, self.position)
            self.position += len(raw)
        else:
            raise ValueError('Attempted to read from closed file')
        #
        return raw
    #
    def read(self, size=65536):
        '''
        Reads at most size (default 64K) bytes from the file descriptor.
        Returns a string if the text property of this object is True,
        otherwise returns a bytestring. Note that the length of the
        returned string is limited to the read size. For multibyte Unicode
        characters, the length of a translated string will be even shorter.
        '''
        raw = self._read(size)
        return str(raw, 'utf-8') if self.text else raw
    #
    def read_to(self, size=-1, sentinel=None):
        '''
        Reads data from the file until the specified number of bytes have
        been read, the first occurrence is encountered of a sentinel
        value, or the end of the file is reached.

        size      --  Maximum number of bytes to read (negative for unlimited)
        sentinel  --  Sentinel value at which to stop reading if encountered
        text      --  Override Unicode conversion if not None

        A negative value for size will read to the end of the file if no
        sentinel has been set. Note that the end of the file in this case
        means the end of the data that has been written by the writer
        process or thread.

        If a sentinel value is used as the stopping condition, the sentinel
        must be passed as a bytestring. Reading will continue until either
        the sentinel value is first seen or the size limit is reached. If
        encountered, the sentinel will be appended to the end of the returned
        string.

        This method returns a bytestring or a Unicode string depending on
        the text property of the PeekReader object.
        '''
        happy = False
        full = b''

        while not happy:
            rsize = 65536 if size < 0 else size
            chunk = self._read(rsize)

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

        return str(full, 'utf-8') if self.text else full
    #
    def readall(self):
        '''
        Reads and returns all the content of the underlying file. The
        return type is a Unicode or byte string, depending on the text
        property of the PeekReader object.
        '''
        self.seek(0)
        return self.read_to()
    #
    def readline(self, size=-1):
        '''
        Reads and returns one line from the underlying file. If size is
        nonnegative, at most size bytes will be read, even if a partial
        line results. The line separator is b'\\n'.
        '''
        return self.read_to(size=size, sentinel=b'\n')
    #
    def readlines(self, hint=-1):
        '''
        Reads and returns all lines in the underlying file, starting from
        the current offset. If hint is nonnegative, reads at most hint
        bytes, even if a partial last line results. The line separator
        depends upon the text processing mode of the PeekReader, since
        line separation occurs only after all the text has been read and
        optionally converted to Unicode.
        '''
        return self.read_to(size=hint).splitlines()
    #
    def seek(self, offset, whence=SEEK_SET):
        '''
        Changes the stream position to the given byte offset.

        offset   --  Byte offset to which to seek
        whence   --  Offset mode (SEEK_SET, SEEK_CUR, or SEEK_END)

        Note that the "end" of the file is the current writer position.
        This position can only be determined if the PeekReader was
        instantiated from a file object, so that the tell() method of that
        file object can be called. If the PeekReader was instantiated
        from a file descriptor, then SEEK_END behaves the same as SEEK_CUR,
        since the end location is unknown.
        '''
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
        '''
        Returns True if the file is not closed.
        '''
        return not self.is_closed
    #
    def tell(self):
        '''
        Returns the current position (byte offset) of the PeekReader. This
        position is independent of the offset of the writer thread or
        process.
        '''
        return self.position
    #
    def writable(self):
        '''
        Returns False. The PeekReader is for reading only, hence the name.
        '''
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
