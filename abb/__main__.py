
import argparse
import sys
import logging

from abb.list_files import parser_list
from abb.audiobook import parser_build

VERSION = "1.1.1"

def main() -> None:
    parser = argparse.ArgumentParser(description="AudioBookBuilder: A tool for audio-book building.")
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
        help='Enable verbose output')
    parser.add_argument('--version', action='version', version=f'AudioBookBuilder {VERSION}',
        help='Show the version number and exit')
    subparsers = parser.add_subparsers(dest='command')

    # Add the sub-command parser
    parser_list(subparsers)
    parser_build(subparsers)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # Execute the command
    args.func(args)

if __name__ == "__main__":
    main()
