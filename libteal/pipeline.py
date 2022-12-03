#!/usr/bin/env python3
#
# Creates pipelines using subprocesses
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


import os
import shlex
import tempfile

from signal import SIGTERM, SIGKILL
from subprocess import Popen, DEVNULL, PIPE, STDOUT


PIPE_STDOUT = { 'stdout': PIPE, 'stderr': None, 'stream': 1 }
PIPE_STDERR = { 'stdout': None, 'stderr': PIPE, 'stream': 2 }
PIPE_BOTH = { 'stdout': PIPE, 'stderr': STDOUT, 'stream': 1 }
PIPE_STDOUT_QUIET = { 'stdout': PIPE, 'stderr': DEVNULL, 'stream': 1 }
PIPE_STDERR_QUIET = { 'stdout': DEVNULL, 'stderr': PIPE, 'stream': 2 }



class Command:
        '''
        Data structure for holding per-command information.
        '''
        command = []
        cwd = None
        environ = {}
        user = None
        group = None
        extra_groups = None
        umask = -1
        stdin = PIPE
        stdout = None
        stderr = None
        stream = 1
        subproc = None
#


class Pipeline:
    def __init__(self, cwd=None, base_env=None, export={},
                 stdout=None, stderr=None, indata=None, user=None,
                 group=None, extra_groups=None, umask=-1):
        '''
        Constructor for a new Pipeline object.

        cwd             --  Working directory for execution (pwd if None)
        base_env        --  Base environment (None for os.environ)
        export          --  Additional environment variables (dict)
        stdout          --  Standard output stream of last process
        stderr          --  Standard error stream of last process
        indata          --  Data to sent to first process
        user            --  Change user for each subprocess
        group           --  Change group for each subprocess
        extra_groups    --  Add extra groups to each subprocess
        umask           --  Set umask for each subprocess

        The stdout and stderr streams may be set to a file object, file
        descriptor, string containing a filename, or the special values
        None, PIPE, or DEVNULL. If set to None, then the stdout or stderr
        stream will be sent to Python's standard output or error, which
        is typically the console or terminal window. Setting these streams
        to PIPE causes the output to be captured in a temporary file,
        which can then be replayed to retrieve the results. DEVNULL redirects
        the stream to /dev/null and discards the contents. Additionally,
        the stderr stream can be set to STDOUT, which will multiplex the
        two streams together onto standard output.

        Each of the cwd, base_env, export, user, group, extra_groups, and
        umask keywords passed to the constructor set these values for each
        subprocess in the pipeline. Individual subprocess settings can be
        overridden in the append() method. The base_env specifies the base
        environment to use (os.environ if None), while export is a dictionary
        of additional environment variables to make available to each
        subprocess. The remainder of the keyword arguments are passed
        verbatim to the subprocess.Popen constructor and are documented
        there.
        '''

        self.cwd = cwd
        self.user = user
        self.group = group
        self.extra_groups = extra_groups
        self.umask = umask

        self.environ = dict(base_env) if base_env is not None else dict(os.environ)
        for key in export:
            self.environ[key] = export[key]
        #

        self.stdin = None
        if indata:
            self.stdin = tempfile.TemporaryFile()
            if type(indata) is str:
                self.stdin.write(bytes(indata, 'utf-8'))
            else:
                self.stdin.write(indata)
            #
            self.stdin.flush()
            self.stdin.seek(0)
        #

        self.stdout = stdout
        if stdout is PIPE:
            self.stdout = tempfile.TemporaryFile()
        elif type(stdout) is str:
            self.stdout = open(stdout, 'w+b')
        #

        self.stderr = stderr
        if stderr is PIPE:
            self.stderr = tempfile.TemporaryFile()
        elif type(stderr) is str:
            self.stderr = open(stderr, 'w+b')
        #

        self.commands = []
    #
    def append(self, command, cwd=None, base_env=None, export={}, user=None,
               group=None, extra_groups=None, umask=-1, pipe=PIPE_STDOUT):
        '''
        Appends a command to the pipeline.

        command            --  The command (as a sequence or str)
        cwd                --  Working directory for this command
        base_env           --  Base environment for this command
        export             --  Extra environment vars for this command
        user               --  Change user for this command
        group              --  Change group for this command
        extra_groups       --  Add extra groups for this command
        umask              --  Set umask for this command
        pipe               --  Relationship of this command to the next one

        The command can be specified as a sequence (typically a list) or as
        a str (in which case, it is split with shlex). The cwd, base_env,
        export, user, group, extra_groups, and umask all override the
        pipeline-level settings for this command. See the constructor help
        for more information.

        The pipe keyword defines the relationship between this command and
        the one that follows it. PIPE_STDOUT (the default) specifies that
        the standard output of this command will be piped to the standard
        input of the next command in the pipeline. Standard error will go
        to the pipeline default location. PIPE_STDERR pipes the standard
        error of this command to the next command in the pipeline, with
        standard output sent to the pipeline default location. PIPE_BOTH
        sends the combined standard output and standard error streams to
        the next command. PIPE_STDOUT_QUIET and PIPE_STDERR_QUIET pipe the
        standard output and error streams to the next command, respectively;
        however, the other stream is sent to DEVNULL and is suppressed.
        '''

        cmd = Command()
        if type(command) is str:
            cmd.command = shlex.split(command)
        else:
            cmd.command = command
        #

        cmd.cwd = self.cwd if cwd is None else cwd

        cmd.environ = dict(self.environ) if base_env is None else dict(base_env)
        for key in export:
            cmd.environ[key] = export[key]
        #

        cmd.user = self.user if user is None else user
        cmd.group = self.group if group is None else group
        cmd.extra_groups = self.extra_groups if extra_groups is None else extra_groups
        cmd.umask = self.umask if umask < 0 else umask

        cmd.stdout = pipe['stdout']
        cmd.stderr = pipe['stderr']
        cmd.stream = pipe['stream']

        self.commands.append(cmd)
    #
    def launch(self):
        if len(self.commands) > 0:
            self.commands[-1].stdout = self.stdout
            self.commands[-1].stderr = self.stderr

            index = 0
            prev_command = None
            stdin = self.stdin

            for item in self.commands:
                if prev_command:
                    if prev_command.stream == 2:
                        stdin = prev_command.subproc.stderr
                    else:
                        stdin = prev_command.subproc.stdout
                #####

                item.subproc = Popen(item.command, stdin=stdin,
                             stdout=item.stdout, stderr=item.stderr,
                             cwd=item.cwd, env=item.environ, user=item.user,
                             group=item.group, extra_groups=item.extra_groups,
                             umask=item.umask)
                #

                if prev_command:
                    if prev_command.stream == 2:
                        prev_command.subproc.stderr.close()
                    else:
                        prev_command.subproc.stdout.close()
                #####

                prev_command = item
            #
        #
    #
    def is_running(self):
        '''
        Returns True iff the pipeline is still running.
        '''
        result = False
        for item in self.commands:
            if item.subproc:
                if item.subproc.poll() is None:
                    result = True
                    break
        #########

        return result
    #
    def poll(self):
        '''
        Polls each subprocess in the pipeline. Returns a list with the
        same number of elements as there are subprocesses in the pipeline.
        Each element will contain None if the subprocess is still running,
        the return code if the subprocess has finished, or False if the
        subprocess has not yet been created.
        '''
        result = []
        for item in self.commands:
            if item.subproc:
                result.append(item.subproc.poll())
            else:
                result.append(False)
        #####

        return result
    #
    def wait(self, timeout=None):
        '''
        Waits for each subprocess to terminate. Returns a list with the
        same number of elements as there are subprocesses in the pipeline.
        Each element will contain the return code of the subprocess, or
        the value False if the subprocess has not yet been created. An
        optional timeout (in seconds) is available. A TimeoutExpired
        (from the subprocess module) exception is raised if it expires.
        '''
        result = []
        for item in self.commands:
            if item.subproc:
                result.append(item.subproc.wait(timeout))
            else:
                result.append(False)
        #####

        return result
    #
    def send_signal(self, signal):
        '''
        Sends the specified signal to each subprocess in the pipeline.
        '''
        for item in self.commands:
            if item.subproc:
                item.subproc.send_signal(signal)
    #########
    def terminate(self):
        '''
        Sends the SIGTERM signal to each subprocess in the pipeline.
        '''
        self.send_signal(SIGTERM)
    #
    def kill(self):
        '''
        Sends the SIGKILL signal to each subprocess in the pipeline.
        '''
        self.send_signal(SIGKILL)
    #
#


if __name__ == '__main__':
    p = Pipeline(stdout=PIPE, indata='Hello, World\n')
    p.append('cat')
    p.append('grep World')
    p.append('tr o 0')
    p.launch()
    p.wait()
    p.stdout.seek(0)
    print(p.stdout.read())
#
