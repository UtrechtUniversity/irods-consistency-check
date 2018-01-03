# irods-consistency-check
Check consistency between irods resource in the catalog and the files on-disk. The ichk command needs to be installed
on the same machine as the irods resource holds its data. It can run in two modes. In the resource mode every
collection and data object will be checked if they are present on disk in the vault path. When a data object
has a registered checksum, this checksum will be compared to the file on disk. It will output it's results in either
a human-readable form or as csv (Comma-seperated values).

## installation
This project contains a setup.py file which supports both python 2.7 or python 3.5+ environments. Installation is easiest
with pip. Just run the following command in the same directory as setup.py (The root of this repo):


`pip install .`

When using a virtual environment, make sure that the irods system user has access to this environment.

## usage

When the installation was succesful, the ichk command will be available. It extracts the credentials and irods settings
from the irods environment file of the current user. This environment file can be (re-)created with the iinit command.
 This user should also have access to the files in the vault path directly. The commandline switches are displayed below:


```
 usage: ichk [-h] [-f FQDN] (-r RESOURCE | -v VAULT) [-o OUTPUT]
            [-m {human,csv}] [-t TRUNCATE]

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
```

You need to either supply a resource or a vault path, but not both. The fqdn (fully qualified domain name) defaults to the fqdn of the current machine.
When composable resources are used, the ichk command will scan for leaf resources starting from the given resource.

## return values

The objects that are checked are categorized as follows:
* COLLECTION
* DATAOBJECT
* DIRECTORY
* FILE

The result of the check are displayed with the following keywords:
* OK
* NOT EXISTING:  This object is found in the iRODS catalog, but is missing in the vault path.
* NOT REGISTERED:  This object is found on the disk, but is missing from the iRODS catalog.
* FILE SIZE MISMATCH:  The object has another file size than registered in the iRODS catalog.
* CHECKSUM MISMATCH:  This object does not have the same checksum as registered in the iRODS catalog.
* ACCESS DENIED:  The current user has no access to this object in the vault path.
* NO CHECKSUM:  There is no checksum registered in the iRODS catalog. This implies that file sizes do match.



