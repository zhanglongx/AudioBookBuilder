
import argparse
import sys
import logging

from MediaCat.list_files import parser_list
from MediaCat.cat import parser_cat

VERSION = "1.0.0"

def main() -> None:
    parser = argparse.ArgumentParser(description="MediaCat: A tool for media file management.")
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
        help='Enable verbose output')
    parser.add_argument('--version', action='version', version=f'MediaCat {VERSION}',
        help='Show the version number and exit')
    subparsers = parser.add_subparsers(dest='command')

    # Add the list command parser
    parser_list(subparsers)
    parser_cat(subparsers)

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
