# irods-consistency-check
ichk (iRODS consistency check) performs a consistency check between data object information in
the iCAT catalog and files in unixfilesystem vaults on an iRODS server. It must be installed locally on the
server.

It can run in three modes:
- In resource mode, a consistency check is performed for every registered data object on a local resource.
- In vault mode, a local unixfilesystem vault is scanned. A consistency check is performed for every file in the vault.
  This mode will detect files that are present in the vault, but not registered in the iCAT database, whereas such files
  are ignored in resource mode.
- In object list mode, a list of data objects is read from a file. A consistency check is performed for all local
  replicas of these data objects. This mode can be used to check whether an iRODS server has valid replicas
  of a particular set of data objects.

Ichk can use either a human-readable output format, or comma-separated values (CSV).

## Requirements
- iRODS >= v4.2.x
- Python 3.5+

## Installation
This project contains a setup.py file which supports Python 3.5+ environments.
Installation is easiest with pip. Just run the following commands:

```bash
virtualenv --no-site-packages default
. default/bin/activate
pip3 install git+https://github.com/UtrechtUniversity/irods-consistency-check.git@v1.0.0
```

When using a virtual environment, make sure that the iRODS system user has access to this environment.

## Usage
When the installation was successful, the ichk command will be available.
It extracts the credentials and iRODS settings from the iRODS environment file of the current user.
This environment file can be (re-)created with the iinit command.
This user should also have access to the files in the vault path directly.

The command line switches are displayed below:
```
usage: ichk [-h] [-f FQDN] (-r RESOURCE | -v VAULT | -l DATA_OBJECT_LIST_FILE)
            [-o OUTPUT] [-m {human,csv}] [-t TRUNCATE] [-T TIMEOUT]
            [-s ROOT_COLLECTION]

Check consistency between iRODS data objects and files in vaults.

optional arguments:
  -h, --help            show this help message and exit
  -f FQDN, --fqdn FQDN  FQDN of resource
  -r RESOURCE, --resource RESOURCE
                        iRODS path of resource
  -v VAULT, --vault VAULT
                        Physical path of the resource vault
  -l DATA_OBJECT_LIST_FILE, --data-object-list DATA_OBJECT_LIST_FILE
                        Check replicas of a list of data objects on this
                        server.
  -o OUTPUT, --output OUTPUT
                        Write output to file
  -m {human,csv}, --format {human,csv}
                        Output format
  -t TRUNCATE, --truncate TRUNCATE
                        Truncate the output to the width of the console
  -T TIMEOUT, --timeout TIMEOUT
                        Sets the maximum amount of seconds to wait for server
                        responses, default 600. Increase this to account for
                        longer-running queries.
  -s ROOT_COLLECTION, --root-collection ROOT_COLLECTION
                        Only check a particular collection and its
                        subcollections.

```

You need to supply either a resource, a vault path or a data object list.
The FQDN (fully qualified domain name) defaults to the FQDN of the current machine.
When composable resources are used, the ichk command will scan for leaf resources starting from the given resource.

## Output

The objects that are checked are categorized as follows:
* COLLECTION
* DATAOBJECT
* DIRECTORY
* FILE

These status codes can be used to represent the result of the check:
* OK
* NOT EXISTING:  This object is found in the iRODS catalog, but is missing in the vault path.
* NOT REGISTERED:  This object is found on the disk, but is missing from the iRODS catalog.
* FILE SIZE MISMATCH:  The object has another file size than registered in the iRODS catalog.
* CHECKSUM MISMATCH:  This object does not have the same checksum as registered in the iRODS catalog.
* ACCESS DENIED:  The current user has no access to this object in the vault path.
* NO CHECKSUM:  There is no checksum registered in the iRODS catalog. This implies that file sizes do match.
* NO_LOCAL_REPLICA: No replica of data object present on server (only used for object list check)
* NOT_FOUND: Object name not found in iRODS (only used for object list check)
* REPLICA_IS_STALE : Replica is stale (i.e. out of date)


The meaning of the fields in CSV output is:
1. Object type
2. Status code
3. Logical path
4. Vault path
5. Observed checksum value (field is empty for collections / directories, as well as for files / data objects with a size mismatch)
6. Expected checksum value (field is empty for collections / directories, as well as for files / data objects with a size mismatch)
7. Observed file size (field is empty for collections / directories)
8. Expected file size (field is empty for collections / directories)
9. Resource name
