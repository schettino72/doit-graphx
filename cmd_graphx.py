"""command doit graph - display a graph with task dependencies"""

from __future__ import print_function

from _functools import partial
from _version import (__version__, __updated__)  # @UnusedImport
from doit import cmd_base
from doit.cmd_base import DoitCmdBase
from doit.exceptions import InvalidCommand
import os
import pprint
import re
import sys
from textwrap import dedent

import six

import networkx as nx


def _match_prefix(items, prefix):
    """
    Utility function for detexting ambiguous prefixes

    :return:    which one of `items` starts with `prefix` unambiguously, 
                or None none matched
    :raises ValueError: if `prefix` matches multiple matched in `items`
    """
    matched = [i for i in items if i.startswith(prefix)]
    if matched:
        if len(matched) > 1:
            msg = "prefix '{}' matched {}; must be one of {}"
            raise ValueError(msg.format(prefix, matched, sorted(items)))
        return matched[0]


def _draw_matplotlib_graph(graph, fname, disp_params, **kws):
    # TODO: maplotlib ignores fname
    from matplotlib import pyplot as plt

    template = disp_params['template']
    show_status = disp_params['show_status']

    def find_node_attr(g, attr, value):
        return [n for n, d in g.nodes_iter(data=True) if d[attr] == value]

    def find_edge_attr(g, attr, value):
        return [(n1, n2) for n1, n2, d in g.edges_iter(data=True) if d[attr] == value]

    node_type_styles = {
        'task':     {'node_color': 'g', 'node_shape': 's'},
        'wildcard': {'node_color': 'g', 'node_shape': 'p'},
        'file':     {'node_color': 'b', 'node_shape': 'o'},
    }
    dep_type_styles = {
        # TASK-dependencies
        'task_dep': {'edge_color': 'k'},
        'setup_tasks': {'edge_color': 'm', },
        'calc_dep': {'edge_color': 'g', },
        'wild_dep': {'edge_color': 'k', 'style': 'dashed'},
        # DATA-dependencies
        'file_dep': {'edge_color': 'b', },
        'targets':   {'edge_color': 'c', },
    }

    pos = nx.spring_layout(graph, dim=2)
    for item_type, style in six.iteritems(node_type_styles):
        nodes = find_node_attr(graph, 'type', item_type)
        nx.draw_networkx_nodes(graph, pos, nodes,
                               label=item_type, alpha=0.8,
                               **style)
    for item_type, style in six.iteritems(dep_type_styles):
        edges = find_edge_attr(graph, 'type', item_type)
        edge_col = nx.draw_networkx_edges(graph, pos, edges,
                                          label=item_type, alpha=0.5,
                                          **style)
        if edge_col:
            edge_col.set_label(None)  # Remove duplicate label on DiGraph.

    if template is None:
        template = '{name}'
        if show_status:
            template = '({status})' + template
    labels = {n: (template.format(name=n, **d) if d['type'] == 'task' else n)
              for n, d in graph.nodes_iter(data=True)}
    nx.draw_networkx_labels(graph, pos, labels)

    ax = plt.gca()
    ax.legend(scatterpoints=1, framealpha=0.5)
    # ax.set_frame_on(False)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    plt.subplots_adjust(0, 0, 1, 1)

    plt.show()


def _store_json(graph, fname, disp_params, **kws):
    import json
    # TODO: Obey disp_params on json
    m = nx.to_dict_of_dicts(graph)
    json.dump(m, fname, **kws)


def _call_nx_write_func(func, graph, fname, disp_params, **kws):
    """Just consumes `disp_params` which is used by json & matplotlib"""
    func(graph, fname, **kws)


def _add_all_supported_output_formats():
    """Add all `nx.write_XXX()` methods plus json & matplotlib funcs, above."""
    prefix = 'write_'
    formats = {m[len(prefix):]: partial(_call_nx_write_func, getattr(nx, m))
               for m in dir(nx) if m.startswith(prefix)}
    formats['json'] = _store_json
    formats['matplotlib'] = _draw_matplotlib_graph
    return formats

# FIXME: Discover import-time for help-strings
#     (Cmd.doc_description should be a function
SUPPORTED_GRAPH_TYPES = _add_all_supported_output_formats()


def _select_graph_func(graph, graph_type):
    graph_names = sorted(SUPPORTED_GRAPH_TYPES)
    try:
        matched_graph_type = _match_prefix(graph_names, graph_type.lower())
    except ValueError as ex:
        raise InvalidCommand("graph-type %s" % ex.args[0])
    else:
        if not matched_graph_type:
            msg = "Unsupported graph-type '%s'; should be one: %s"
            raise InvalidCommand(msg % (graph_type, graph_names))
        else:
            func = SUPPORTED_GRAPH_TYPES[matched_graph_type]

            return matched_graph_type, func


def _construct_graph(all_tasks_map, filter_task_names, no_children, filter_deps):
    """
    Construct a *networkx* graph of nodes (Tasks/Files/Wildcards) and 
    their dependencies (file/wildcard, task/setup,calc).

    :param seq filter_task_names: If None, graph includes all tasks
    :param str filter_deps: a list of prefixes separated with [,| ],
                            If None, includes all deps
    """

    dep_attributes = {
        'task_dep':     {'node_type': 'task'},
        'setup_tasks':  {'node_type': 'task'},
        'calc_dep':     {'node_type': 'task'},
        'file_dep':     {'node_type': 'file'},
        'wild_dep':     {'node_type': 'wildcard'},
        'targets':      {'node_type': 'file'},
    }

    dep_attributes = Graphx._filter_dep_attributes_to_collect(
        dep_attributes, filter_deps)

    graph = nx.DiGraph()

    def add_graph_node(node, node_type):
        if node in graph:
            return
        if node_type != 'task':
            graph.add_node(node, type=node_type)
        else:
            graph.add_node(node, type=node_type)
            task = all_tasks_map[node]
            if not filter_task_names or node in filter_task_names:
                for dep, dep_kws in six.iteritems(dep_attributes):
                    for dname in getattr(task, dep):
                        add_graph_node(
                            dname, dep_kws['node_type'])
                        if dep == 'targets':
                            edge = (dname, node)
                        else:
                            edge = (node, dname)
                        graph.add_edge(*edge, type=dep)

    for tname in (filter_task_names or all_tasks_map.keys()):
        add_graph_node(tname, 'task')

    return graph


opt_subtasks = {
    'name': 'subtasks',
    'short': 'b',
    'long': 'subtasks',
    'type': bool,
    'default': False,
    'help': "include also sub-tasks"
            "(applies when task-list given)"
}

opt_private = {
    'name': 'private',
    'short': 'p',
    'long': 'private',
    'type': bool,
    'default': False,
    'help': "include also private tasks starting with '_'"
            " (applies when task-list given)"
}

opt_no_children = {
    'name': 'no_children',
    'short': 'c',
    'long': 'no-children',
    'type': bool,
    'default': False,
    'help': "TODO: include only selected tasks"
            " (applies when task-list given)"
}

opt_deps = {
    'name': 'deps',
    'short': '',
    'long': 'deps',
    'type': str,
    'default': '',
    'help': "type of dependencies to include from selected tasks"
            " (list of: ALL|file|wild|task|calc|setup|none|target)"
}

opt_show_status = {
    'name': 'show_status',
    'short': 's',
    'long': 'status',
    'type': bool,
    'default': False,
    'help': "read task-status (R)un, (U)p-to-date, (I)gnored"
            " (matplotlib-only, see `--template`)"
}

opt_template = {
    'name': 'template',
    'short': '',
    'long': 'template',
    'type': str,
    'default': None,
    'help': "template for task-labels "
            "(matplotlib-only, use %s to get all keywords)"
}

opt_graph_type = {
    'name': 'graph_type',
    'short': 'g',
    'long': 'graph',
    'type': str,
    'default': 'matplotlib',
    'help': "selection of graph library"
            " (one of: %s)." % sorted(SUPPORTED_GRAPH_TYPES)
}

opt_out_file = {
    'name': 'out_file',
    'short': 'O',
    'long': 'out-file',
    'type': str,
    'default': '-',
    'help': "where to store graph, if textual"
}



class Graphx(DoitCmdBase):

    """command doit graph"""

    doc_purpose = "display a dependency-graph for all (or selected ) tasks"
    doc_usage = "[TASK ...]"
    doc_description = dedent("""\
        Without any options, includes all known taks.
        TODO: Task-selection works with wildcards.
        
        Examples:
          doit graph        ## By default, plots a matplotlib frame
          doit graph --deps file,calc,target --private
          doit graph --out-file some.png
          doit graph --graph-type json --out-file some.png
        
        For networkx's `write_XXX()` methods see:
        http://networkx.github.io/documentation/latest/reference/readwrite.html

        version: {}
        See https://github.com/pydoit/doit-graphx
        """.format(__version__))

    cmd_options = (opt_subtasks, opt_private, opt_no_children, opt_deps,
                   opt_show_status, opt_template, opt_graph_type,
                   opt_out_file)

    STATUS_MAP = {'ignore': 'I', 'up-to-date': 'U', 'run': 'R'}

    @staticmethod
    def _check_task_names(all_task_names, task_names):
        """repost if task 'task_names' """
        # Note: simpler and user-friendlier than cmd_base.check_tasks_exist()
        if not set(task_names).issubset(all_task_names):
            bad_tasks = set(task_names) - all_task_names
            msg = "Task(s) not found: %s" % str(bad_tasks)
            raise InvalidCommand(msg)

    @staticmethod
    def _include_subtasks(tasks, task_names, include_subtasks):
        """append any subtasks of 'task_names' """
        # get task by name
        subtasks = []
        for name in task_names:
            subtasks.extend(
                cmd_base.subtasks_iter(tasks, tasks[name]))
        return subtasks

    @staticmethod
    def _filter_dep_attributes_to_collect(dep_attributes, filter_deps):
        if not filter_deps:
            return dep_attributes
        filter_deps = re.sub(r'[\s,|]+', ' ', filter_deps).strip()
        if not filter_deps:
            return dep_attributes
        else:
            dep_names = list(dep_attributes)
            dep_names.extend(['all', 'none'])
            dep_attributes_out = {}
            for f_dep in filter_deps.lower().split():
                try:
                    full_dep = _match_prefix(dep_names, f_dep)
                except ValueError as ex:
                    raise InvalidCommand("graph-type %s" % ex.args[0])
                else:
                    if not full_dep:
                        msg = "Unsupported dependency-type '%s'; should be one: %s"
                        raise InvalidCommand(
                            msg % (full_dep, sorted(dep_names)))
                    if 'all' == full_dep:
                        return dep_attributes
                    elif 'none' == full_dep:
                        return {}
                    dep_attributes_out[full_dep] = dep_attributes[full_dep]

            return dep_attributes_out

    def _update_task_nodes(self, tasks_map, graph, show_status):
        def task_status(task):
            # FIXME group task status is never up-to-date
            if self.dep_manager.status_is_ignore(task):
                task_status = 'ignore'
            else:
                # FIXME:'ignore' handling is ugly
                task_status = self.dep_manager.get_status(task, None)
            return Graphx.STATUS_MAP[task_status]
        for node, d in graph.nodes(data=True):
            if d['type'] == 'task':
                task = tasks_map[node]
                status = task_status(task) if show_status else ''
                d['status'] = status
                d['is_subtask'] = task.is_subtask

    def _prepare_out_file(self, fname, ext):
        """Appends extension(dot included) if `fname` has'nt got one, or `stdout` if was '-'."""
        if '-' == fname:
            return self.outstream

        _, e = os.path.splitext(fname)
        if e:
            ext = ''
        return fname + ext

    def _execute(self,
                 subtasks=opt_subtasks['default'],
                 no_children=opt_no_children['default'],
                 private=opt_private['default'],
                 show_status=opt_show_status['default'],
                 deps=opt_deps['default'],
                 template=opt_template['default'],
                 graph_type=opt_graph_type['default'],
                 out_file=opt_out_file['default'],
                 pos_args=None):
        task_names = pos_args
        tasks_map = dict([(t.name, t) for t in self.task_list])

        # TODO: Imporve task-selection procedure.
        #
        if task_names:
            Graphx._check_task_names(tasks_map.keys(), task_names)
            if not private:
                task_names = [t for t in task_names if not t.startswith('_')]
            if subtasks:
                task_names = Graphx._include_subtasks(
                    tasks_map, task_names, subtasks)

        graph = _construct_graph(tasks_map, task_names, no_children, deps)
        self._update_task_nodes(tasks_map, graph, show_status)
        graph_type, func = _select_graph_func(graph, graph_type)
        out_file = self._prepare_out_file(out_file, graph_type)
        disp_params = dict(zip(['graph_type', 'show_status', 'deps', 'template'],
                               [graph_type, show_status, deps, template]))
        kws = {}  # TODO: kws not used on write_XXX() methods.
        func(graph, out_file, disp_params, **kws)
