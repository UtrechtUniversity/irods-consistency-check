"""Formatters for output of checks"""

from __future__ import print_function


class Formatter(object):

    def __init__(self, output):
        self.output = output

    def head(self):
        raise NotImplementedError

    def fmt(self):
        raise NotImplementedError


class HumanFormatter(Formatter):
    def head(self):
        print("[Status] Resource Path => Vault Path", file=self.output)

    def fmt(self, resource_path, vault_path, status):
        print("[{status.name}] {resource_path} => {vault_path}".format(**locals())[:180], file=self.output)


class CSVFormatter(Formatter):
    pass
