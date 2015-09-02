import inspect
from collections import defaultdict
import time
from grouper import Grouper
from graph import GraphvizOutput


class CallStackCollector:
    def __init__(self):
        # Current call stack
        self.call_stack = ['__main__']
        # A mapping of which function called which other function
        self.call_dict = defaultdict(lambda: defaultdict(int))
        # Counters for each function
        self.func_count = defaultdict(int)
        self.func_count_max = 0
        self.call_stack_timer = []
        self.previous_event_return = False
        # Accumulative time per function
        self.func_time = defaultdict(float)
        self.func_time_max = 0
        self.trace_grouper = Grouper()
        self.painter = GraphvizOutput()
        self.painter.processor = self

    def collect(self, frame, event):
        if event == 'call':
            keep = True
            code = frame.f_code

            # Stores all the parts of a human readable name of the current call
            full_name_list = []

            # Work out the module name
            module = inspect.getmodule(code)
            if module:
                module_name = module.__name__

                if module_name == '__main__':
                    module_name = ''
            else:
                module_name = ''

            if module_name:
                full_name_list.append(module_name)

            # Work out the class name
            try:
                class_name = frame.f_locals['self'].__class__.__name__
                full_name_list.append(class_name)
            except (KeyError, AttributeError):
                pass

            # Work out the current function or method
            func_name = code.co_name
            if func_name == '?':
                func_name = '__main__'
            full_name_list.append(func_name)

            # Create a readable representation of the current call
            full_name = '.'.join(full_name_list)

            # the stack call is too deeeeeeep
            if len(self.call_stack) > 99:
                keep = False

            # Store the call information
            if keep:

                if self.call_stack:
                    src_func = self.call_stack[-1]
                else:
                    src_func = None

                self.call_dict[src_func][full_name] += 1

                self.func_count[full_name] += 1
                self.func_count_max = max(
                    self.func_count_max, self.func_count[full_name]
                )

                self.call_stack.append(full_name)
                self.call_stack_timer.append(time.time())

            else:
                self.call_stack.append('')
                self.call_stack_timer.append(None)

        if event == 'return':

            self.previous_event_return = True

            if self.call_stack:
                full_name = self.call_stack.pop(-1)

                if self.call_stack_timer:
                    start_time = self.call_stack_timer.pop(-1)
                else:
                    start_time = None

                if start_time:
                    call_time = time.time() - start_time

                    self.func_time[full_name] += call_time
                    self.func_time_max = max(
                        self.func_time_max, self.func_time[full_name]
                    )

    def stat_group_from_func(self, func, calls):
        stat_group = StatGroup()
        stat_group.name = func
        stat_group.group = self.trace_grouper(func)
        stat_group.calls = Stat(calls, self.func_count_max)
        stat_group.time = Stat(self.func_time.get(func, 0), self.func_time_max)

        return stat_group

    def nodes(self):
        funcs = self.func_count.keys()
        for func in funcs:
            calls = self.func_count[func]
            yield self.stat_group_from_func(func, calls)

    def edges(self):
        src_funcs = self.call_dict.keys()
        for src_func in src_funcs:
            if not src_func:
                continue
            dest_funcs = self.call_dict[src_func]
            dst_funcs = dest_funcs.keys()
            for dst_func in dst_funcs:
                calls = dest_funcs[dst_func]
                edge = self.stat_group_from_func(dst_func, calls)
                edge.src_func = src_func
                edge.dst_func = dst_func
                yield edge

    def groups(self):
        grp = defaultdict(list)
        for node in self.nodes():
            grp[node.group].append(node)
        for g in grp.iteritems():
            yield g

    def harvest_data(self):
        """
        Collect the call stack graph data.
        """
        clusters = []
        for group, nodes in self.groups():
            funcs = [node.name for node in nodes]
            clusters.append({
                'cluster': group,
                'nodes': funcs
            })
        nodes = []
        for node in self.nodes():
            nodes.append({
                'name': node.name,
                'calls': node.calls.value,
                'time': node.time.value,
                'avg': node.time.value / node.calls.value
            })
        edges = []
        for edge in self.edges():
            edges.append({
                'from': edge.src_func,
                'to': edge.dst_func
            })
        return {
            'clusters': clusters,
            'nodes': nodes,
            'edges': edges
        }

    def draw_graph(self):
        self.painter.done()
        try:
            fd = open('pycallgraph.png', 'rb')
            binary = fd.read()
            fd.close()
        except Exception, e:
            binary = bytes()
        return binary

    def reset(self):
        self.call_stack = ['__main__']
        self.call_dict.clear()
        self.func_count.clear()
        self.call_stack_timer = []
        self.previous_event_return = False
        self.func_time.clear()


class Stat(object):
    """
    Stores a "statistic" value, e.g. "time taken" along with the maximum
    possible value of the value, which is used to calculate the fraction of 1.
    The fraction is used for choosing colors.
    """

    def __init__(self, value, total):
        self.value = value
        self.total = total
        try:
            self.fraction = value / total
        except ZeroDivisionError:
            self.fraction = 0


class StatGroup(object):
    def __init__(self):
        self.name = None
        self.group = None
        self.calls = None
        self.time = None
        self.src_func = None
        self.dst_func = None
