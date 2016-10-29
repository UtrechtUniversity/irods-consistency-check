"""Scan and check resource or vault"""

from __future__ import print_function
import sys
import os
import errno
from enum import Enum
import hashlib
import base64
from ichk.formatters import HumanFormatter, CSVFormatter
from irods.models import Resource, Collection, DataObject
import irods.exception as iexc


class Status(Enum):
    OK = 0
    NOT_EXISTING = 1        # File registered in iRODS but not found in vault
    NOT_REGISTERED = 2      # File found in vault but is not registered in iRODS
    FILE_SIZE_MISMATCH = 3  # File sizes do not match between database and vault
    CHECKSUM_MISMATCH = 4   # Checksums do not match between database and vault
    ACCESS_DENIED = 5       # This script was denied access to the file
    NO_CHECKSUM = 6         # iRODS has no checksum registered

class Check(object):

    def __init__(self, session, fqdn):
        self.fqdn = fqdn
        self.session = session

    def setformatter(self, output, fmt):
        """Use different formatters based on fmt Argument"""
        if fmt == "human":
            self.formatter = HumanFormatter(output)
        elif fmt == "csv":
            self.formatter = CSVFormatter(output)
        else:
            raise ValueError("Unknown formatter: {}".format(fmt))

    def get_resource(self, resource_name):
        try:
            resource = self.session.query(Resource).filter(Resource.name == resource_name).one()
        except iexc.NoResultFound:
            sys.exit("No result found for a resource named: {resource_path}".format(**locals()))
        self.resource = resource

    def get_resource_from_vault_path(self, vault_path):
        try:
            resource = self.session.query(Resource).filter(
                Resource.vault_path == vault_path).one()
        except iexc.NoResultFound:
            sys.exit("No result found for resource with vault path: {vault_path}".format(**locals()))
        self.resource = resource
        vault = os.path(vault_path)

    @property
    def vault(self):
        if self._vault:
            return self._vault
        else:
            return None

    @vault.setter
    def vault(self, vault_path):
        if os.path.exists(vault_path):
            self._vault = os.path.realpath(vault_path)
        else:
            sys.exit("Vault path {vault_path} does not exist".format(**locals()))

    def run(self):
        """Must be implemented by subclass"""
        raise NotImplementedError


class ResourceCheck(Check):
    """Starting from a Resource path. Check consistency of database"""

    def __init__(self, session, fqdn, resource_name):
        super(ResourceCheck, self).__init__(session, fqdn)
        self.resource_name = resource_name

    def run(self):
        print("Checking resource {resource_name} for consistency".format(resource_name=self.resource_name), file=sys.stderr)
        # Step 1:
        # Check if Resource is accessible for current user and get details
        self.get_resource(self.resource_name)
        # Step 2:
        # Check if associated physical path to the vault is accessible
        self.vault = self.resource[Resource.vault_path]

        self.formatter.head()
        # Step 3:
        # Recursively go over every collection, subcollection and data object
        # in the resource and do the following checks:
        # a) Does file or directory exist in vault?
        # b) If it is a file do the file sizes match with iRODS?
        # c) If it is a file with a checksum, do the checksums match?
        # Call the dataformatter for every result.
        query = self.session.query(Collection.id, Collection.name).filter(Resource.id == self.resource[Resource.id])
        results = query.all()
        collections = results.rows
        for collection in collections:
            self.check_collection(collection)

    def check_collection(self, collection):
        coll_id = collection[Collection.id]
        coll_name = collection[Collection.name]

        #todo build path in vault from collection name and check if it exists

        data_objects = self.session.query(DataObject).filter(Collection.id==coll_id).all().rows
        for data_object in data_objects:
            obj_name = data_object[DataObject.name]
            obj_path = coll_name + '/' + obj_name
            phy_path, status = self.check_data_object(data_object, obj_path)
            self.formatter.fmt(obj_path, phy_path, status)

    def check_data_object(self, data_object, obj_path):
        phy_path = data_object[DataObject.path]

        try:
            statinfo = os.stat(phy_path)
        except OSError as e:
            if e.errno == errno.ENOENT:
                return  obj_path, phy_path, Status.NOT_EXISTING
            elif e.errno == errno.EACCES:
                return phy_path, Status.ACCESS_DENIED
            else:
                raise

        # TODO: what about sparse files?
        data_object_size = data_object[DataObject.size]
        if data_object_size != statinfo.st_size:
            return phy_path, Status.FILE_SIZE_MISMATCH

        irods_checksum = data_object[DataObject.checksum]
        if not irods_checksum:
            return phy_path, Status.NO_CHECKSUM
        else:
            try:
                f = open(phy_path, 'rb')
            except OSError as e:
                if e.errno == errno.EACCES:
                    return phy_path, Status.ACCESS_DENIED
                else:
                    raise
            else:
                hsh  = hashlib.sha256()
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if chunk:
                        hsh.update(chunk)
                    else:
                        break
                phy_checksum = b.b64encode(hsh.digest())
            finally:
                f.close()
            if phy_checksum != irods_checksum:
                return phy_path, Status.CHECKSUM_MISMATCH

        return phy_path, Status.OK


class VaultCheck(Check):
    """Starting from a physical vault path check for consistency"""

    def __init__(self, session, fqdn, vault_path):
        super(VaultCheck, self).__init__(session, fqdn)
        self.vault_path = vault_path

    def run(self, session):
        self.session = session
        print("Checking vault at {path} for consistency".format(path=self.path), file=sys.stderr)
        # Step 1:
        # Check if the physical path is accessible for current user
        self.vault = self.vault_path
        # Step 2:
        # Check if associated resource is accessible
        self.get_resource_from_vault_path(self.vault_path)
        # Step 3:
        # Recursively go over every directory, subdirectory and file in the
        # vault and do the following checks:
        # a) Does the file or directory have an associated object in the
        # resource?
        # b) If it is a file do the file sizes match with iRODS?
        # c) If it is a file with a checksum, do the checksums match?
        # Call the dataformatter for every result.


