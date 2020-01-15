"""Check consistency between iRODS data objects and files in vaults."""
from __future__ import print_function
import sys
import os
import argparse
import json
from getpass import getpass
from ichk import check
from irods.session import iRODSSession
from irodsutils import password_obfuscation


def entry():
    """Use as entry_point in setup.py"""

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("-f", "--fqdn",
                        help="FQDN of resource")
    scan_type = parser.add_mutually_exclusive_group(required=True)
    scan_type.add_argument("-r", "--resource",
                           help="iRODS path of resource")
    scan_type.add_argument("-v", "--vault",
                           help="Physical path of the resource vault")
    scan_type.add_argument("-l", "--data-object-list", dest='data_object_list_file', default=None,
                           type=argparse.FileType('r'),
                           help="Check replicas of a list of data objects on this server.")
    scan_type.add_argument("--all-local-resources", action="store_true", default=False,
                           help="Scan all unixfilesystem resources on this server")
    scan_type.add_argument("--all-local-vaults", action="store_true", default=False,
                           help="Scan all vaults of unixfilesystem resources on this server")
    parser.add_argument("-o", "--output", type=argparse.FileType('w'),
                        help="Write output to file")
    parser.add_argument("-m", "--format", dest="fmt", default='human',
                        help="Output format", choices=['human', 'csv'])
    parser.add_argument("-t", "--truncate", default=False,
                        help="Truncate the output to the width of the console")
    parser.add_argument("-T", "--timeout", default=10 * 60, type=int,
                        help="Sets the maximum amount of seconds to wait for server responses"
                        + ", default 600. Increase this to account for longer-running queries.")
    parser.add_argument("-s", "--root-collection", dest='root_collection', default=None,
                        help="Only check a particular collection and its subcollections.")

    args = parser.parse_args()

    if args.root_collection is not None and args.data_object_list_file is not None:
        print("Error: the --root-collection / -s and the --data-object-list / -l option can't be combined.")
        sys.exit(1)

    if args.fqdn:
        pass
    else:
        import socket
        args.fqdn = socket.getfqdn()

    if args.root_collection is not None:
        args.root_collection = args.root_collection.rstrip("/")

    session = setup_session()

    session.connection_timeout = args.timeout

    try:
        run(session, args)
    except:
        raise
    finally:
        session.cleanup()


def setup_session():
    """Use irods environment files to configure a iRODSSession"""

    env_json = os.path.expanduser("~/.irods/irods_environment.json")
    try:
        with open(env_json, 'r') as f:
            irods_env = json.load(f)
    except OSError:
        sys.exit("Can not find or access {}. Please use iinit".format(env_json))

    irodsA = os.path.expanduser("~/.irods/.irodsA")
    try:
        with open(irodsA, "r") as r:
            scrambled_password = r.read()
            password = password_obfuscation.decode(scrambled_password)
    except OSError:
        print(
            "Could not open {} .".format(scrambled_password),
            file=sys.stderr
        )
        password = getpass(prompt="Please provide your irods password:")

    print(
        "Connecting to irods at {irods_host}:{irods_port} as {irods_user_name}"
        .format(**irods_env), file=sys.stderr
    )

    session = iRODSSession(
        password=password,
        **irods_env
    )

    return session


def run(session, args):
    if args.resource:
        executor = check.ResourceCheck(
            session, args.fqdn, args.resource, args.root_collection, False)
    elif args.vault:
        executor = check.VaultCheck(
            session, args.fqdn, args.vault, args.root_collection, False)
    elif args.all_local_resources:
        executor = check.ResourceCheck(
            session, args.fqdn, None, args.root_collection, True)
    elif args.all_local_vaults:
        executor = check.VaultCheck(
            session, args.fqdn, None, args.root_collection, True)
    elif args.data_object_list_file:
        executor = check.ObjectListCheck(
            session, args.fqdn, args.data_object_list_file)
    else:
        print("Error: unknown check type.", file=sys.stderr)
        sys.exit(1)

    options = {'output': args.output or sys.stdout, 'fmt': args.fmt}
    if args.truncate:
        options['truncate'] = True

    executor.setformatter(**options)

    executor.run()
