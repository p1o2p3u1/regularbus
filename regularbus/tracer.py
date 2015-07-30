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
        cur_file_path = frame.f_code.co_filename
        line_no = frame.f_lineno

        if cur_file_path in self.should_not_trace_cache:
            return self._trace

        real_file_path = _get_real_path(cur_file_path)

        if real_file_path in self.should_trace_cache:
            self.data[real_file_path][line_no] = None
        else:
            if not cur_file_path:
                return self._trace
            if cur_file_path.startswith('<'):
                self.should_not_trace_cache[cur_file_path] = None
                return self._trace
            if not cur_file_path.endswith(".py") and not cur_file_path.endswith(".pyc") and not cur_file_path.endswith(
                    "$py.class"):
                self.should_not_trace_cache[cur_file_path] = None
                return self._trace
            trace_it = self.should_trace(cur_file_path)
            if trace_it:
                self.should_trace_cache[real_file_path] = None
                self._init_trace_file(real_file_path, line_no)
            else:
                self.should_not_trace_cache[cur_file_path] = None
        return self._trace

    def start(self):
        sys.settrace(self._trace)
        return self._trace
