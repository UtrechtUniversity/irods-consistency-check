"""Formatters for output of checks"""

from __future__ import print_function


class Formatter(object):

    def __init__(self, output, **options):
        self.output = output

    def head(self):
        raise NotImplementedError

    def fmt(self):
        raise NotImplementedError


class HumanFormatter(Formatter):

    name = 'human'
    options = ['truncate']
    template = """----
Status: {status.name}
Resource path: {resource_path}
Vault path:  {vault_path}
"""

    def __init__(self, output=None, truncate=None):
        if truncate:
            # TODO: write routine to check column width of active terminal
            self.truncate = 179
        else:
            self.truncate = None
        super(HumanFormatter, self).__init__(output=output)

    def head(self):
        print("Results of consistency check\n\n", file=self.output)

    def fmt(self, resource_path, vault_path, status):
        print(self.template.format(**locals()),
              file=self.output)


class CSVFormatter(Formatter):
    name = 'csv'
    options = []

    def __init__(self, output=None):
        super(CSVFormatter, self).__init__(output=output)

        import csv
        self.writer = csv.writer(self.output, dialect=csv.excel)

    def head(self):
        self.writer.writerow(['Status', 'Resource Path', 'Vault Path'])

    def fmt(self, resource_path, vault_path, status):
        self.writer.writerow([status.name, resource_path, vault_path])

