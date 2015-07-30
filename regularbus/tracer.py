from coverage.parser import CodeParser
import sys
import os


def _get_real_path(filename):

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


class SimplePyTracer:

    def __init__(self):
        # This is a function, decide if we need to trace a file
        self.should_trace = None
        # This is a dictionary, cache the filename that should trace
        self.should_trace_cache = {}
        # This is a dictionary, cache the filename that should not trace
        self.should_not_trace_cache = {}
        # The coverage data
        self.data = {}
        # File parser cache, cache normal file lines.
        self.parse_cache = {}

    def _init_trace_file(self, filename, lineno):
        """
        here comes a new file that need to trace
        :param filename: the name of the file
        :param lineno: first called line number
        :return: None
        """
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
        # filename can be a relative path name
        filename = frame.f_code.co_filename
        line_no = frame.f_lineno

        if filename in self.should_not_trace_cache:
            return self._trace
        filename = _get_real_path(filename)
        if filename in self.should_trace_cache:
            self.data[filename][line_no] = None
            return self._trace
        else:
            if not filename:
                print "empty filename, ignore trace ", filename
                return self._trace
            if filename.startswith('<'):
                print "invalid filename, ignore trace ", filename
                self.should_not_trace_cache[filename] = None
                return self._trace
            if not filename.endswith(".py") and not filename.endswith(".pyc") and not filename.endswith("$py.class"):
                print "not a python source file, ignore trace ", filename
                self.should_not_trace_cache[filename] = None
                return self._trace

            trace_it = self.should_trace(filename)
            if trace_it:
                self.should_trace_cache[filename] = None
                self._init_trace_file(filename, line_no)
            else:
                self.should_not_trace_cache[filename] = None

        return self._trace

    def start(self):
        sys.settrace(self._trace)
        return self._trace
