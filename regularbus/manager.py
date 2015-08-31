import os
import atexit
import random
import socket
import sys
import flask
import twisted
import autobahn
import coverage
import threading
from coverage.files import TreeMatcher
from distutils import sysconfig
from pycoverage.collector import CoverageCollector
from pycallgraph.collector import CallStackCollector


def get_real_path(filename):
    """
    Get the real absolute path of the python source file
    :param filename: the name of the file, maybe a relative path
    :return: absolute path
    """
    if not filename.endswith(".py"):
        if filename[-4:-1] == ".py":
            filename = filename[:-1]
        elif filename.endswith("$py.class"):  # jython
            filename = filename[:-9] + ".py"

    if os.path.isabs(filename):
        return filename
    else:
        real_path = os.path.abspath(filename)
        if not os.path.exists(real_path):
            real_path = os.path.realpath(os.path.join(os.getcwd(), filename))
        else:
            real_path = os.path.realpath(real_path)
        return real_path


def get_dir(module):
    """
    Get the dir name of a python module
    :param module:
    :return:
    """
    if hasattr(module, '__file__'):
        filename = module.__file__
    else:
        filename = module
    filename = os.path.dirname(os.path.split(filename)[0])
    if filename.endswith('.egg'):
        filename = os.path.split(filename)[0]
    return filename


def get_pylib_matcher():
    """
    Get the python library paths matcher. Sometimes we have different pythons installed so be careful.
    :return: a python library matcher
    """
    pylib_dirs = set()
    for m in (atexit, os, random, socket, flask, twisted, autobahn, coverage):
        if m is not None and hasattr(m, "__file__"):
            m_dir = get_dir(m)
            pylib_dirs.add(m_dir)
    sys_lib = sysconfig.get_python_lib()
    pylib_dirs.add(sys_lib)
    return TreeMatcher(list(pylib_dirs))


class CollectorManager:
    def __init__(self):
        self.coverage_collector = CoverageCollector()
        self.call_graph_collector = CallStackCollector()
        # Cache the filename that should trace
        self.should_trace_cache = set()
        # Cache the filename that should not trace
        self.should_not_trace_cache = set()
        self.do_call_graph = False
        self.pylib_match = get_pylib_matcher()

    def harvest_coverage_data(self):
        cov_data = self.coverage_collector.harvest_data()
        return cov_data

    def harvest_call_graph_data(self):
        graph_data = self.call_graph_collector.harvest_data()
        return graph_data

    def harvest_graph(self):
        binary = self.call_graph_collector.draw_graph()
        return binary

    def clear_graph(self):
        self.call_graph_collector.reset()

    def trace(self, frame, event, arg_unused):
        """
        The main trace function, decide what we need to do for each function
        call or line execution.
        :param frame: the current stack frame
        :param event: event is a string: 'call', 'line', 'return', 'exception',
            'c_call', 'c_return', or 'c_exception'.
        :param arg_unused: we don't need this, however settrace need it.
        :return: return a reference to a local trace function to be used that
            scope, which means we need to return the trace function itself.
        """
        # Be careful that the filename can be a relative path name, such as ../logic/file1.py
        cur_file_path = frame.f_code.co_filename
        line_no = frame.f_lineno

        if cur_file_path in self.should_not_trace_cache:
            return self.trace

        real_file_path = get_real_path(cur_file_path)

        if real_file_path in self.should_trace_cache:
            self.coverage_collector.collect(real_file_path, line_no)
            if self.do_call_graph:
                self.call_graph_collector.collect(frame, event)
        else:
            if not cur_file_path:
                print "-" * 20, "empty file name, ignore trace ", cur_file_path
                self.should_not_trace_cache.add(cur_file_path)
                return self.trace

            elif cur_file_path.startswith('<'):
                # something like <string>, <module>
                print "-" * 20, "invalid filename, ignore trace ", cur_file_path
                self.should_not_trace_cache.add(cur_file_path)
                return self.trace

            elif not cur_file_path.endswith(".py") and not cur_file_path.endswith(
                    ".pyc") and not cur_file_path.endswith(
                    "$py.class"):
                print "-" * 20, "not a python source file, ignore trace ", cur_file_path
                self.should_not_trace_cache.add(cur_file_path)
                return self.trace

            elif not os.path.exists(real_file_path):
                # sometimes we only have .pyc file and doesn't have .py source file.
                print "-" * 20, "source file doesn't exists, ignore trace ", real_file_path
                self.should_not_trace_cache.add(cur_file_path)
                return self.trace

            # then check if this is lib file
            elif self.pylib_match and self.pylib_match.match(real_file_path):
                print "-" * 20, "library file, ignore trace ", real_file_path
                self.should_not_trace_cache.add(cur_file_path)
                return self.trace

            else:
                print "+" * 20, "trace this file ", real_file_path
                self.should_trace_cache.add(cur_file_path)
                self.coverage_collector.collect(real_file_path, line_no)
                if self.do_call_graph:
                    self.call_graph_collector.collect(frame, event)

        return self.trace

    def start_trace(self):
        self.do_call_graph = False
        sys.settrace(self.trace)
        threading.settrace(self.trace)
