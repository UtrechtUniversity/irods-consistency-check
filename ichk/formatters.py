"""Formatters for output of checks"""

from __future__ import print_function


class Formatter(object):

    def head(self):
        raise NotImplementedError

    def fmt(self):
        raise NotImplementedError


class HumanFormatter(Formatter):
    def __init__(self, output):
        self.output = output

    def head(self):
        print("Resource Path\t\t\t|Vault Path\t\t\t|Status", self.output)

    def fmt(self, resource_path, vault_path, status):
        print("{resource_path}\t\t\t|{vault_path}\t\t\t|{status.name}\n".format(**locals()), self.output)


class CSVFormatter(Formatter):
    pass
