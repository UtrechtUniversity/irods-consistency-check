"""Formatters for output of checks"""

from __future__ import print_function
from ichk import check
import sys

class Formatter(object):

    PY2 = (sys.version_info.major == 2)

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
Type: {obj_type}
iRODS path: {obj_path}
Physical path: {phy_path}
Status: {status}"""

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
        obj_type = result.obj_type.name
        status = result.status.name
        # python 2 format defaults to ASCII encoding, enforce UTF-8
        if self.PY2:
            obj_path = result.obj_path.encode('utf-8')
            phy_path = result.phy_path.encode('utf-8')
        else:
            obj_path = result.obj_path
            phy_path = result.phy_path

        def printl(message):
            print(message, file=self.output)

        printl(self.template.format(**locals()))

        values = result.observed_values

        if result.status is check.Status.FILE_SIZE_MISMATCH:
            printl("Expected size: " + str(values['expected_filesize']))
            printl("Observed size: " + str(values['observed_filesize']))

        if result.status is check.Status.CHECKSUM_MISMATCH:
            printl("Expected checksum: " + values['expected_checksum'])
            printl("Observed checksum: " + values['observed_checksum'])

        printl("")

class CSVFormatter(Formatter):
    name = 'csv'
    options = []

    def __init__(self, output=None):
        super(CSVFormatter, self).__init__(output=output)

        import csv
        self.writer = csv.writer(
            self.output, dialect=csv.excel)

    def head(self):
        self.writer.writerow(('Type', 'Status', 'iRODS Path', 'Physical Path',
                              'Observed checksum', 'Expected checksum',
                              'Observed size', 'Expected size'))

    def __call__(self, result):
        if self.PY2:
            # python 2 defaults to ASCII encoding, enforce UTF-8
            obj_path = result.obj_path.encode('utf-8')
            phy_path = result.phy_path.encode('utf-8')
        else:
            obj_path = result.obj_path
            phy_path = result.phy_path

        self.writer.writerow(
            (result.obj_type.name,
             result.status.name,
             obj_path,
             phy_path,
             result.observed_values.get('observed_checksum', ''),
             result.observed_values.get('expected_checksum', ''),
             str(result.observed_values.get('observed_filesize', '')),
             str(result.observed_values.get('expected_filesize', ''))))
