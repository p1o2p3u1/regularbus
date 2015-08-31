from __future__ import division
import textwrap
import tempfile
import os
from color import Color


def node_color(node):
    value = float(node.time.fraction * 2 + node.calls.fraction) / 3
    return Color.hsv(value / 2 + .5, value, 0.9)


def edge_color(edge):
    value = float(edge.time.fraction * 2 + edge.calls.fraction) / 3
    return Color.hsv(value / 2 + .5, value, 0.7)


def node_label(node):
    parts = [
        '{0.name}',
        'calls: {0.calls.value:n}',
        'time: {0.time.value:f}s',
    ]

    return r'\n'.join(parts).format(node)


def edge_label(edge):
    return '{0}'.format(edge.calls.value)


def attrs_from_dict(d):
    output = []
    for attr, val in d.iteritems():
        output.append('%s = "%s"' % (attr, val))
    return ', '.join(output)


def gen_node(key, attr):
    return '"{0}" [{1}];'.format(
        key, attrs_from_dict(attr),
    )


def gen_edge(edge, attr):
    return '"{0.src_func}" -> "{0.dst_func}" [{1}];'.format(
        edge, attrs_from_dict(attr),
    )


class GraphvizOutput:

    def __init__(self):
        self.processor = None
        self.output_file = 'pycallgraph'
        self.font_name = 'Verdana'
        self.font_size = 7
        self.group_font_size = 10
        self.group_border_color = Color(0, 0, 0, 0.8)
        self.graph_attributes = None

        self.prepare_graph_attributes()

    def prepare_graph_attributes(self):

        self.graph_attributes = {
            'graph': {
                'overlap': 'scalexy',
                'fontname': self.font_name,
                'fontsize': self.font_size,
                'fontcolor': Color(0, 0, 0, 0.5).rgba_web()
            },
            'node': {
                'fontname': self.font_name,
                'fontsize': self.font_size,
                'fontcolor': Color(0, 0, 0).rgba_web(),
                'style': 'filled',
                'shape': 'rect',
            },
            'edge': {
                'fontname': self.font_name,
                'fontsize': self.font_size,
                'fontcolor': Color(0, 0, 0).rgba_web(),
            }
        }

    def done(self):
        source = self.generate()
        fd, temp_name = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write(source)

        cmd = '"dot" -Tpng -o{0} {1}'.format(self.output_file, temp_name)

        try:
            ret = os.system(cmd)
            if ret:
                raise Exception(
                    'The command "%(cmd)s" failed with error '
                    'code %(ret)i.' % locals())
        finally:
            os.unlink(temp_name)

    def generate(self):
        """
        Returns a string with the contents of a DOT file for Graphviz to
        parse.
        """
        indent_join = '\n' + ' ' * 12

        return textwrap.dedent('''\
        digraph G {{

            // Attributes
            {0}

            // Groups
            {1}

            // Nodes
            {2}

            // Edges
            {3}

        }}
        '''.format(
            indent_join.join(self.generate_attributes()),
            indent_join.join(self.generate_groups()),
            indent_join.join(self.generate_nodes()),
            indent_join.join(self.generate_edges()),
        ))

    def generate_attributes(self):
        output = []
        for section, attrs in self.graph_attributes.iteritems():
            output.append('{0} [ {1} ];'.format(
                section, attrs_from_dict(attrs),
            ))
        return output

    def generate_groups(self):

        output = []
        for group, nodes in self.processor.groups():
            funcs = [node.name for node in nodes]
            funcs = '" "'.join(funcs)
            group_color = self.group_border_color.rgba_web()
            group_font_size = self.group_font_size
            output.append(
                'subgraph "cluster_{group}" {{ '
                '"{funcs}"; '
                'label = "{group}"; '
                'fontsize = "{group_font_size}"; '
                'fontcolor = "black"; '
                'style = "bold"; '
                'color="{group_color}"; }}'.format(**locals()))
        return output

    def generate_nodes(self):
        output = []
        for node in self.processor.nodes():
            attr = {
                'color': node_color(node).rgba_web(),
                'label': node_label(node),
            }
            output.append(gen_node(node.name, attr))

        return output

    def generate_edges(self):
        output = []

        for edge in self.processor.edges():
            attr = {
                'color': edge_color(edge).rgba_web(),
                'label': edge_label(edge),
            }
            output.append(gen_edge(edge, attr))

        return output
