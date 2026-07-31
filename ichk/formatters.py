"""Formatters for output of checks"""

import base64

from ichk import check


class Formatter(object):

    def __init__(self, output, **options):
        self.output = output
        self.checksum_format = options.get("checksum_format", "irods")

    def _format_checksum(self, checksum):
        def get_checksum_value(c):
            if checksum.startswith("md5:"):
                return c[4:]
            elif checksum.startswith("sha2:"):
                return c[5:]
            else:
                return c

        def get_checksum_type(c):
            if c.startswith("md5:"):
                return "md5"
            elif c.startswith("sha2:"):
                return "sha2"
            else:
                return "unknown"

        if checksum in ["", "N/A (checksum verification disabled)"]:
            return checksum

        if self.checksum_format == "irods":
            if checksum.startswith("md5:"):
                return get_checksum_value(checksum)
            else:
                return checksum
        elif self.checksum_format == "irods-short":
            return get_checksum_value(checksum)
        elif self.checksum_format == "hex":
            checksum_type = get_checksum_type(checksum)
            checksum_value = base64.b64decode(get_checksum_value(checksum)).hex()
            return f"{checksum_type}:{checksum_value}"
        elif self.checksum_format == "hex-short":
            return base64.b64decode(get_checksum_value(checksum)).hex()
        else:
            raise NotImplementedError("Cannot format checksum for format " + self.checksum_format)

    def head(self):
        raise NotImplementedError

    def __call__(self):
        raise NotImplementedError


class HumanFormatter(Formatter):

    name = 'human'
    options = ['truncate']
    template = """----
Type: {obj_type}
Resource: {resource}
iRODS path: {obj_path}
Physical path: {phy_path}
Status: {status}
Replica status: {replica_status}
"""

    def __init__(self, output=None, checksum_format="irods", truncate=None):
        if truncate:
            # TODO: write routine to check column width of active terminal
            self.truncate = 179
        else:
            self.truncate = None
        super(HumanFormatter, self).__init__(output=output, checksum_format=checksum_format)

    def head(self):
        print("Results of consistency check\n\n", file=self.output)

    def __call__(self, result):
        obj_type = result.obj_type.name

        if result.obj_type in (check.ObjectType.DATAOBJECT,
                               check.ObjectType.FILE):
            resource = result.resource
        else:
            resource = "N/A"

        status = result.status.name
        replica_status = result.replica_status

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
            printl("Expected checksum: " + self._format_checksum(values['expected_checksum']))
            printl("Observed checksum: " + self._format_checksum(values['observed_checksum']))

        printl("")


class CSVFormatter(Formatter):
    name = 'csv'
    options = []

    def __init__(self, output=None, checksum_format="irods"):
        super(CSVFormatter, self).__init__(output=output, checksum_format=checksum_format)

        import csv
        self.writer = csv.writer(
            self.output, dialect=csv.excel)

    def head(self):
        self.writer.writerow(('Type', 'Status', 'Replica status', 'iRODS Path', 'Physical Path',
                              'Observed checksum', 'Expected checksum',
                              'Observed size', 'Expected size', 'Resource'))

    def __call__(self, result):
        obj_path = result.obj_path
        phy_path = result.phy_path

        if result.obj_type in (check.ObjectType.DATAOBJECT,
                               check.ObjectType.FILE):
            resource = result.resource
        else:
            resource = ""

        self.writer.writerow(
            (result.obj_type.name,
             result.status.name,
             result.replica_status,
             obj_path,
             phy_path,
             self._format_checksum(result.observed_values.get('observed_checksum', '')),
             self._format_checksum(result.observed_values.get('expected_checksum', '')),
             str(result.observed_values.get('observed_filesize', '')),
             str(result.observed_values.get('expected_filesize', '')),
             resource))
