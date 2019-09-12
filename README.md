# irods-consistency-check
Check consistency between iRODS resource in the catalog and the files on-disk.
The ichk command needs to be installed on the same machine as the iRODS resource holds its data.
It can run in two modes. In the resource mode every collection and data object will be checked if they are present on disk in the vault path.
When a data object has a registered checksum, this checksum will be compared to the file on disk.
It will output it's results in either a human-readable form or as CSV (Comma-separated values).

## Requirements
- iRODS >= v4.2.x
- Python 2.7 or 3.5+

## Installation
This project contains a setup.py file which supports both python 2.7 or python 3.5+ environments.
Installation is easiest with pip. Just run the following commands:

```bash
virtualenv --no-site-packages default
. default/bin/activate
pip install git+https://github.com/UtrechtUniversity/irods-consistency-check.git
```

When using a virtual environment, make sure that the iRODS system user has access to this environment.

## Usage
When the installation was successful, the ichk command will be available.
It extracts the credentials and iRODS settings from the iRODS environment file of the current user.
This environment file can be (re-)created with the iinit command.
This user should also have access to the files in the vault path directly.

The command line switches are displayed below:
```
 usage: ichk [-h] [-f FQDN] (-r RESOURCE | -v VAULT ) [-o OUTPUT]
             [-m {human,csv}] [-t TRUNCATE] [-T TIMEOUT] [-s COLLECTION] [-a]

 Check recursively if an iRods resource is consistent with its vault or vice
 versa

 optional arguments:
   -h, --help            show this help message and exit
   -f FQDN, --fqdn FQDN  FQDN of resource
   -r RESOURCE, --resource RESOURCE
                        iRODS path of resource
   -v VAULT, --vault VAULT
                         Physical path of the resource vault
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
   -s COLLECTION, --root-collection COLLECTION
                         Only check this collection and its subcollections, rather
                         than all collections.
```

You need to either supply a resource or a vault path, but not both.
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

The meaning of the fields in CSV output is:
1. Object type
2. Status code
3. Logical path
4. Vault path
5. Observed checksum value (field is empty for collections / directories, as well as for files / data objects with a size mismatch)
6. Expected checksum value (field is empty for collections / directories, as well as for files / data objects with a size mismatch)
7. Observed object size (field is empty for collections / directories)
8. Expected checksum value (field is empty for collections / directories)
