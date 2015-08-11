import os
import atexit
import random
import socket
import threading
import flask
import twisted
import autobahn
import coverage
from coverage.files import TreeMatcher
from tracer import SimplePyTracer


class CoverageCollector:

    def __init__(self, ignore_paths=None):
        self.cov_files = []
        self.data = {}
        self.tracer = None
        self.trace_fun = None
        # check where are the libraries
        self.pylib_dirs = []
        self.started = False
        for m in (atexit, os, random, socket, flask, twisted, autobahn, coverage):
            if m is not None and hasattr(m, "__file__"):
                m_dir = self._get_dir(m)
                if m_dir not in self.pylib_dirs:
                    self.pylib_dirs.append(m_dir)

        if ignore_paths is not None:
            if type(ignore_paths) is str:
                if ignore_paths not in self.pylib_dirs:
                    self.pylib_dirs.append(ignore_paths)
            elif type(ignore_paths) is list:
                for p in ignore_paths:
                    if p not in self.pylib_dirs:
                        self.pylib_dirs.append(p)
            else:
                # what the hell is this?
                pass

        if self.pylib_dirs:
            self.pylib_match = TreeMatcher(self.pylib_dirs)

    def start_trace(self):
        self.started = True
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

    def _should_trace(self, filename):
        """
        Decide if we need to trace this file or not. We need to ignore python
        library files and package files, and only trace the game source files.
        :param filename: the name of the file
        :return: True or False
        """
        if not os.path.exists(filename):
            return False

        # then check if this is lib file
        if self.pylib_match and self.pylib_match.match(filename):
            return False

        print "++++++++++++trace this file ", filename
        # trace it.
        return True

    def _get_dir(self, module):
        if hasattr(module, '__file__'):
            filename = module.__file__
        else:
            filename = module
        filename = os.path.dirname(os.path.split(filename)[0])
        if filename.endswith('.egg'):
            filename = os.path.split(filename)[0]
        return filename

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
        if self.started:
            # RuntimeError: dictionary changed size during iteration?
            for filename in self.tracer.parse_cache.keys():
                item = self.tracer.parse_cache[filename]
                key = filename.replace('\\', '/')
                parser = item['parser']  # code parser
                code = item['code']  # a set of total code line number
                exec1 = self.data.get(filename) or {}  # a dict of code line number that executed
                executed = parser.first_lines(exec1)  # a set of code line number that executed
                missing = code - executed   # a set of code line number that missed execute
                if len(code) == 0:  # for some __init__.py, file is empty but also have 1 line code executed..Why?
                    cov = 1     # for that file, let's make it 100%
                else:
                    cov = float(len(executed)) / len(code)
                result[key] = {
                    'code': list(code),
                    'executed': list(executed),
                    'missed': list(missing),
                    'coverage': cov
                }
        return result

    def add_cov_file(self, cov_file):
        self.cov_files.append(cov_file)

    def clear(self):
        self.tracer.clear()

    def init_cov_files(self, files):
        self.cov_files = files

    def stop_trace(self):
        self.started = False
        self.tracer.stop()
        threading.settrace(None)


