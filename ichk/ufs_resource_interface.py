import base64
import errno
import hashlib
import os

from ichk.resource_interface import ResourceInterface
from ichk.status_codes import Status

class UFSResourceInterface(ResourceInterface):
    CHUNK_SIZE = 8192

    def check_object_exists(self, path):
        return self._check_exists(path)


    def check_coll_exists(self, path):
        return self._check_exists(path)


    def _check_exists(self, path):
        try:
            statinfo = os.stat(path)
        except OSError as e:
            if e.errno == errno.ENOENT:
                return Status.NOT_EXISTING
            elif e.errno == errno.EACCES:
                return Status.ACCESS_DENIED
            else:
                raise

        return Status.OK


    def get_size(self, path):
        return os.stat(path).st_size


    def get_checksum(self, path, checksumtype):
        if checksumtype == "md5":
            hsh = hashlib.md5()
        elif checksumtype == "sha2":
            hsh = hashlib.sha256()
        else:
            raise ValueError(f"Checksum type {checksumtype} not supported.")

        f = open(path, 'rb')

        while True:
           chunk = f.read(UFSResourceInterface.CHUNK_SIZE)
           if chunk:
               hsh.update(chunk)
           else:
               break

        if hsh.name == 'md5':
           return hsh.hexdigest()
        else:
           return base64.b64encode(hsh.digest()).decode('ascii')
