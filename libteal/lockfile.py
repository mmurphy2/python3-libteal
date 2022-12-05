#!/usr/bin/env python3
#
# PID-based locking code.
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

# TODO: improve the process checking features
# TODO: consider whether or not the race condition, however unlikely, can be
#       eliminated (perhaps fnctl.flock the lock file when acquiring)
# TODO: add error handling, in case we don't have permissions for the lock file

import os
import pathlib


class PIDLock:
    '''
    Implements a simple locking mechanism using the process ID of the current
    Python process. The intent of this lock is to prevent two copies of the
    same application or library from accessing the same resources, or to limit
    a program to a single instance.
    '''
    def __init__(self, lockfile):
        '''
        Constructor.

        lockfile   --  Path to the file that will be used for locking

        Ideally, lockfile should live on a tmpfs file system so that it is
        removed automatically if the system reboots.
        '''
        self.path = pathlib.PosixPath(lockfile)
    #
    def check_lock(self):
        '''
        Checks the lock file to determine if we can proceed to acquire the
        lock. Returns True if this process already holds the lock, or if no
        other process holds the lock, or if the lock file has become stale.
        Stale lock files are removed automatically.
        '''
        result = False
        if self.path.exists():
            this_pid = os.getpid()
            check_pid = 0
            with open(self.path, 'r') as fh:
                check_pid = int(fh.read().strip())
            #
            if this_pid == check_pid:
                # We already hold the lock
                result = True
            else:
                # See if we have a stale lock
                procpath = pathlib.PosixPath('/proc').joinpath(str(check_pid))
                if procpath.exists():
                    data = ''
                    with open(procpath.joinpath('status')) as fh:
                        data = fh.read()
                    #
                    if 'python' not in data:
                        # pid has been reused, so it should be safe to clean up the lock file
                        result = True
                        self.path.unlink(missing_ok=True)
                    #
                else:
                    # Stale lock: clean it up
                    result = True
                    self.path.unlink(missing_ok=True)
            #####
        else:
            # Not locked, so we're good to proceed
            result = True
        #
        return result
    #
    def lock(self):
        '''
        Acquires the PID lock by writing the current PID to the lock file. The
        lock is checked both before and after writing the lock file. There is
        still a tiny possibility for a race condition if two identical copies
        of this code run at the same time on different CPU cores.

        Returns True if we successfully wrote the lock file and then read the
        same PID back from it. A return value of False indicates a possible
        conflict with another process.
        '''
        result = False
        if self.check_lock():
            with open(self.path, 'w') as fh:
                pid = os.getpid()
                fh.write(str(pid) + '\n')
            #

            result = self.check_lock()
        #

        return result
    #
    def unlock(self):
        '''
        Checks to see if our PID is the one contained in the lock file. If it
        is, removes the lock file. Returns True if the lock file removal
        action is taken, False otherwise.
        '''
        result = False

        # Check that we're the process holding the lock
        if self.check_lock():
            self.path.unlink(missing_ok=True)
            result = True
        #

        return result
    #
#
