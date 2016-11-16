"""Formatters for output of checks"""

from __future__ import print_function


class Formatter(object):

    def __init__(self, output, **options):
        self.output = output

    def head(self):
        raise NotImplementedError

    def __call__(self):
        raise NotImplementedError


class HumanFormatter(Formatter):

    name = 'human'
    options = ['truncate']
    template = """----
Type: {0.obj_type.name}
iRODS path: {0.obj_path}
Physical path: {0.phy_path}
Status: {0.status.name}
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

    def __call__(self, result):
        print(self.template.format(result),
              file=self.output)


class CSVFormatter(Formatter):
    name = 'csv'
    options = []

    def __init__(self, output=None):
        super(CSVFormatter, self).__init__(output=output)

        import csv
        self.writer = csv.writer(
            self.output, dialect=csv.excel)

    def head(self):
        self.writer.writerow(('Type', 'Status', 'iRODS Path', 'Physical Path'))

    def __call__(self, result):
        self.writer.writerow(
            (result.obj_type.name,
             result.status.name,
             result.obj_path,
             result.phy_path))
