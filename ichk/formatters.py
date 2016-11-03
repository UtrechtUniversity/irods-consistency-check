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

    def __init__(self, output=None, truncate=None):
        if truncate:
            # TODO: write routine to check column width of active terminal
            self.truncate = 179
        super(HumanFormatter, self).__init__(output=output)

    def head(self):
        print("[Status] Resource Path => Vault Path", file=self.output)

    def fmt(self, resource_path, vault_path, status):
        print(
            "[{status.name}] {resource_path} => {vault_path}"
            .format(**locals())[:self.truncate],
            file=self.output
        )


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
        self.writer.writerow([status, resource_path, vault_path])

