#!/usr/bin/env python3
#
# Enhanced path objects and file testing operations.
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


import getpass
import grp
import os
import pathlib
import stat


READ = 4
WRITE = 2
EXECUTE = 1


class TealPosixPath(pathlib.PosixPath):
    '''
    Extended version of pathlib.PosixPath, which adds support for additional
    file tests that are not present in the base library version. Objects of
    this type can be used anywhere path-like objects are permitted in Python.
    '''
    def __init__(self, *pathsegments):
        '''
        Constructor.

        *pathsegments   --  Path segments used for initialization
        '''
        pathlib.PosixPath.__init__(*pathsegments)
    #
    def test_file_mode(self, permission):
        '''
        Tests file mode against the effective user and group IDs to determine
        whether or not the current process has the given permission on the
        path represented by this object.

        permission   --   One of: READ, WRITE, EXECUTE
        '''
        result = False

        # Begin by determining which bits in the file mode we need to check.
        u_const = stat.S_IRUSR
        g_const = stat.S_IRGRP
        o_const = stat.S_IROTH

        if permission == WRITE:
            u_const = stat.S_IWUSR
            g_const = stat.S_IWGRP
            o_const = stat.S_IWOTH
        elif permission == EXECUTE:
            u_const = stat.S_IXUSR
            g_const = stat.S_IXGRP
            o_const = stat.S_IXOTH
        elif permission != READ:
            raise OSError('Invalid permission type')
        #

        # Overall bitmask used for checking root execute permissions
        all_bits = u_const | g_const | o_const

        try:
            if self.exists():
                # Since the purpose of this library is to support an alternative to
                # writing shell scripts, follow the behavior of what most shells
                # would do, and check the effective user and group IDs. This differs
                # from the behavior of the access(2) system call.
                uid = os.geteuid()
                gid = os.getegid()

                s = self.stat()
                owner = s.st_uid
                group = s.st_gid
                mode = s.st_mode

                if uid == 0:
                    # Special rules exist for root
                    if permission in (READ, WRITE):
                        # root can read and write anything
                        result = True
                    else:
                        # If any execute permission bit is set, then root can execute
                        # the file as well
                        if mode & all_bits:
                            result = True
                        #
                    #
                else:
                    # Non-root uid
                    if owner == uid:
                        # If the current effective uid is the owner of the file, we
                        # only need to match the user permission bits.
                        if mode & u_const:
                            result = True
                        #
                    else:
                        # For groups, things are a little bit more complex. If our
                        # egid is the same as the file's gid, we have a case similar
                        # to user matching. However, we also need to check membership
                        # in supplemental groups.
                        group_matched = False
                        if group == gid:
                            group_matched = True
                            if mode & g_const:
                                result = True
                            #
                        else:
                            for grp in os.getgroups():
                                if group == grp:
                                    group_matched = True
                                    if mode & g_const:
                                        result = True
                                        break
                        #############

                        # If the file's group doesn't match any group with which the
                        # user is associated, check the "other" permissions
                        if not group_matched:
                            if mode & o_const:
                                result = True
            #################
        except PermissionError as e:
            pass   # just return False
        #

        return result
    #
    def is_executable(self):
        '''
        Returns True if this path exists and is executable by the current
        process.
        '''
        return self.test_file_mode(EXECUTE)
    #
    def is_readable(self):
        '''
        Returns True if this path exists and is readable by the current
        process.
        '''
        return self.test_file_mode(READ)
    #
    def is_writable(self):
        '''
        Returns True if this path exists and is writable by the current
        process.
        '''
        return self.test_file_mode(WRITE)
    #
#


def path(*pathsegments):
    '''
    Factory function for easy creation of a TealPosixPath object.

    *pathsegments   --  Initial path segments
    '''
    return TealPosixPath(*pathsegments)
#

def cwd():
    '''
    Factory function that creates a TealPosixPath pointing to the current
    working directory.
    '''
    return TealPosixPath.cwd()
#

def home():
    '''
    Factory function that creates a TealPosixPath pointing to the user's
    home directory. If the user's home directory cannot be determined, a
    RunTime error is raised.
    '''
    return TealPosixPath.home()
#


# Procedural Interface
#
# These functions provide convenient non-object-oriented ways to run various
# tests on paths, mirroring the code structure of shell scripts more closely.

def pwd():
    '''
    Returns a string representation of the current working directory.
    '''
    return str(TealPosixPath.cwd())
#

def glob(pattern, path=None):
    '''
    Returns a list of strings matching the pattern in a given path, or the
    current working directory if the path is None.

    pattern   --  Glob pattern (see the fnmatch module for syntax)
    path      --  Optional base path in which to perform the operation
    '''
    pathobj = None
    if result is None:
        pathobj = TealPosixPath.cwd()
    else:
        pathobj = TealPosixPath(path)
    #
    return [ str(item) for item in pathobj.glob(pattern) ]
#

def exists(path):
    '''
    Returns True if the given path exists.
    '''
    return TealPosixPath(path).exists()
#

def is_dir(path):
    '''
    Returns True if the given path is a directory.
    '''
    return TealPosixPath(path).is_dir()
#

def is_file(path):
    '''
    Returns True if the given path exists and is a regular file, following
    symbolic links to the destination.
    '''
    return TealPosixPath(path).is_file()
#

def is_mount(path):
    '''
    Returns True if the given path is a mount point, meaning that a different
    filesystem is mounted at the given path.
    '''
    return TealPosixPath(path).is_mount()
#

def is_symlink(path):
    '''
    Returns True if the given path is a symbolic link.
    '''
    return TealPosixPath(path).is_symlink()
#

def is_socket(path):
    '''
    Returns True if the given path is a Unix socket (follows symbolic links).
    '''
    return TealPosixPath(path).is_socket()
#

def is_fifo(path):
    '''
    Returns True if the given path is a FIFO (named pipe). Follows symbolic
    links.
    '''
    return TealPosixPath(path).is_fifo()
#

def is_block_device(path):
    '''
    Returns True if the given path is a block device (follows symbolic links).
    '''
    return TealPosixPath(path).is_block_device()
#

def is_char_device(path):
    '''
    Returns True if the given path is a character device (follows symbolic
    links).
    '''
    return TealPosixPath(path).is_char_device()
#

def is_readable(path):
    '''
    Returns True if the given path exists and is readable by the current
    effective user (follows symbolic links).
    '''
    return TealPosixPath(path).is_readable()
#

def is_writable(path):
    '''
    Returns True if the given path exists and is writable by the current
    effective user (follows symbolic links).
    '''
    return TealPosixPath(path).is_writable()
#

def is_executable(path):
    '''
    Returns True if the given path exists and is executable by the current
    effective user (follows symbolic links).
    '''
    return TealPosixPath(path).is_executable()
#


if __name__ == '__main__':
    import sys

    for entry in sys.argv[1:]:
        p = path(entry)
        print(entry)
        print('    Readable:  ', p.is_readable())
        print('    Writable:  ', p.is_writable())
        print('    Executable:', p.is_executable())
    #
#
