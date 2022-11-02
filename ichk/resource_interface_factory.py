from irods.models import Resource
import irods.exception as iexc

from ichk.s3_resource_interface import S3ResourceInterface
from ichk.ufs_resource_interface import UFSResourceInterface


class ResourceInterfaceFactory:
    def __init__(self, session):
        self.resource_interface_cache = dict()
        self.session = session


    def get_resource_interface(self, resource_name):
        if resource_name in self.resource_interface_cache:
            return self.resource_interface_cache.get(resource_name)

        resource_type = self._get_resource_type(resource_name)
        if resource_type  == "unixfilesystem":
            result = UFSResourceInterface()
            self.resource_interface_cache[resource_name] = result
            return result
        elif resource_type == "s3":
            result = S3ResourceInterface(self.session, resource_name)
            self.resource_interface_cache[resource_name] = result
            return result
        elif resource_type is None:
            return None
        else:
            raise ValueError(f"Resource type {resource_type} not supported.")


    def _get_resource_type(self, resource_name):
        try:
            resource = self.session.query(Resource).filter(
                Resource.name == resource_name).one()
        except iexc.NoResultFound:
            return None
        return resource[Resource.type]
