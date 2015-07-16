import os
import sys
from tracer import SimplePyTracer

class CoverageCollector:

    def __init__(self):
        self.data = {}
        self.tracer = None

    def start(self):
        self.tracer = SimplePyTracer()
        self.tracer.data = self.data
        self.tracer.should_trace = self._should_trace
        fn = self.tracer.start()
        return fn

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
        return True

    def harvest_data(self):
        """
        {
            "file1.py": {
                "code": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "executed": [1, 2, 3, 4, 5, 6, 7, 8, 9],
                "missing": [10],
                "coverage": 0.9
            }
        }
        """
        result = {}
        for filename, item in self.tracer.parse_cache.iteritems():
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
