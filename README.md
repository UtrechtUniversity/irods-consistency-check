# irods-consistency-check
Check consistency between irods resource in the catalog and the files on-disk. The ichk command needs to be installed
on the same machine as the irods resource holds its data. It can run in two modes. In the resource mode every
collection and data object will be checked if they are present on disk in the vault path. When a data object
has a registered checksum, this checksum will be compared to the file on disk. 

## installation
This project contains a setup.py file which supports both python 2.7 or python 3.5+ environments. Installation is easiest
with pip. Just run the following command in the same directory as setup.py (The root of this repo):


`pip install .`

When using a virtual environment, make sure that the irods system user has access to this environment.

## usage

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
