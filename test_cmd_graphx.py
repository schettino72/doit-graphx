"""command doit graph - display a graph with task dependencies"""

from __future__ import print_function

from cmd_graphx import Graphx
import cmd_graphx
from doit.exceptions import InvalidCommand
from doit.task import Task
from tests.conftest import CmdFactory
import unittest

from six import StringIO
import six


class TestMatchPrefix(unittest.TestCase):

    def items(self):
        return ['abc', 'ab_', '123', '1__']

    def test_fail(self):
        prefixes = [None, []]
        for prefix in prefixes:
            self.assertRaises(
                TypeError, cmd_graphx._match_prefix, self.items(), prefix)

    def test_unknown(self):
        prefixes = ['abcd', 'foo', 'abcd', '11', tuple(), ]
        for prefix in prefixes:
            self.assertIsNone(cmd_graphx._match_prefix(self.items(), prefix))

    def test_good(self):
        prefixes = ['abc', 'ab_', '12', '1_']
        results = ['abc', 'ab_', '123', '1__']
        for prefix, result in zip(prefixes, results):
            self.assertEqual(
                cmd_graphx._match_prefix(self.items(), prefix), result, prefix)

    def test_ambiguous(self):
        prefixes = ['', 'a', 'ab', '1']
        for prefix in prefixes:
            self.assertRaises(
                ValueError, cmd_graphx._match_prefix, self.items(), prefix)


class TestFilterDepAttributes(unittest.TestCase):

    def _deps_attributes(self):
        return {'task_dep': 1, 'setup_tasks': 2, 'calc_dep': 3,
                'file_dep': 4, 'wild_dep': 5, 'targets': 6, }

    def test_empty(self):
        attrs_in = self._deps_attributes()
        filters = ''
        attrs_out = Graphx._filter_dep_attributes_to_collect(attrs_in, filters)
        self.assertEqual(attrs_out, attrs_in, filters)

    def test_prefixes_n_separators(self):
        attrs_in = self._deps_attributes()
        filters = '  se | FIL,  tAs | c wil tar |'
        attrs_out = Graphx._filter_dep_attributes_to_collect(attrs_in, filters)
        self.assertEqual(attrs_out, attrs_in, filters)

    def test_ambiguous(self):
        attrs_in = self._deps_attributes()
        filters = '  tA '
        self.assertRaises(
            InvalidCommand,
            Graphx._filter_dep_attributes_to_collect, attrs_in, filters)

    def test_all(self):
        attrs_in = self._deps_attributes()
        filters = 'all'
        attrs_out = Graphx._filter_dep_attributes_to_collect(attrs_in, filters)
        self.assertEqual(attrs_out, attrs_in, filters)

    def test_all_and_others(self):
        attrs_in = self._deps_attributes()
        filters = 'calc all,task'
        attrs_out = Graphx._filter_dep_attributes_to_collect(attrs_in, filters)
        self.assertEqual(attrs_out, attrs_in, filters)

    def test_none(self):
        attrs_in = self._deps_attributes()
        filters = ' file,  none | task '
        attrs_out = Graphx._filter_dep_attributes_to_collect(attrs_in, filters)
        self.assertEqual(attrs_out, {}, filters)

    def test_none_and_others(self):
        attrs_in = self._deps_attributes()
        filters = ' fil,  non | task '
        attrs_out = Graphx._filter_dep_attributes_to_collect(attrs_in, filters)
        self.assertEqual(attrs_out, {}, filters)


def _sample_tasks():
    def find_deps():
        return dict(file_dep=['a.json', 'b.json'])

    return [
        Task("read", None, file_dep=['fin.txt'], targets=['fout.hdf5']),
        Task("t3", None, task_dep=['t3:a'], has_subtask=True, ),
        Task("t3:a", None, is_subtask=True, file_dep=[
             'fout.hdf5'], targets=['a.json']),
        Task("t3:b", None, is_subtask=True,
             file_dep=['fout.hdf5', 'fin.txt'], targets=['b.json']),
        Task("join_files", None, task_dep=[
             't3:*', 't3:a', 't3:b', ], calc_dep=['find_deps']),
        Task("find_deps", [find_deps]),
    ]


def _sample_tasks_map():
    return dict([(t.name, t) for t in _sample_tasks()])


class TestConstructGraph(unittest.TestCase):

    def test_filter_nodes_empty(self):
        filter_task_names = []
        tasks_map = _sample_tasks_map()
        graph = cmd_graphx._construct_graph(tasks_map, filter_task_names,
                                            no_children=False, filter_deps=None)
        self.assertTrue(
            len(graph.nodes()) > 0, 'Nodes empty: %s' % graph.nodes())
        self.assertTrue(
            len(graph.edges()) > 0, 'Edges empty: %s' % graph.edges())

    def test_filter_nodes_none(self):
        filter_task_names = None
        tasks_map = _sample_tasks_map()
        graph = cmd_graphx._construct_graph(tasks_map, filter_task_names,
                                            no_children=False, filter_deps=None)
        self.assertTrue(
            len(graph.nodes()) > 0, 'Nodes empty: %s' % graph.nodes())
        self.assertTrue(
            len(graph.edges()) > 0, 'Edges empty: %s' % graph.edges())

    def test_filter_nodes_one(self):
        filter_task_names = []
        tasks_map = _sample_tasks_map()
        graph = cmd_graphx._construct_graph(tasks_map, filter_task_names,
                                            no_children=False, filter_deps=None)
        self.assertTrue(
            len(graph.nodes()) > 0, 'Nodes empty: %s' % graph.nodes())
        self.assertTrue(
            len(graph.edges()) > 0, 'Edges empty: %s' % graph.edges())

    def test_node_attributes(self):
        filter_task_names = []
        tasks_map = _sample_tasks_map()
        graph = cmd_graphx._construct_graph(tasks_map, filter_task_names,
                                            no_children=False, filter_deps=None)
        for node, d in graph.nodes(data=True):
            self.assertIn('type', d, (node, d))
            # This test does not belong here!
            # if d['type'] == 'task':
            #     self.assertIn('status', d, (node, d))
            #     self.assertIn('is_subtask', d, (node, d))


class TestCmdGraphx(unittest.TestCase):

    @unittest.skip(('Blocks on graph-plot.'))
    def test_matplotlib(self):
        cmd = CmdFactory(Graphx, task_list=_sample_tasks())
        cmd._execute()

    def test_store_json_stdout(self):
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=_sample_tasks())
        cmd._execute(graph_type='json')
        got = output.getvalue()
        self.assertIn("read", got)
        self.assertIn("t3", got)
        self.assertIn("join_files", got)

    def test_target_in(self):
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=_sample_tasks())
        cmd._execute(graph_type='json')
        got = output.getvalue()
        self.assertIn("fout.hdf5", got)

    def test_target_out(self):
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=_sample_tasks())
        cmd._execute(graph_type='json', deps='task')
        got = output.getvalue()
        self.assertNotIn("fout.hdf5", got)

    def test_children(self):
        # TODO: Implement no-child option.
        my_task = Task("t2", [""], file_dep=['d2.txt'])
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=[my_task])
        cmd._execute(graph_type='json', no_children=False)
        got = output.getvalue()
        self.assertIn("d2.txt", got)

    @unittest.skip('NOT IMPL YET')
    def test_no_children(self):
        my_task = Task("t2", [""], file_dep=['d2.txt'])
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=[my_task])
        cmd._execute(graph_type='json', no_children=True)
        got = output.getvalue()
        self.assertNotIn("d2.txt", got)
