
import argparse
import os
import re

from typing import List

from MediaCat.archive import ArchiveExtractor

class ListFiles:
    def __init__(self, path : str, filters : List[str] = []) -> None:
        """
        ListFiles class to list files in a directory.
        :param path: Path to the directory to list files from.
        :param filters: List of filters to use.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path {path} does not exist.")

        self.path = path
        self.filters = filters

    def list(self) -> List[str]:
        """
        List files in the directory.
        :return: List of files in the directory.
        """
        files = []
        for _, _, filenames in os.walk(self.path):
            for filename in filenames:
                files.append(self._filter(filename))
        return files
    
    def _filter(self, str) -> str:
        result = str
        for pattern in self.filters:
            result = re.sub(pattern, '', result)
        return result
    
def main_list(args : argparse.Namespace) -> None:
    path = args.PATH
    
    if os.path.isfile(path):
        with ArchiveExtractor(path) as temp_dir:
            list_files = ListFiles(str(temp_dir), args.filters)
            files = list_files.list()
            for file in files:
                print(file)
    elif os.path.isdir(path):
        list_files = ListFiles(path, args.filters)
        files = list_files.list()
        for file in files:
            print(file)
    else: 
        raise FileNotFoundError(f"Path {path} does not exist.")
    
def parser_list(subparsers : argparse._SubParsersAction) -> None:
    list_parser = subparsers.add_parser('list', help='List files in a directory or archive.')
    list_parser.add_argument('PATH', type=str, help='Path to the directory or archive to list files from.')
    list_parser.set_defaults(func=main_list)
