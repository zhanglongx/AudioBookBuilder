
import argparse
import os
import shutil
import tempfile
import platform
import logging
import ffmpeg
import subprocess

from typing import List
from tqdm import tqdm

from abb.const import (
    DEFAULT_BITRATE,
    DEFAULT_ENCODING)

class AudiobookBuilder:
    def __init__(self, directory: str, 
        file_keywords : List[str],
        bitrate : str = DEFAULT_BITRATE,
        verbose : bool = False,
        re_encode : bool = True) -> None:
        """
        AudiobookBuilder class to build an audiobook from media files.
        :param directory: Path to the directory containing media files.
        :param file_keywords: List of keywords to match files.
        :param bitrate: Bitrate for re-encoding audio files.
        :param verbose: Verbose mode.
        :param re_encode: Force re-encode all files, even if they are already in .m4a format.
        """
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")

        if re_encode is False:
            logging.warning("Copy files instead of re-encoding may cause issues")

        self.directory = os.path.abspath(directory)
        # remove file extensions from keywords
        self.file_keywords = [os.path.splitext(keyword)[0] for keyword in file_keywords]
        self.bitrate = bitrate
        self.verbose = verbose
        self.re_encode = re_encode

        self.temp_dir = tempfile.mkdtemp()

        logging.debug(f"Temporary directory created: {self.temp_dir}")

    @property
    def aac_encoder(self) -> str:
        """Select hardware AAC encoder based on platform"""
        # FIXME: dynamic probing for available encoders
        system = platform.system()
        if system == "Windows":
            logging.debug("Using Windows Media Foundation AAC encoder")
            return "aac_mf"
        elif system == "Darwin":
            logging.debug("Using Apple AudioToolbox AAC encoder")
            return "aac_at"
        else:
            logging.debug("Using fall-back software AAC encoder")
            logging.info("Software AAC encoder may be slow")
            return "aac"

    def _match_files(self) -> List[str]:
        """Match files in the directory that contain any of the keywords"""
        matched = []
        for keyword in self.file_keywords:
            for file in os.listdir(self.directory):
                if keyword in file:
                    matched.append(os.path.join(self.directory, file))

        if len(matched) != len(set(matched)):
            logging.warning("Not all files are unique, duplicates found")

        return matched

    def _convert_to_m4a(self, input_file: str, index: int) -> str:
        """Convert a file to .m4a format using ffmpeg-python, if not already"""
        output_path = os.path.join(self.temp_dir, f"{index:02d}.m4a")
        if not self.re_encode and input_file.lower().endswith('.m4a'):
            shutil.copy(input_file, output_path)
        else:
            (
                ffmpeg
                .input(input_file)
                .output(output_path, **{
                    'c:a': self.aac_encoder, 
                    'b:a': self.bitrate,
                    'map': '0:a'
                })
                .overwrite_output()
                .run(quiet=not self.verbose)
            )
        return output_path

    def _generate_chapters(self, converted_files : List) -> str:
        """Generate a ffmetadata file with chapters"""
        metadata_path = os.path.join(self.temp_dir, "chapters.txt")
        with open(metadata_path, "w", encoding=DEFAULT_ENCODING) as f:
            f.write(";FFMETADATA1\n")
            current_time = 0
            for idx, file in enumerate(converted_files):
                duration = self._get_audio_duration(file)
                f.write("[CHAPTER]\n")
                f.write("TIMEBASE=1/1000\n")
                f.write(f"START={int(current_time * 1000)}\n")
                f.write(f"END={int((current_time + duration) * 1000)}\n")
                f.write(f"title={idx+1:02d}. {self.file_keywords[idx]}\n")
                current_time += duration
        return metadata_path

    def _get_audio_duration(self, file_path: str) -> float:
        """Get duration in seconds using ffmpeg-python probe"""
        probe = ffmpeg.probe(file_path)
        duration = float(probe['format']['duration'])
        return duration

    def _concat_audio(self, output_file: str, 
        metadata_path: str, converted_files : List ) -> None:
        """Concatenate audio files and embed chapters using ffmpeg-python"""
        concat_list_path = os.path.join(self.temp_dir, "inputs.txt")
        with open(concat_list_path, "w", encoding=DEFAULT_ENCODING) as f:
            for file in converted_files:
                f.write(f"file '{file}'\n")

        joined_audio_path = os.path.join(self.temp_dir, "joined.m4b")

        (
            ffmpeg
            .input(concat_list_path, format='concat', safe=0)
            .output(joined_audio_path, c='copy')
            .overwrite_output()
            .run(quiet=not self.verbose)
        )

        # Create a new ffmpeg process using subprocess
        # FIXME: I can't write the right ffmpeg-python code
        subprocess.run([
                'ffmpeg',
                "-xerror",
                '-i', joined_audio_path,
                '-i', metadata_path,
                '-map_metadata', '1',
                '-c', 'copy',
                '-y', 
                output_file
            ], check=True, 

            stdout=subprocess.DEVNULL if not self.verbose else None,
            stderr=subprocess.DEVNULL if not self.verbose else None)

    def build(self, output_file: str = "output.m4b", 
            cleanup : bool = True) -> None:
        """Main method to build final m4b audiobook"""
        try:
            matched_files = self._match_files()
            if not matched_files:
                raise FileNotFoundError("No matching files found.")

            converted_files = []
            # Use tqdm for progress bar if verbose is False
            files = matched_files if self.verbose else tqdm(matched_files, 
                desc="Converting files", unit="file")
            for idx, file in enumerate(files):
                converted_file = self._convert_to_m4a(file, idx)
                converted_files.append(converted_file)

            metadata_path = self._generate_chapters(
                converted_files=converted_files)
            self._concat_audio(output_file=output_file, 
                metadata_path=metadata_path, 
                converted_files=converted_files)

        finally:
            if cleanup:
                shutil.rmtree(self.temp_dir)
            else:
                print(f"Temporary files kept in: {self.temp_dir}")

def main_cat(args : argparse.Namespace) -> None:
    output_file = os.path.join(args.output)

    if not os.path.exists(args.list):
        raise FileNotFoundError(f"List file not found: {args.list}")

    # TODO: archive
    with open(args.list, "r", encoding=DEFAULT_ENCODING) as f:
        file_keywords = f.read().splitlines()

        builder = AudiobookBuilder(directory=args.PATH, 
            file_keywords=file_keywords,
            re_encode=not args.not_re_encode,
            verbose=args.verbose)
        builder.build(output_file=output_file,
            cleanup=not args.not_cleanup)

    print(f"Output file: {output_file}")

def parser_cat(subparser: argparse._SubParsersAction) -> None:
    cat_parser = subparser.add_parser("cat", aliases=["audiobook"],
        help="Build an audiobook from media files")
    cat_parser.add_argument("-b", "--bitrate", type=str, default=DEFAULT_BITRATE,
        help="re-encode audio bitrate")
    cat_parser.add_argument("--not-cleanup", action="store_true", default=False,
        help="do not delete temporary files")
    cat_parser.add_argument("--not-re-encode", action="store_true", default=False,
        help="force re-encode all files, even if they are already in .m4a format")
    cat_parser.add_argument("-l", "--list", type=str, default="list.txt",
        help="keywords to match files",)
    cat_parser.add_argument("-o", "--output", type=str, default="output.m4b",
        help="output file name (with .m4b extension)")
    cat_parser.add_argument("PATH", type=str, 
        help="input directory containing media files",)
    cat_parser.set_defaults(func=main_cat)
