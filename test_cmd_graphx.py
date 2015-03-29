"""command doit graph - display a graph with task dependencies"""

from __future__ import print_function

from cmd_graphx import _match_prefix, Graphx

import unittest
import six
from doit.task import Task
from six import StringIO
from tests.conftest import CmdFactory


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


class TestCmdGraphx(unittest.TestCase):

    def tasks(self):
        return [
            Task("read", None, file_dep=['fin.txt'], targets=['fout.hdf5']),
            Task("t3", None, task_dep=['t3:a'], has_subtask=True, ),
            Task("t3:a", None, is_subtask=True),
            Task("t4", None, task_dep=['r*']),
        ]

    def test_store_json_stdout(self):
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=self.tasks())
        cmd._execute(graph_type='json')
        got = output.getvalue()
        self.assertIn("read", got)
        self.assertIn("t3", got)
        self.assertIn("t4", got)

    def test_target(self):
        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=self.tasks())
        cmd._execute(graph_type='json')
        got = output.getvalue()
        self.assertIn("fout.hdf5", got)

        output = StringIO()
        cmd = CmdFactory(Graphx, outstream=output, task_list=self.tasks())
        cmd._execute(graph_type='json', deps='file')
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
