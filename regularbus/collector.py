import os
import sys
import atexit
import random
import socket
import threading
from tracer import SimplePyTracer
from coverage.files import FileLocator, TreeMatcher
from coverage.codeunit import CodeUnit

# Pypy has some unusual stuff in the "stdlib".  Consider those locations
# when deciding where the stdlib is.
try:
    import _structseq       # pylint: disable=F0401
except ImportError:
    _structseq = None

class CoverageCollector:

    def __init__(self):
        self.data = {}
        self.tracer = None
        self.trace_fun = None
        self.file_locator = FileLocator()
        # check where are the libraries
        self.pylib_dirs = []
        for m in (atexit, os, random, socket):
            if m is not None and hasattr(m, "__file__"):
                m_dir = self._get_dir(m)
                if m_dir not in self.pylib_dirs:
                    self.pylib_dirs.append(m_dir)
        # avoid tracing the package itself
        self.cover_dir = self._get_dir(__file__)

        if self.cover_dir:
            self.cover_match = TreeMatcher([self.cover_dir])

        if self.pylib_dirs:
            self.pylib_match = TreeMatcher(self.pylib_dirs)

    def start(self):
        self._start()
        threading.settrace(self._thread_trace)

    def _thread_trace(self, frame, event, arg):
        if self.trace_fun is None:
            self.trace_fun = self._start()
        return self.trace_fun(frame, event, arg)

    def _start(self):
        self.tracer = SimplePyTracer()
        self.tracer.data = self.data
        self.tracer.should_trace = self._should_trace
        self.trace_fun = self.tracer.start()
        return self.trace_fun

    def _should_trace(self, filename, frame):
        """
        Decide if we need to trace this file or not. We need to ignore python
        library files and package files, and only trace the game source files.
        :param filename: the name of the file
        :return: True or False
        """
        # empty filename shouldn't be traced.
        if not filename:
            return False

        # something like <string>
        if filename.startswith('<'):
            return False

        # ignore none python file, such as html
        if not filename.endswith(".py") and not filename.endswith(".pyc") and not filename.endswith("$py.class"):
            return False

        # change file name like .pyc
        if not filename.endswith(".py"):
            if filename[-4:-1] == ".py":
                filename = filename[:-1]
            elif filename.endswith("$py.class"):  # jython
                filename = filename[:-9] + ".py"

        # if the filename is not an absolute path
        if not os.path.isabs(filename):
            for path in [os.curdir] + sys.path:
                if path is None:
                    continue
                f = os.path.join(path, filename)
                if os.path.exists(f):
                    filename = f
                    break
        filename = self.file_locator.canonical_filename(filename)
        # then check if this is lib file
        if self.pylib_match and self.pylib_match.match(filename):
            return False
        # then check if this is the coverage package source
        if 0:
            if self.cover_match and self.cover_match.match(filename):
                return False
        # trace it.
        return True

    def _get_dir(self, module):
        return os.path.split(CodeUnit(module, self.file_locator).filename)[0]

    def harvest_data(self):
        """
        Harvest all the trace data we collected.
        :return:
        {
            "filename1.py": {
                code: [1, 2, 4, 5, 7, 8]
                executed: [2, 5, 8],
                missed: [1, 4, 7]
                coverage: 0.375
            },
            "filename2.py": {
                code: [..]
                executed: [..],
                missed: [1, 2, 3, ...]
                coverage: 0.8
            }
        }
        """
        result = {}
        keys = self.tracer.parse_cache.keys()
        for filename in keys:
            # replace windows \\ path separator
            item = self.tracer.parse_cache[filename]
            key = filename.replace('\\', '/')
            parser = item['parser']
            code = item['code']
            exec1 = self.data.get(filename) or {}
            executed = parser.first_lines(exec1)
            missing = code - executed
            result[key] = {
                'code': list(code),
                'executed': list(executed),
                'missed': list(missing),
                'coverage': float(len(executed)) / len(code)
            }
        return result
