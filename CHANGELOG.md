# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Upgrade Python-irodsclient to v3.2.0
- Remove support for Python 3.6 and 3.7.

## [2.2.0] - 2024-08-14

This version has been tested with Python 3.6+.

Changes since 2.1.0:
- Add --no-verify-checksum option for skipping checksum verification
- Upgrade Python-irodsclient to v2.1.0
- Use standard password obfuscation functions from Python-irodsclient rather than
  local copies

## [2.1.0] - 2022-11-03

This version has been tested with Python 3.6+.

Changes since 2.0.0:
- Add support for new replica statuses in iRODS 4.2.11
- Add support for S3 resources (in resource and object list mode)
- Add option for using Quasi-XML parser in Python-irodsclient, which enables scanning
  of data objects and collections that have particular unusual characters (ASCII codes
  01 through 08, 11, 12 and 14 through 31; on iRODS 4.2.8 and earlier also backticks).

## [2.0.0] - 2020-01-17
This version has been tested with Python 3.6+.

Changes since 1.0.0:
- The output format has changed: the output now contains a resource name field
- New options: --all-local-resources and --all-local-vaults

## [1.0.0] - 2019-11-21
This version of ichk requires Python 3.5+. It is otherwise identical
to version 0.4.0.

## [0.4.0] - 2019-11-21
This version of ichk is compatible with both Python 2.7 and Python 3.5+

Information about versions older than 0.4.0 is not available.
