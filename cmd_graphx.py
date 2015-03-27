"""command doit graph - display a graph with task dependencies"""

from __future__ import print_function

from doit import cmd_base
from doit.cmd_base import DoitCmdBase
from doit.exceptions import InvalidCommand
import pprint
import re
from textwrap import dedent

import six


def _draw_matplotlib_graph(graph, template, show_status):
    import networkx as nx
    from matplotlib import pyplot as plt

    def find_node_attr(g, attr, value):
        return [n for n,d in g.nodes_iter(data=True) if d[attr] == value]
    def find_edge_attr(g, attr, value):
        return [(n1,n2) for n1,n2,d in g.edges_iter(data=True) if d[attr] == value]

    node_type_styles = {
        'task':     { 'node_color': 'g', 'node_shape': 's'},
        'file':     { 'node_color': 'b', 'node_shape': 'o'},
        'wildcard': { 'node_color': 'c', 'node_shape': '8'},
    }
    dep_type_styles = {
        ## TASK-dependencies
        'task_dep': { 'edge_color': 'k', 'style': 'dotted'},
        'setup_dep':{ 'edge_color': 'm', },
        'calc_dep': { 'edge_color': 'g', },
        ## DATA-dependencies
        'file_dep': { 'edge_color': 'b', },
        'wild_dep': { 'edge_color': 'b', 'style': 'dashed'},
        'target':   { 'edge_color': 'c', },
    }

    pos = nx.spring_layout(graph, dim=2)
    for item_type, style in six.iteritems(node_type_styles):
        nodes       = find_node_attr(graph, 'type', item_type)
        nx.draw_networkx_nodes(graph, pos, nodes,
                               label=item_type, alpha=0.8,
                               **style)
    for item_type, style in six.iteritems(dep_type_styles):
        edges       = find_edge_attr(graph, 'type', item_type)
        edge_col    = nx.draw_networkx_edges(graph, pos, edges,
                               label=item_type, alpha=0.5,
                               **style)
        if edge_col:
            edge_col.set_label(None)    ## Remove duplicate label on DiGraph.

    if template is None:
        template = '{name}'
        if show_status:
            template = '({status})' + template
    labels = {n: (template.format(name=n, **d) if d['type'] == 'task' else n)
                   for n,d in graph.nodes_iter(data=True)}
    nx.draw_networkx_labels(graph, pos, labels)
    
    ax = plt.gca()
    ax.legend(scatterpoints=1, framealpha=0.5)
    #ax.set_frame_on(False)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    plt.subplots_adjust(0,0,1,1)

    plt.show()


SUPPORTED_GRAPH_TYPES = {'matplotlib': _draw_matplotlib_graph}


opt_subtasks = {
    'name': 'subtasks',
    'short':'b',
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
    'short':'c',
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
            " (list of: ALL|file|wild|task|calc|setup|none|TODO:target)"
    }

opt_show_status = {
    'name': 'show_status',
    'short': 's',
    'long': 'status',
    'type': bool,
    'default': False,
    'help': 'read task-status (R)un, (U)p-to-date, (I)gnored (see `--template`)'
    }

opt_template = {
    'name': 'template',
    'short': '',
    'long': 'template',
    'type': str,
    'default': None,
    'help': "template for task-labels (use %s to get all keywords)"
    }

opt_graph_type = {
    'name': 'graph_type',
    'short': 'g',
    'long': 'graph',
    'type': str,
    'default': 'matplotlib',
    'help': "selection of graph library"
            " (one of: %s)." % list(SUPPORTED_GRAPH_TYPES) 
    }

opt_out_file = {
    'name': 'out_file',
    'short': 'O',
    'long': 'out-file',
    'type': str,
    'default': False,
    'help': "TODO: where to store graph, if textual"
    }


def my_safe_repr(obj, context, maxlevels, level):
    """pretty print supressing unicode prefix

    http://stackoverflow.com/questions/16888409/
           suppress-unicode-prefix-on-strings-when-using-pprint
    """
    typ = type(obj)
    if six.PY2 and typ is six.text_type:
        obj = str(obj)
    return pprint._safe_repr(obj, context, maxlevels, level)


class Graphx(DoitCmdBase):
    """command doit graph"""

    doc_purpose = "display a dependency-graph for all (or selected ) tasks"
    doc_usage = "[TASK ...]"
    doc_description = dedent("""\
        Without any options, includes all known taks.
        TODO: Task-selection works also with wildcards.
        
        Examples:
          doit graph
          doit graph --deps file,calc,target --private
          doit graph --out-file some.png
          doit graph --graph-type json --out-file some.png
        """)

    cmd_options = (opt_subtasks, opt_private, opt_no_children, opt_deps, 
                   opt_show_status, opt_template, opt_graph_type, 
                   opt_out_file)

    STATUS_MAP = {'ignore': 'I', 'up-to-date': 'U', 'run': 'R'}


    @staticmethod
    def _check_task_names(all_task_names, task_names):
        """repost if task 'task_names' """
        ## Note: simpler and user-friendlier than cmd_base.check_tasks_exist()
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
            subtasks.extend(cmd_base.subtasks_iter(tasks, tasks[name]))
        return subtasks

    @staticmethod
    def _get_task_status(dep_manager, task):
        """print a single task"""
        # FIXME group task status is never up-to-date
        if dep_manager.status_is_ignore(task):
            task_status = 'ignore'
        else:
            # FIXME:'ignore' handling is ugly
            task_status = dep_manager.get_status(task, None)
        return Graphx.STATUS_MAP[task_status]

    def _prepare_graph(self, all_tasks_map, filter_task_names, filter_deps, show_status):
        """
        Construct a *networkx* graph of nodes (Tasks/Files/Wildcards) and their dependencies (file/wildcard, task/setup,calc).

        :param filter_task_names: If None, graph includes all tasks
        """
        import networkx as nx
        
        def _filter_dependencies_to_collect(dep_attributes, filter_deps):
            filter_deps = re.sub(r'[\s,|]+', ' ', filter_deps).strip()
            if filter_deps:
                dep_attributes2 = {}
                for f_dep in filter_deps.split():
                    if 'all'.startswith(f_dep):
                        dep_attributes2 = dep_attributes
                    elif 'none'.startswith(f_dep):
                        dep_attributes2 = {}
                    else:
                        dep_attributes2.update({dep:dep_kws
                                for dep, dep_kws 
                                in six.iteritems(dep_attributes)
                                if dep.startswith(f_dep)})
            print(dep_attributes2)
            return dep_attributes2
            

        dep_attributes = {
            'task_dep':     {'node_type':'task'},
            'setup_tasks':  {'node_type':'task', 'edge_type':'setup_dep'},
            'calc_dep':     {'node_type':'task'},
            'file_dep':     {'node_type':'file'},
            'wild_dep':     {'node_type':'wildcard'},
        }
        
        dep_attributes = _filter_dependencies_to_collect(dep_attributes, filter_deps)
        
        graph = nx.DiGraph()
        def add_graph_node(node, node_type, add_deps=False):
            if node in graph:
                return
            if node_type != 'task':
                graph.add_node(node, type=node_type)
            else:
                task = all_tasks_map[node]
                status = ''
                if show_status:
                    status = Graphx._get_task_status(self.dep_manager, task)
                graph.add_node(node, type=node_type,
                               is_subtask=task.is_subtask, status=status)
                if add_deps:
                    for dep, dep_kws in six.iteritems(dep_attributes):
                        for dname in getattr(task, dep):
                            dig_deps = filter_task_names is None or dname in filter_task_names
                            add_graph_node(dname, dep_kws['node_type'], add_deps=dig_deps)
                            graph.add_edge(node, dname, type=dep_kws.get('edge_type', dep))
                    ## Above loop cannot add targets
                    #    because they are reversed.
                    #
                    # FIX: Targets are not filtered!!
                    for dname in task.targets:
                        add_graph_node(dname, 'file')
                        graph.add_edge(dname, node, type='target')

        ## Add all named-tasks
        #    and their dependencies.
        #
        for tname in (filter_task_names or all_tasks_map.keys()):
            add_graph_node(tname, 'task', add_deps=True)

        return graph

    def _display_graph(self, graph, graph_type, template, show_status, out_file):
        for gtype in SUPPORTED_GRAPH_TYPES:
            if gtype.startswith(graph_type):
                func = SUPPORTED_GRAPH_TYPES[gtype]
                func(graph, template, show_status)
                break
        else:
            msg = "Unsupported graph-type '%s'; should be one : %s"
            raise InvalidCommand(msg % (graph_type, list(SUPPORTED_GRAPH_TYPES)))
            
        
    def _execute(self, subtasks=False, no_children=True, show_status=False,
                 private=False, deps=False, template=None,
                 graph_type='matplotlib', out_file=None, pos_args=None):
        task_names=pos_args
        tasks_map = dict([(t.name, t) for t in self.task_list])

        if task_names:
            Graphx._check_task_names(tasks_map.keys(), task_names)
            if not private:
                task_names = [t for t in task_names if not t.startswith('_')]
            if subtasks:
                task_names = Graphx._include_subtasks(tasks_map, task_names, subtasks)
            
        graph = self._prepare_graph(tasks_map, task_names, deps, show_status)

        self._display_graph(graph, graph_type, template, show_status, out_file)


