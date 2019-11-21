from enum import Enum


class Status(Enum):
    OK = 0
    NOT_EXISTING = 1        # File registered in iRODS but not found in vault
    NOT_REGISTERED = 2      # File found in vault but is not registered in iRODS
    FILE_SIZE_MISMATCH = 3  # File sizes do not match between database and vault
    CHECKSUM_MISMATCH = 4   # Checksums do not match between database and vault
    ACCESS_DENIED = 5       # This script was denied access to the file
    NO_CHECKSUM = 6         # iRODS has no checksum registered
    NO_LOCAL_REPLICA = 7    # No replica of data object present on server (object list check)
    NOT_FOUND = 8           # Object not found in iRODS (object list check)
    REPLICA_IS_STALE = 9    # Replica is stale

    def __repr__(self):
        return self.name


class ObjectType(Enum):
    COLLECTION = 0
    DATAOBJECT = 1
    FILE = 2
    DIRECTORY = 3

