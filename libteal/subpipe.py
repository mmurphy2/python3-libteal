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
import subprocess
import tempfile
import time


PIPE_STDOUT = { 'stdout': subprocess.PIPE, 'stderr': None, 'stream': 1 }
PIPE_STDERR = { 'stdout': None, 'stderr': subprocess.PIPE, 'stream': 2 }
PIPE_BOTH = { 'stdout': subprocess.PIPE, 'stderr': subprocess.STDOUT,
             'stream': 1 }
PIPE_STDOUT_QUIET = { 'stdout': subprocess.PIPE, 'stderr': subprocess.DEVNULL,
                     'stream': 1 }
PIPE_STDERR_QUIET = { 'stdout': subprocess.DEVNULL, 'stderr': subprocess.PIPE,
                     'stream': 2 }


class Command:
    def __init__(self, command, cwd=None, env=None, text=None,
                 pipe=PIPE_STDOUT):
        '''
        Constructor
        '''

        self.command = command
        if type(command) is str:
            self.command = shlex.split(command)
        #

        self.cwd = cwd
        self.env = env
        self.text = text

        self.stdin = None
        self.stdout = pipe['stdout']
        self.stderr = pipe['stderr']
        self.stream = pipe['stream']

        self.subproc = None
        self.stream = None
    #
#


class Pipeline:
    def __init__(self, stdin=None, stdin_text=False, stderr=None, cwd=None,
                 env=None, export=None, text=True):
        '''
        Constructor
        '''

        self.pipe_stdin = pipe_stdin
        if stdin_text:
            self.pipe_stdin = tempfile.TemporaryFile()
            self.pipe_stdin.write(pipe_stdin)
            self.pipe_stdin.flush()
        #
        self.pipe_stderr = stderr
        self.pipe_cwd = cwd
        self.pipe_env = env
        self.pipe_export = export
        self.pipe_text = text

        self.commands = []
    #
    def _build_env(self, env, export):
        out_env = {}
        if env is None:
            for ev in os.environ:
                out_env[ev] = os.environ[ev]
            #
        else:
            for ev in env:
                out_env[ev] = env[ev]
            #
        #

        if export is not None:
            for ev in export:
                out_env[ev] = export[ev]
            #
        #

        return out_env
    #
    def append(self, command, cwd=None, env=None, export=None, text=None,
               pipe=PIPE_STDOUT):
        '''
        Appends a command to the pipeline
        '''

        if cwd is None:
            cwd = self.pipe_cwd
        #

        if text is None:
            text = self.pipe_text
        #

        cmd = Command(command, cwd, self._build_env(env, export), text, pipe)
        self.commands.append(cmd)
    #
    def launch(self):
        if len(self.commands) > 0:
            self.commands[0].stdin = self.pipe_stdin
            self.commands[-1].stdout = subprocess.PIPE
            self.commands[-1].stderr = self.pipe_stderr
            prev_command = None

            for command in self.commands:
                stdin = command.stdin
                if prev_command:
                    if prev_command.stream == 2:
                        stdin = prev_command.subproc.stderr
                    else:
                        stdin = prev_command.subproc.stdout
                    #
                #

                command.subproc = subprocess.Popen(command.command,
                                        stdin=stdin, stdout=command.stdout,
                                        stderr=command.stderr,
                                        cwd=command.cwd, env=command.env,
                                        text=command.text)

                if prev_command:
                    if prev_command.stream == 2:
                        prev_command.subproc.stderr.close()
                    else:
                        prev_command.subproc.stdout.close()
                    #
                #
            #
        #
    #
    def poll(self):
        code = None
        for command in self.commands:
            if command.subproc:
                this_code = command.subproc.poll()
                if this_code is not None:
                    if code is None:
                        code = this_code
                    else:
                        if code == 0:
                            code = this_code
        #################
        return code
    #
    def wait(self, timeout=None):
        total = 0
        result = self.poll()
        while result is None:
            time.sleep(0.1)
            total += 0.1

            result = self.poll()
            if result is None and timeout is not None:
                if total >= timeout:
                    raise subprocess.TimeoutExpired()
                #
            #
        #

        return result
    #
    def send_signal(self, signal):
        for command in self.commands:
            if command.subproc:
                command.subproc.send_signal(signal)
    #########
    def terminate(self):
        for command in self.commands:
            if command.subproc:
                command.subproc.terminate()
    #########
    def kill(self):
        for command in self.commands:
            if command.subproc:
                command.subproc.kill()
    #########
#


def subpipe(*args, stdin=None, stdin_text=False, stderr=None, cwd=None,
            env=None, export=None, text=True):
    '''
    Creates a pipeline of subprocesses and returns a Pipeline object.

    Each non-keyword argument to this function consists of a str, list, or
    dict. A str or list argument specifies a command with default pipeline
    attributes, while a dict is used whenever it is necessary to fine-tune
    a single process in the pipeline.
    '''
    pass
#


if __name__ == '__main__':
    # TODO unit test code
    pass
#
