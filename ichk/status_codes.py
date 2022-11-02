from enum import Enum


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
    REPLICA_NOT_GOOD = 9    # Replica has a state other than GOOD_REPLICA
    UNKNOWN = 10            # Unknown status (e.g. collection presence on S3 resource)

    def __repr__(self):
        return self.name


class ReplicaStatus(Enum):
    STALE_REPLICA = 0
    GOOD_REPLICA = 1
    INTERMEDIATE_REPLICA = 2
    READ_LOCKED = 3
    WRITE_LOCKED = 4

    def __repr__(self):
        return self.name
