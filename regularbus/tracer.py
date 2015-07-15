from coverage.parser import CodeParser
import os
import sys

class SimplePyTracer:

    def __init__(self):
        self.should_trace_cache = {}
        self.should_not_trace_cache = {}
        self.data = {}
        self.parse_cache = {}

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

        # something like .pyc
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

        # then check if this is lib file

        return None

    def _init_trace_file(self, filename, lineno):
        if filename not in self.data:
            self.data[filename] = {}
        self.data[filename][lineno] = None
        if filename not in self.parse_cache:
            parser = CodeParser(filename=filename)
            statements, _ = parser.parse_source()
            self.parse_cache[filename] = {
                'parser': parser,
                'code': statements
            }

    def _trace(self, frame, event, arg_unused):
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
        filename = frame.f_code.co_filename
        line_no = frame.f_lineno
        if event == "call":
            if filename in self.should_not_trace_cache:
                return self._trace

            if filename not in self.should_trace_cache:
                trace_it = self._should_trace(filename, frame)
                if trace_it:
                    self.should_trace_cache[filename] = None
                    # we need to trace it
                    self._init_trace_file(filename, line_no)
                else:
                    self.should_not_trace_cache[filename] = None
            else:
                # we need to trace it.
                self.data[filename][line_no] = None

        if event == 'line':
            if filename in self.should_trace_cache:
                self.data[filename][frame.f_lineno] = None

        return self._trace

    def _harvest_data(self):
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
        for filename, item in self.parse_cache.iteritems():
            parser = item['parser']
            code = item['code']
            exec1 = self.data.get(filename) or {}
            executed = parser.first_lines(exec1)
            missing = code - executed
            result[filename] = {
                'code': list(code),
                'executed': list(executed),
                'missed': list(missing),
                'coverage': float(len(executed)) / len(code)
            }
        return result


