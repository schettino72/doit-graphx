from doit.cmd_base import Command

class Graphx(Command):
    name = 'graphx'
    doc_purpose = 'generate graph of doit tasks and dependencies'
    doc_usage = '[TASK]'
    doc_description = ''

    def execute(self, opt_values, pos_args):
        print("DO SOMETHING")
