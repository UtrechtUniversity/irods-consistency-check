"""Formatters for output of checks"""

from __future__ import print_function
import sys

class Formatter(object):

    PY2 = (sys.version_info.major == 2)

    def __init__(self, output, show_size_checksum, **options):
        self.output = output
        self.show_size_checksum = show_size_checksum

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

    def __init__(self, output=None, show_size_checksum = False, truncate=None):
        if truncate:
            # TODO: write routine to check column width of active terminal
            self.truncate = 179
        else:
            self.truncate = None
        super(HumanFormatter, self).__init__(output=output, show_size_checksum = show_size_checksum)

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

        print(self.template.format(**locals()),
              file=self.output)

        def printl(message):
            print(message, file=self.output)

        if self.show_size_checksum:
            values = result.observed_values

            def printl(message):
                print(message, file=self.output)

            if ( 'expected_filesize' in values and
                 'observed_filesize' in values and
                  values['observed_filesize'] != values['expected_filesize'] ):
                    printl("Expected size: " + values['expected_filesize'])
                    printl("Observed size: " + values['observed_filesize'])

            if ( 'expected_checksum' in values and
                 'observed_checksum' in values and
                  values['observed_checksum'] != values['expected_checksum'] ):
                    printl("Expected checksum: " + values['expected_checksum'])
                    printl("Observed checksum: " + values['observed_checksum'])

        printl("")

class CSVFormatter(Formatter):
    name = 'csv'
    options = []

    def __init__(self, output=None, show_size_checksum=False):
        super(CSVFormatter, self).__init__(output=output, show_size_checksum=show_size_checksum)

        import csv
        self.writer = csv.writer(
            self.output, dialect=csv.excel)

    def head(self):
        self.writer.writerow(('Type', 'Status', 'iRODS Path', 'Physical Path'))

    def __call__(self, result):
        if self.PY2:
            # python 2 defaults to ASCII encoding, enforce UTF-8
            obj_path = result.obj_path.encode('utf-8')
            phy_path = result.phy_path.encode('utf-8')
        else:
            obj_path = result.obj_path
            phy_path = result.phy_path

        def if_defined(dct,index):
            if index in dct and dct[index] != None:
                return dct[index]
            else:
                return ""

        if self.show_size_checksum:
            self.writer.writerow(
                (result.obj_type.name,
                 result.status.name,
                 obj_path,
                 phy_path,
                 if_defined(result.observed_values, 'observed_checksum'),
                 if_defined(result.observed_values, 'expected_checksum'),
                 if_defined(result.observed_values, 'observed_filesize'),
                 if_defined(result.observed_values, 'expected_filesize')))
        else:
            self.writer.writerow(
                (result.obj_type.name,
                 result.status.name,
                 obj_path,
                 phy_path))

