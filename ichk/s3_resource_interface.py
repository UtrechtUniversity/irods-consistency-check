import base64
import hashlib
import os

import boto3
import botocore.exceptions

from irods.models import Resource
import irods.exception as iexc

from ichk.resource_interface import ResourceInterface
from ichk.status_codes import Status

class S3ResourceInterface(ResourceInterface):
    CHUNK_SIZE = 8192


    def __init__(self, irods_session, resource_name):
        self.irods_session = irods_session
        self.resource_name = resource_name
        self.s3_hostname = self._get_s3_hostname(resource_name)
        (self.s3_accesskey, self.s3_secretkey) = self._get_s3_credentials(resource_name)
        self.s3_region = self._get_resource_context_param(resource_name, "S3_REGIONNAME")
        boto3_session = boto3.Session(aws_access_key_id = self.s3_accesskey.strip(),
                                   aws_secret_access_key = self.s3_secretkey.strip(),
                                   region_name = self.s3_region.strip())
        self.boto3_client = boto3_session.client('s3', endpoint_url="https://" + self.s3_hostname)


    def check_object_exists(self, path):
        bucket = self._get_bucket_name(path)
        key = self._get_key_name(path)
        try:
            self.boto3_client.head_object(Bucket=bucket, Key=key)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                return Status.NOT_EXISTING
            elif e.response['Error']['Code'] == "403":
                return Status.ACCESS_DENIED
            else:
                raise()

        return Status.OK


    def _get_bucket_name(self, path):
        return path.split("/")[1]


    def _get_key_name(self, path):
        return "Vault/" + "/".join(path.split("/")[3:])


    def check_coll_exists(self, path):
        # Collections do not exist separately from objects on S3 resources
        return Status.UNKNOWN


    def get_size(self, path):
        bucket = self._get_bucket_name(path)
        key = self._get_key_name(path)
        object = self.boto3_client.head_object(Bucket=bucket, Key=key)
        return object["ContentLength"]


    def get_checksum(self, path, checksumtype):
        if checksumtype == "md5":
            hsh = hashlib.md5()
        elif checksumtype == "sha2":
            hsh = hashlib.sha256()
        else:
            raise ValueError(f"Checksum type {checksumtype} not supported.")

        bucket = self._get_bucket_name(path)
        key = self._get_key_name(path)

        with self.boto3_client.get_object(Bucket=bucket, Key=key)["Body"] as stream:
            while True:
               chunk = stream.read(S3ResourceInterface.CHUNK_SIZE)
               if chunk:
                   hsh.update(chunk)
               else:
                   break

        if hsh.name == 'md5':
           return hsh.hexdigest()
        else:
           return base64.b64encode(hsh.digest()).decode('ascii')


    def _get_s3_hostname(self, resource_name):
        return self._get_resource_context_param(resource_name,
            "S3_DEFAULT_HOSTNAME")


    def _get_s3_credentials(self, resource_name):
        authfile = self._get_resource_context_param(resource_name,
            "S3_AUTH_FILE")

        if authfile is None:
            raise Exception(f"Could not find auth file config for S3 resource {resource_name}")

        with open(authfile, "r") as f:
            accesskey = f.readline()
            secretkey = f.readline()
            return (accesskey, secretkey)


    def _get_resource_context_param(self, resource_name, param):
        context = self._get_resource_context(resource_name)
        for kvpair in context.split(";"):
            (k, v) = kvpair.split("=")
            if param == k:
                return v
        return None


    def _get_resource_context(self, resource_name):
        try:
            resource = self.irods_session.query(Resource).filter(
                Resource.name == resource_name).one()
        except iexc.NoResultFound:
            return None
        return resource[Resource.context]
