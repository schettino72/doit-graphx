"""command doit graph - display a graph with task dependencies"""

from __future__ import print_function

from cmd_graphx import _match_prefix, Graphx

import unittest
import six
from doit.task import Task
from six import StringIO
from tests.conftest import CmdFactory
from doit.exceptions import InvalidCommand


class TestMatchPrefix(unittest.TestCase):

    def items(self):
        return ['abc', 'ab_', '123', '1__']

    def test_fail(self):
        prefixes = [None, []]
        for prefix in prefixes:
            self.assertRaises(
                TypeError, _match_prefix, self.items(), prefix)

    def test_unknown(self):
        prefixes = ['abcd', 'foo', 'abcd', '11', tuple(), ]
        for prefix in prefixes:
            self.assertIsNone(_match_prefix(self.items(), prefix))

    def test_good(self):
        prefixes = ['abc', 'ab_', '12', '1_']
        results = ['abc', 'ab_', '123', '1__']
        for prefix, result in zip(prefixes, results):
            self.assertEqual(
                _match_prefix(self.items(), prefix), result, prefix)

    def test_ambiguous(self):
        prefixes = ['', 'a', 'ab', '1']
        for prefix in prefixes:
            self.assertRaises(
                ValueError, _match_prefix, self.items(), prefix)


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


class TestCmdGraphx(unittest.TestCase):

    def _tasks(self):
        def find_deps():
            return dict(file_dep=['a.json', 'b.json'])

        return [
            Task("read", None, file_dep=['fin.txt'], targets=['fout.hdf5']),
            Task("t3", None, task_dep=['t3:a'], has_subtask=True, ),
            Task("t3:a", None, is_subtask=True, file_dep=[
                 'fout.hdf5'], targets=['a.json']),
            Task("t3:b", None, is_subtask=True,
                 file_dep=['fout.hdf5', 'fin.txt'], targets=['b.json']),
            Task("join_files", None, task_dep=['t*'], calc_dep=['find_deps']),
            Task("find_deps", [find_deps]),
        ]

    @unittest.skip(('Blocks on graph-plot.'))
    def test_matplotlib(self):
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=self._tasks())
        cmd._execute()

    def test_store_json_stdout(self):
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=self._tasks())
        cmd._execute(graph_type='json')
        got = output.getvalue()
        self.assertIn("read", got)
        self.assertIn("t3", got)
        self.assertIn("join_files", got)

    def test_target_in(self):
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=self._tasks())
        cmd._execute(graph_type='json')
        got = output.getvalue()
        self.assertIn("fout.hdf5", got)

    def test_target_out(self):
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=self._tasks())
        cmd._execute(graph_type='json', deps='task')
        got = output.getvalue()
        self.assertNotIn("fout.hdf5", got)

    def test_children(self):
        my_task = Task("t2", [""], file_dep=['d2.txt'])
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=[my_task])
        cmd._execute(graph_type='json', no_children=False)
        got = output.getvalue()
        self.assertIn("d2.txt", got)

    def test_no_children(self):
        my_task = Task("t2", [""], file_dep=['d2.txt'])
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=[my_task])
        cmd._execute(graph_type='json', no_children=True)
        got = output.getvalue()
        self.assertNotIn("d2.txt", got)
