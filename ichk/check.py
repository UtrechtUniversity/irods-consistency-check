"""Scan and check resource or vault"""

from __future__ import print_function
import sys
import os
import errno
from enum import Enum
from collections import namedtuple
from itertools import chain
import hashlib
import base64
from ichk.formatters import Formatter
from irods.column import Like
from irods.data_object import irods_dirname, irods_basename
from irods.models import Resource, Collection, DataObject
import irods.exception as iexc

CHUNK_SIZE = 8192
PY2 = (sys.version_info.major == 2)


class Status(Enum):
    OK = 0
    NOT_EXISTING = 1        # File registered in iRODS but not found in vault
    NOT_REGISTERED = 2      # File found in vault but is not registered in iRODS
    FILE_SIZE_MISMATCH = 3  # File sizes do not match between database and vault
    CHECKSUM_MISMATCH = 4   # Checksums do not match between database and vault
    ACCESS_DENIED = 5       # This script was denied access to the file
    NO_CHECKSUM = 6         # iRODS has no checksum registered
    NO_LOCAL_REPLICA = 7    # No replica of data object present on server
                            # (object list check)
    NOT_FOUND = 8           # Object not found in iRODS (object list check)
    REPLICA_IS_STALE = 9    # Replica is stale

    def __repr__(self):
        return self.name


class ObjectType(Enum):
    COLLECTION = 0
    DATAOBJECT = 1
    FILE = 2
    DIRECTORY = 3


Result = namedtuple(
    'Result',
    'obj_type obj_path phy_path status observed_values resource')


def on_disk(path):

    try:
        os.stat(path)
    except OSError as e:
        if e.errno == errno.ENOENT:
            return Status.NOT_EXISTING
        elif e.errno == errno.EACCES:
            return Status.ACCESS_DENIED
        else:
            raise

    return Status.OK


class ObjectChecker(object):

    def __init__(self, data_object, phy_path):
        self.data_object = data_object
        self.phy_path = phy_path
        self._statinfo = None

    def get_obj_name(self):
        if PY2:
            return "{}/{}".format(
                self.data_object[Collection.name].encode('utf-8'),
                self.data_object[DataObject.name].encode('utf-8')
            )
        else:
            return "{}/{}".format(
                self.data_object[Collection.name],
                self.data_object[DataObject.name]
            )

    def get_result(self):
        status = self.exists_on_disk()
        observed_values = {}

        if status == Status.OK:
            # File exists on disk and is accessible
            status, observed_filesizes = self.compare_filesize()
            observed_values.update(observed_filesizes)
            if status == Status.OK:
                status, observed_checksums = self.compare_checksums()
                observed_values.update(observed_checksums)

            if self.data_object[DataObject.replica_status] == "1":
                # Replica in a good state (i.e. not stale)
                pass
            elif self.data_object[DataObject.replica_status] == "0":
                # Replica is stale. Override status message, but keep
                # observed size / checksum values intact, since they could
                # still be useful.
                status = Status.REPLICA_IS_STALE
            else:
                # Note: once https://github.com/irods/irods/issues/4343 has been implemented, we'll
                # need to add a state for dirty data objects.
                raise ValueError("Unknown replica state {} for data object {}".format(
                    self.data_object[DataObject.replica_status], self.get_obj_name()))

        return Result(ObjectType.DATAOBJECT, self.get_obj_name(),
                      self.phy_path, status, observed_values, self.data_object[Resource.name])

    @property
    def statinfo(self):
        if self._statinfo:
            return self._statinfo
        try:
            statinfo = os.stat(self.phy_path)
        except OSError as e:
            if e.errno == errno.ENOENT:
                statinfo = Status.NOT_EXISTING
            elif e.errno == errno.EACCES:
                statinfo = Status.ACCESS_DENIED
            else:
                raise

        self._statinfo = statinfo
        return statinfo

    def exists_on_disk(self):
        if isinstance(self.statinfo, Status):
            return self.statinfo
        return Status.OK

    def compare_filesize(self):
        # TODO: what about sparse files?
        data_object_size = self.data_object[DataObject.size]
        if isinstance(self.statinfo, Status):
            return self.statinfo, {}

        info = {
            'expected_filesize': data_object_size,
            'observed_filesize': self.statinfo.st_size}

        if data_object_size != self.statinfo.st_size:
            return Status.FILE_SIZE_MISMATCH, info

        return Status.OK, info

    def compare_checksums(self):
        irods_checksum = self.data_object[DataObject.checksum]
        info = {}
        if not irods_checksum:
            return Status.NO_CHECKSUM, info

        try:
            f = open(self.phy_path, 'rb')
        except OSError as e:
            if e.errno == errno.EACCES:
                return Status.ACCESS_DENIED, info
            else:
                raise
        else:
            # iRODS returns sha256 checksums as base64 encoded string of
            # the hash prefixed with sha2 and seperated
            # by a colon, ':'.
            # md5 checksums are not prefixed and not base64 encoded.
            if irods_checksum.startswith("sha2:"):
                irods_checksum = irods_checksum[5:]
                hsh = hashlib.sha256()
            else:
                hsh = hashlib.md5()

            while True:
                chunk = f.read(CHUNK_SIZE)
                if chunk:
                    hsh.update(chunk)
                else:
                    break

            if hsh.name == 'md5':
                phy_checksum = hsh.hexdigest()
            else:
                phy_checksum = base64.b64encode(hsh.digest()).decode('ascii')
            f.close()

        info = {
            'expected_checksum': irods_checksum,
            'observed_checksum': phy_checksum}

        if phy_checksum != irods_checksum:
            return Status.CHECKSUM_MISMATCH, info

        return Status.OK, info


class Check(object):

    def __init__(self, session, fqdn, root_collection):
        self.fqdn = fqdn
        self.session = session
        if root_collection is not None:
            found_collection = (self.session.query(Collection.id, Collection.name)
                                .filter(Collection.name == root_collection)
                                .get_results())
            if len(list(found_collection)) != 1:
                print("Error: root collection {} not found.".format(root_collection),
                        file=sys.stderr)
                sys.exit(1)

        self.root_collection = root_collection

    def setformatter(self, output=None, fmt=None, **options):
        """Use different formatters based on fmt Argument"""
        if (output is None) or (fmt is None):
            raise ValueError(
                "Check.setformatter needs an output and fmt argument")

        formatters = Formatter.__subclasses__()
        for formatter in formatters:
            if formatter.name == fmt:
                self.formatter = formatter(output, **options)
                break
        else:
            raise ValueError("Unknown formatter: {}".format(fmt))

    def get_resource(self, resource_name):
        try:
            resource = self.session.query(Resource).filter(
                Resource.name == resource_name).one()
        except iexc.NoResultFound:
            resource = None
        return resource

    def get_local_ufs_resources(self, fqdn):
        try:
            return self.session.query(Resource).filter(Resource.location == fqdn).filter(
                Resource.type == "unixfilesystem").get_results()
        except iexc.NoResultFound:
            return None

    def get_resource_from_phy_path(self, phy_path):
        try:
            resource = (self.session.query(Resource)
                        .filter(Resource.vault_path == phy_path)
                        .filter(Resource.location == self.fqdn)
                        .one()
                        )
        except iexc.NoResultFound:
            resource = None
        return resource

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
            sys.exit("Vault path {vault_path} does not exist"
                     .format(**locals()))

    def find_root(self, resource):
        ancestors = []

        def climb(resource):
            parent = resource[Resource.parent]
            if parent is None:
                print("Root resource is {}".format(resource[Resource.name]),
                      file=sys.stderr)
                return resource
            else:
                ancestor = (
                    self.session.query(Resource.id, Resource.name)
                    .filter(Resource.id == parent)
                    .one()
                )
                ancestors.append(ancestor[Resource.name])
                return climb(self.get_resource(ancestor[Resource.name]))

        root = climb(resource)
        ancestors.reverse()
        return root, ancestors

    def find_leaves(self, resource, ancestors=None):
        """Find leaf nodes of the resource hierarchy. These are the storage
        resources containing the actual data."""

        if ancestors is None:
            ancestors = []
        to_visit = [(resource, ancestors)]

        while len(to_visit) > 0:
            node, ancestors = to_visit.pop(0)
            children = node[Resource.children]
            if children:
                ancestors_of_children = ancestors + [node[Resource.name]]
                for child in (c.strip("{}") for c in children.split(";")):
                    child_resource = self.get_resource(child)
                    to_visit.append((child_resource, ancestors_of_children))

            elif node[Resource.location] == self.fqdn:
                print("{} is a storage resource with vault path {}"
                      .format(node[Resource.name], node[Resource.vault_path]),
                      file=sys.stderr)
                hiera = ancestors + [node[Resource.name]]
                yield node, hiera

            else:
                print("Storage resource {} not on fqdn {}, but {}"
                      .format(resource[Resource.name], self.fqdn,
                              resource[Resource.location]),
                      file=sys.stderr)

    def run(self):
        """Must be implemented by subclass"""
        raise NotImplementedError


class ResourceCheck(Check):
    """Starting from a Resource path. Check consistency of database"""

    def __init__(self, session, fqdn, resource_name,
                 root_collection, all_local_resources):
        super(ResourceCheck, self).__init__(session, fqdn, root_collection)
        self.resource_name = resource_name
        self.all_local_resources = all_local_resources

    def run(self):
        if self.all_local_resources:

            resource_data = self.get_local_ufs_resources(self.fqdn)
            if resource_data is None:
                print(
                    "Error: no local unixfilesystem resources found.",
                    file=sys.stderr)
                sys.exit(1)
            resources = list(resource_data)
            resources.sort(key=lambda r: r[Resource.name])

            resource_number = 0
            for resource in resources:
                self.process_resource(resource, resource_number == 0)
                resource_number += 1
        else:
            resource = self.get_resource(self.resource_name)
            if resource is None:
                print("Error: resource {} not found".format(self.resource_name),
                        file=sys.stderr)
                sys.exit(1)
            self.process_resource(resource, True)

    def process_resource(self, resource, print_header):
        resource_name = resource[Resource.name]

        print("Checking resource {} for consistency"
              .format(resource_name), file=sys.stderr)

        if print_header:
            self.formatter.head()

        root, ancestors = self.find_root(resource)
        for leaf, hiera in self.find_leaves(resource, ancestors):
            resource_hierarchy = ";".join(hiera)
            self.check_collections(
                leaf[Resource.name], resource_hierarchy, leaf[Resource.vault_path])

    def collections_in_root(self, resource_name):
        """Returns a generator for all the Collections in the root resource"""
        if self.root_collection is None:
            return (self.session.query(Collection.id, Collection.name)
                    .filter(Resource.name == resource_name)
                    .get_results()
                    )
        else:
            generator_collection = (self.session.query(Collection.id, Collection.name)
                                    .filter(Resource.name == resource_name)
                                    .filter(Collection.name == self.root_collection)
                                    .get_results()
                                    )
            generator_subcollections = (self.session.query(Collection.id, Collection.name)
                                        .filter(Resource.name == resource_name)
                                        .filter(Like(Collection.name, self.root_collection + "/%%"))
                                        .get_results()
                                        )
            return chain(generator_collection, generator_subcollections)

    def data_objects_in_collection(self, coll_id, resource_hierarchy):
        """Returns a generator for all data objects in a collection"""
        return (self.session.query(DataObject, Collection.name, Resource.name)
                .filter(Collection.id == coll_id)
                .filter(DataObject.resc_hier == resource_hierarchy)
                .get_results()
                )

    def convert_collection_name_to_path(
            self, coll_name, vault_path, zone_name):
        prefix = "/" + zone_name
        return coll_name.replace(prefix, vault_path, 1)

    def check_collections(self, resource_name, resource_hierarchy, vault_path):
        """Check every collection within the target resource for consistency"""

        for coll in self.collections_in_root(resource_name):
            coll_id = coll[Collection.id]
            coll_name = coll[Collection.name]
            coll_path = self.convert_collection_name_to_path(
                coll_name, vault_path, self.session.zone)
            status_on_disk = on_disk(coll_path)
            result = Result(obj_type=ObjectType.COLLECTION,
                            obj_path=coll_name,
                            phy_path=coll_path,
                            status=status_on_disk,
                            observed_values={},
                            resource=None)
            self.formatter(result)
            if status_on_disk != Status.OK:
                continue

            if PY2:
                print("Checking data objects of collection {} in hierarchy: {}"
                      .format(coll_name.encode('utf-8'), resource_hierarchy),
                      file=sys.stderr)
            else:
                print("Checking data objects of collection {} in hierarchy: {}"
                      .format(coll_name, resource_hierarchy),
                      file=sys.stderr)

            for data_object in self.data_objects_in_collection(
                    coll_id, resource_hierarchy):
                phy_path = data_object[DataObject.path]
                object_checker = ObjectChecker(data_object, phy_path)
                result = object_checker.get_result()
                self.formatter(result)


class VaultCheck(Check):
    """Starting from a physical vault path check for consistency"""

    def __init__(self, session, fqdn, vault_path,
                 root_collection, all_local_resources):
        super(VaultCheck, self).__init__(session, fqdn, root_collection)
        self.all_local_resources = all_local_resources
        self.vault_path = vault_path

    def run(self):
        if self.all_local_resources:

            resource_data = self.get_local_ufs_resources(self.fqdn)
            if resource_data is None:
                print(
                    "Error: no local unixfilesystem resources found.",
                    file=sys.stderr)
                sys.exit(1)
            resources = list(resource_data)
            resources.sort(key=lambda r: r[Resource.name])

            vault_number = 0
            for resource in resources:
                self.process_vault(resource, vault_number == 0)
                vault_number += 1
        else:
            resource = self.get_resource_from_phy_path(self.vault_path)
            if resource is None:
                print("Error: unable to find resource with vault path {}.".format(self.vault_path),
                        file=sys.stderr)
                sys.exit(1)
            self.process_vault(resource, True)

    def process_vault(self, resource, print_header):
        vault_path = resource[Resource.vault_path]

        print("Checking vault at {} for consistency"
              .format(vault_path),
              file=sys.stderr)

        if print_header:
            self.formatter.head()

        if resource is None:
            sys.exit("Error: could not find iRODS resource with vault path {}"
                     .format(vault_path))

        root, ancestors = self.find_root(resource)
        hiera = ancestors + [resource[Resource.name]]
        resource_hierarchy = ";".join(hiera)

        if self.root_collection is None:
            path_to_walk = vault_path
        else:
            path_to_walk = self.root_collection.replace(
                "/" + root[Resource.zone_name], vault_path, 1)

        for dirname, subdirs, filenames in os.walk(path_to_walk):

            for subdir in subdirs:
                phy_path = os.path.join(dirname, subdir)
                coll_name = self.convert_collection_path_to_name(
                    phy_path, vault_path, self.session.zone)
                collection, status = self.get_collection(coll_name, resource[Resource.name])
                if collection:
                    obj_path = collection[Collection.name]
                else:
                    obj_path = "UNKNOWN"
                result = Result(
                    ObjectType.DIRECTORY, obj_path, phy_path, status, {}, None)

                self.formatter(result)

            for filename in filenames:
                phy_path = os.path.join(dirname, filename)
                data_object, status = self.get_data_object(
                    phy_path, resource_hierarchy)
                observed_values = {}

                if data_object is None:
                    obj_path = "UNKNOWN"
                    result = Result(
                        ObjectType.FILE,
                        obj_path,
                        phy_path,
                        status,
                        observed_values,
                        None)
                else:
                    object_checker = ObjectChecker(data_object, phy_path)
                    result = object_checker.get_result()
                    # Override object type in Result - should be FILE
                    result = Result(
                        ObjectType.FILE,
                        result.obj_path,
                        result.phy_path,
                        result.status,
                        result.observed_values,
                        result.resource)
                self.formatter(result)

    def convert_collection_path_to_name(self, phy_path, vault_path, zone_name):
        prefix = '/' + zone_name
        return phy_path.replace(vault_path, prefix, 1)

    def get_collection(self, coll_name, resource_name):
        try:
            collection = (
                self.session.query(Collection, Resource.id)
                .filter(Collection.name == coll_name)
                .filter(Resource.name == resource_name)
                .one()
            )
        except iexc.NoResultFound:
            collection = None
            status = Status.NOT_REGISTERED
        else:
            status = Status.OK

        return collection, status

    def get_data_object(self, phy_path, resource_hierarchy):
        try:
            result = (
                self.session.query(DataObject, Collection.name, Resource.name)
                .filter(DataObject.path == phy_path)
                .filter(DataObject.resc_hier == resource_hierarchy)
                .first()
            )
        except iexc.NoResultFound:
            status = Status.NOT_REGISTERED
            data_object = None
        else:
            data_object = result
            if data_object is None:
                status = Status.NOT_REGISTERED
            else:
                status = Status.OK

        return data_object, status


class ObjectListCheck(Check):
    """Check all local replicas of a list of objects"""

    def __init__(self, session, fqdn, object_list_file):
        super(ObjectListCheck, self).__init__(session, fqdn, None)
        self.object_list_file = object_list_file
        self.resource_locality_lookup = self._gen_resource_locality_lookup()

    def _gen_resource_locality_lookup(self):
        result = {}
        resources = self.session.query(Resource.name, Resource.location)
        for resource in resources:
            result[resource[Resource.name]
                   ] = resource[Resource.location] == self.fqdn
        return result

    def _is_local_resource(self, resource_name):
        return self.resource_locality_lookup[resource_name]

    def _check_object(self, object_name):

        def _not_found():
            result = Result(ObjectType.DATAOBJECT, object_name,
                            "", Status.NOT_FOUND, {}, None)
            self.formatter(result)
            return

        try:
            collection = self.session.collections.get(
                irods_dirname(object_name))
            objects = self.session.query(DataObject, Collection.name, Resource.name).filter(
                DataObject.name == irods_basename(object_name)).filter(
                DataObject.collection_id == collection.id).all()
        except (iexc.NoResultFound, iexc.CollectionDoesNotExist):
            _not_found()
            return

        if len(objects) == 0:
            _not_found()
            return

        results_found = False

        for object in objects:
            if self._is_local_resource(object[DataObject.resource_name]):
                object_checker = ObjectChecker(object, object[DataObject.path])
                result = object_checker.get_result()
                results_found = True

        if not results_found:
            result = Result(ObjectType.DATAOBJECT, object_name,
                            "", Status.NO_LOCAL_REPLICA, {}, None)

        self.formatter(result)

    def run(self):
        print("Checking object list {} for consistency of local replicas"
              .format(self.object_list_file.name),
              file=sys.stderr)

        self.formatter.head()

        for line in self.object_list_file:
            self._check_object(line.rstrip('\n'))
