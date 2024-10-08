"""Check consistency between iRODS data objects and files in vaults."""

import argparse
import json
import os
import socket
import sys
from getpass import getpass

from irods import password_obfuscation
from irods.message import (ET, XML_Parser_Type)
from irods.session import iRODSSession

from ichk import check


def entry():
    """Used as entry_point in setup.py"""
    try:
        main(get_args())
    except KeyboardInterrupt:
        print("Script interrupted by user.", file=sys.stderr)


def get_args():
    '''Returns command line arguments of the script.'''
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("-f", "--fqdn",
                        help="FQDN of resource", default=socket.getfqdn())
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
    parser.add_argument("--no-verify-checksum", action="store_true", default=False,
                        help="Do not verify checksums of data objects. Just check presence and size of vault files.")
    parser.add_argument("-q", "--quasi-xml", action="store_true", default=False,
                        help="Enable the Quasi-XML parser, which supports unusual characters (0x01-0x31, backticks)")
    args = parser.parse_args()

    if args.root_collection is not None and args.data_object_list_file is not None:
        print("Error: the --root-collection / -s and the --data-object-list / -l option can't be combined.")
        sys.exit(1)

    if args.root_collection is not None:
        args.root_collection = args.root_collection.rstrip("/")

    return args


def main(args):
    session = setup_session()
    session.connection_timeout = args.timeout

    if args.quasi_xml:
        ET(XML_Parser_Type.QUASI_XML, session.server_version)

    with session:
        run(session, args)


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
    '''Actually runs the check'''
    if args.resource:
        executor = check.ResourceCheck(
            session, args.fqdn, args.resource, args.root_collection,
            all_local_resources=False, no_verify_checksum=args.no_verify_checksum)
    elif args.vault:
        executor = check.VaultCheck(
            session, args.fqdn, args.vault, args.root_collection,
            all_local_resources=False, no_verify_checksum=args.no_verify_checksum)
    elif args.all_local_resources:
        executor = check.ResourceCheck(
            session, args.fqdn, None, args.root_collection,
            all_local_resources=True, no_verify_checksum=args.no_verify_checksum)
    elif args.all_local_vaults:
        executor = check.VaultCheck(
            session, args.fqdn, None, args.root_collection,
            all_local_resources=True, no_verify_checksum=args.no_verify_checksum)
    elif args.data_object_list_file:
        executor = check.ObjectListCheck(
            session, args.fqdn, args.data_object_list_file,
            no_verify_checksum=args.no_verify_checksum)
    else:
        print("Error: unknown check type.", file=sys.stderr)
        sys.exit(1)

    options = {'output': args.output or sys.stdout, 'fmt': args.fmt}
    if args.truncate:
        options['truncate'] = True

    executor.setformatter(**options)

    executor.run()
