from coverage.parser import CodeParser


class CoverageCollector:

    def __init__(self, ignore_paths=None):
        self.data = {}
        self.parse_cache = {}

    def collect(self, filename, line_no):
        if filename not in self.data:
            self.data[filename] = set()
        self.data[filename].add(line_no)
        if filename not in self.parse_cache:
            parser = CodeParser(filename=filename)
            statements, _ = parser.parse_source()
            self.parse_cache[filename] = {
                'parser': parser,
                'code': statements
            }

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
        # RuntimeError: dictionary changed size during iteration, so be careful do not use .iteritems()
        for filename in self.parse_cache.keys():
            item = self.parse_cache[filename]
            key = filename.replace('\\', '/')
            parser = item['parser']  # code parser
            code = item['code']  # a set of total code line number
            exec1 = self.data.get(filename) or {}  # a set of code line number that executed
            executed = parser.first_lines(exec1)  # a set of code line number that executed
            missing = code - executed   # a set of code line number that missed execute
            if len(code) == 0:  # for some __init__.py, the file is empty but also have 1 line code executed..Why?
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

    def reset(self):
        self.parse_cache.clear()
        self.data.clear()




