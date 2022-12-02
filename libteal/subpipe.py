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
import threading
import time

from subprocess import Popen, DEVNULL, PIPE, STDOUT


PIPE_STDOUT = { 'stdout': PIPE, 'stderr': None, 'stream': 1 }
PIPE_STDERR = { 'stdout': None, 'stderr': PIPE, 'stream': 2 }
PIPE_BOTH = { 'stdout': PIPE, 'stderr': STDOUT, 'stream': 1 }
PIPE_STDOUT_QUIET = { 'stdout': PIPE, 'stderr': DEVNULL, 'stream': 1 }
PIPE_STDERR_QUIET = { 'stdout': DEVNULL, 'stderr': PIPE, 'stream': 2 }

SLEEP_TIME = 0.000001


class SubCommand:
    def __init__(self, command, stdout=PIPE, stderr=PIPE, cwd=None,
                 base_env=None, export=None, text=True, stream=0):
        '''
        Constructor.

        command    --  Command to execute (as sequence or str)
        stdout     --  Standard output stream (or None, PIPE, DEVNULL)
        stderr     --  Standard error stream (or None, PIPE, DEVNULL, STDOUT)
        cwd        --  Change working directory before execution
        base_env   --  Base environment (None to use default environment)
        export     --  Dict of additional environment variables for command
        text       --  Use text streams for command I/O
        stream     --  For pipelines, 1=stdout, 2=stderr of previous command
        '''

        self.command = command
        if type(command) is str:
            self.command = shlex.split(command)
        #

        self.stdout = stdout
        self.stderr = stderr

        self.cwd = cwd
        self.env = self._build_env(base_env, export)
        self.text = text
        self.stream = stream

        self.subproc = None
        self.thread = None
        self.output = None
        self.error = None
    #
    def _build_env(self, env, export):
        '''
        Helper function to build an environment from a base environment.

        env     --  Base environment
        export  --  Dict of extra variables to include in new environment

        If env is None, then os.environ is used as the base environment.
        '''
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

#


class PipeThread(threading.Thread):
    def __init__(self, pipeline):
        threading.Thread.__init__(self, name='pipeline')
        self.pipeline = pipeline
    #
    def run(self):
        '''
        Runs the pipeline inside the thread, transmitting any standard
        input data to the first process and collecting standard output and
        standard error data from the last process.
        '''
        stdin = self.pipeline.stdin
        comm_indata = None
        temp = None

        if self.pipeline.indata:
            if len(self.pipeline.commands) > 1:
                temp = tempfile.TemporaryFile()
                data = self.pipeline.indata
                if type(data) is str:
                    data = bytes(data, 'utf-8')
                #
                temp.write(data)
                temp.flush()
                temp.seek(0)
                stdin = temp
            else:
                # We don't need a temporary input file with only 1 process in
                # the pipeline, since the subprocess communicate method can
                # handle this situation
                comm_indata = self.pipeline.indata
            #
        #

        prev_command = None
        for item in self.pipeline.commands:
            stdout = item.stdout
            stderr = item.stderr

            if prev_command:
                if prev_command.stream == 2:
                    stdin = prev_command.subproc.stderr
                else:
                    stdin = prev_command.subproc.stdout
            #####

            item.subproc = Popen(item.command, stdin=stdin,
                             stdout=item.stdout, stderr=item.stderr,
                             cwd=item.cwd, env=item.env, text=item.text)
            #

            if prev_command:
                if prev_command.stream == 2:
                    prev_command.subproc.stderr.close()
                else:
                    prev_command.subproc.stdout.close()
            #####

            prev_command = item
        #

        self.pipeline.output, self.pipeline.error = \
            self.pipeline.commands[-1].subproc.communicate(comm_indata)
        #

        if temp:
            temp.close()
        #
    #
#


class Pipeline:
    def __init__(self, stdin=PIPE, indata=None, stdout=PIPE, stderr=PIPE,
                 cwd=None, base_env=None, export=None, text=True):
        '''
        Constructor.

        stdin     --  Standard input stream to first process
        indata    --  Data to sent to first process (if stdin=PIPE)
        stdout    --  Standard output stream of last process
        stderr    --  Standard error stream of last process
        cwd       --  Working directory for execution
        base_env  --  Base environment (None for os.environ)
        export    --  Additional environment variables (as dict)
        '''

        self.stdin = stdin
        self.indata = indata
        self.stdout = stdout
        self.stderr = stderr
        self.cwd = cwd
        self.base_env = base_env
        self.export = export
        self.text = text

        self.commands = []
        self.output = None
        self.error = None
        self.thread = None
    #
    def append(self, command, cwd=None, base_env=None, export=None, text=None,
               pipe=PIPE_STDOUT):
        '''
        Appends a command to the pipeline
        '''

        if cwd is None:
            cwd = self.cwd
        #

        if base_env is None:
            base_env = self.base_env
        #

        if export is None:
            export = self.export
        #

        if text is None:
            text = self.text
        #

        stdout = pipe['stdout']
        stderr = pipe['stderr']

        cmd = SubCommand(command, stdout, stderr, cwd, base_env, export, text)
        self.commands.append(cmd)
    #
    def launch(self):
        if len(self.commands) > 0:
            self.thread = PipeThread(self)
            self.thread.start()
        #
    #
    def is_running(self):
        '''
        Returns True iff the thread exists and is still running.
        '''
        result = False
        if self.thread:
            result = self.thread.is_alive()
        #

        return result
    #
    def wait(self, timeout=None):
        '''
        Waits for the thread and subcommand to terminate, then returns a
        3-tuple containing the exit code, standard output data, and standard
        error data. Uses busy waiting so that the threads can be interrupted
        if required by calling code. An optional timeout is available. If set,
        a TimeoutExpired exception is raised if the subcommand has not
        finished in timeout seconds.
        '''
        code = None
        start = time.time()
        while self.is_running():
            if timeout is not None:
                if (time.time() - start) >= timeout:
                    raise TimeoutExpired()
                #
            #

            if self.is_running():
                # Still running at the end of the timeout check, so yield
                # the CPU from the main thread
                time.sleep(SLEEP_TIME)
            #
        #

        if self.commands[-1].subproc:
            code = self.commands[-1].subproc.returncode
        #

        return (code, self.output, self.error)
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


def subpipe(*args, stdin=None, indata=None, stdout=PIPE, stderr=None,
               cwd=None, base_env=None, export=None, text=True):
    '''
    Runs a pipeline of external commands and waits for completion. Each
    external command may be specified as either a sequence of arguments or as
    a string to be split with shlex. Returns a 3-tuple consisting of the exit
    status, standard output data, and standard error data.

    stdin       --  Standard input stream to the first command
    indata      --  Data to send to the first command's standard input
    stdout      --  Standard output stream from the last command
    stderr      --  Standard error stream from the last command
    cwd         --  Working directory in which to run the commands
    base_env    --  Base set of environment variables
    export      --  Dictionary of additional environment variables
    text        --  Use text streams to/from the commands

    Note that sending indata to the pipeline sets stdin to PIPE. The stdin,
    stdout, and stderr streams can be set to a stream or file handle (as
    permitted by the subprocess module), or to the special values PIPE or
    DEVNULL. The stderr argument can be set to STDOUT to merge the error data
    onto the output stream. Capturing a stream is disabled by setting its
    corresponding argument to None. Capturing output and error data requires
    stdout and stderr to be set to PIPE, respectively.

    If base_env is None (the default), the os.environ (the environment seen
    by the Python interpreter) is used as the base environment. Otherwise,
    base_env must be set to a dictionary that will define the execution
    environment. Note that PATH must be set unless the absolute path to the
    command is given.

    Additional environment variables can be added to the base environment
    by passing a dictionary to the export argument. This dictionary maps
    environment variable names to values.
    '''
    if indata is not None:
        stdin = PIPE

        if text and type(indata) is bytes:
            indata = str(indata, 'utf-8')
        elif not text and type(indata) is str:
            indata = bytes(indata, 'utf-8')
        #
    #

    pipeline = Pipeline(stdin, indata, stdout, stderr, cwd, base_env, export,
                        text)
    for arg in args:
        pipeline.append(arg)
    #

    pipeline.launch()
    return pipeline.wait()
#


if __name__ == '__main__':
    print(subpipe('cat', indata='Hello, World\n'))
    print(subpipe('cat', 'grep World', 'tr o 0', indata='Hello, World\n'))
    print(subpipe('/usr/bin/env', export={'FOO': 'BAR'}))
#
