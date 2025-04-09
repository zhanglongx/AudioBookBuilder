import argparse
import os
import shutil
import tempfile
import platform
import logging
import ffmpeg
import subprocess

from abc import abstractmethod
from typing import List
from tqdm import tqdm

from abb.const import (DEFAULT_BITRATE, DEFAULT_ENCODING)

class AudioBookBuilder:
    def __init__(self, 
        bitrate : str = DEFAULT_BITRATE,
        re_encode : bool = True,
        verbose : bool = False) -> None:
        """
        ABB base class to handle audiobook building.
        :param bitrate: Bitrate for re-encoding audio files.
        :param re_encode: Force re-encode all files, even if they are already in .m4a format.
        :param verbose: Verbose mode.
        """
        self.bitrate = bitrate
        self.re_encode = re_encode
        self.verbose = verbose

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

    def _convert_to_m4a(self, input_file : str, output_file : str) -> None:
        """Convert a file to .m4a format using ffmpeg-python, if not already"""
        if not self.re_encode and input_file.lower().endswith('.m4a'):
            shutil.copy(input_file, output_file)
        else:
            (
                ffmpeg
                .input(input_file)
                .output(output_file, **{
                    'c:a': self.aac_encoder, 
                    'b:a': self.bitrate,
                    'map': '0:a'
                })
                .overwrite_output()
                .run(quiet=not self.verbose)
            )

    def _get_audio_duration(self, file_path: str) -> float:
        """Get duration in seconds using ffmpeg-python probe"""
        probe = ffmpeg.probe(file_path)
        duration = float(probe['format']['duration'])
        return duration

    @abstractmethod
    def chapters(self) -> str:
        """Abstract method to generate chapters"""
        pass

    @abstractmethod
    def raw_audio(self) -> str:
        """Abstract method to get raw audio"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Abstract method to clean up temporary files"""
        pass

    def build(self, output_file: str, cleanup: bool = True) -> None:
        """
        Method to build the audiobook.
        :param output_file: Path to the output audiobook file.
        :param cleanup: Whether to clean up temporary files.
        """
        try:
            # Generate chapters metadata
            chapters_path = self.chapters()
            
            # Get the raw audio file
            raw_audio_path = self.raw_audio()
            
            # FIXME: I can't write the right ffmpeg-python code
            subprocess.run([
                'ffmpeg',
                '-i', raw_audio_path,
                '-i', chapters_path,
                '-map_metadata', '1',
                '-c', 'copy',
                '-y', output_file
            ], check=True,
            stdout=subprocess.DEVNULL if not self.verbose else None,
            stderr=subprocess.DEVNULL if not self.verbose else None)
            
        finally:
            if cleanup:
                self.cleanup()

class DirectoryBuilder(AudioBookBuilder):
    def __init__(self, directory: str, 
        keywords_file : str,
        bitrate : str = DEFAULT_BITRATE,
        re_encode : bool = True,
        verbose : bool = False) -> None:
        """
        AudiobookBuilder class to build an audiobook from media files.
        :param directory: Path to the directory containing media files.
        :param file_keywords: List of keywords to match files.
        :param bitrate: Bitrate for re-encoding audio files.
        :param re_encode: Force re-encode all files, even if they are already in .m4a format.
        :param verbose: Verbose mode.
        """
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not os.listdir(directory):
            raise ValueError(f"Directory is empty: {directory}")
        
        if not os.path.exists(keywords_file):
            raise FileNotFoundError(f"Keywords file not found: {keywords_file}")

        if re_encode is False:
            logging.warning("Copy files instead of re-encoding may cause issues")

        self.directory = os.path.abspath(directory)

        with open(keywords_file, "r", encoding=DEFAULT_ENCODING) as f:
            keywords = f.read().splitlines()
            # remove file extensions from keywords
            self.file_keywords = [os.path.splitext(k)[0] for k in keywords]

        if not self.file_keywords:
            raise ValueError("No keywords found in the keywords file.")

        self.temp_dir = tempfile.mkdtemp()
        logging.debug(f"Temporary directory created: {self.temp_dir}")

        self._converted_files = []

        super().__init__(bitrate=bitrate, re_encode=re_encode, 
            verbose=verbose)

    def chapters(self) -> str:
        """Implementation of the abstract method to generate chapters"""
        metadata_path = os.path.join(self.temp_dir, "chapters.txt")
        with open(metadata_path, "w", encoding=DEFAULT_ENCODING) as f:
            f.write(";FFMETADATA1\n")
            current_time = 0
            for idx, file in enumerate(self.converted_files):
                duration = super()._get_audio_duration(file)
                f.write("[CHAPTER]\n")
                f.write("TIMEBASE=1/1000\n")
                f.write(f"START={int(current_time * 1000)}\n")
                f.write(f"END={int((current_time + duration) * 1000)}\n")
                f.write(f"title={idx+1:02d}. {self.file_keywords[idx]}\n")
                current_time += duration
        return metadata_path
    
    def raw_audio(self) -> str:
        """Implementation of the abstract method to get raw audio"""
        concat_list_path = os.path.join(self.temp_dir, "inputs.txt")
        with open(concat_list_path, "w", encoding=DEFAULT_ENCODING) as f:
            for file in self.converted_files:
                f.write(f"file '{file}'\n")

        # FIXME: duplicated filename
        joined_audio_path = os.path.join(self.temp_dir, "joined.m4b")
        (
            ffmpeg
            .input(concat_list_path, format='concat', safe=0)
            .output(joined_audio_path, c='copy')
            .overwrite_output()
            .run(quiet=not self.verbose)
        )

        return joined_audio_path

    def cleanup(self) -> None:
        """Implementation of the abstract method to clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logging.debug(f"Temporary directory removed: {self.temp_dir}")
        else:
            logging.warning(f"Temporary directory not found: {self.temp_dir}")

    @property
    def converted_files(self) -> List[str]:
        """List of converted files"""
        if self._converted_files:
            return self._converted_files

        matched_files = self._match_files()
        if not matched_files:
            raise FileNotFoundError("No matching files found.")

        converted_files = []
        # Use tqdm for progress bar if verbose is False
        files = matched_files if self.verbose else tqdm(matched_files, 
            desc="Converting files", unit="file")
        for idx, file in enumerate(files):
            output_file = os.path.join(self.temp_dir, f"{idx:02d}.m4a")

            converted_file = super()._convert_to_m4a(input_file=file, 
                output_file=output_file)
            converted_files.append(converted_file)

        self._converted_files = converted_files
        return converted_files

    def _match_files(self) -> List[str]:
        """Match files in the directory that contain any of the keywords"""
        matched = []
        for keyword in self.file_keywords:
            for file in os.listdir(self.directory):
                if keyword in file:
                    matched.append(os.path.join(self.directory, file))

        if len(matched) != len([f for f in os.listdir(self.directory)]):
            logging.warning("Not all files matched."
                f" Found {len(matched)} out of {len(os.listdir(self.directory))} files.")

        return matched
    
class SingleBuilder(AudioBookBuilder):
    def __init__(self, file: str, 
        chapter_file : str,
        bitrate : str = DEFAULT_BITRATE,
        re_encode : bool = True,
        verbose : bool = False) -> None:
        """
        AudiobookBuilder class to build an audiobook from a single media file.
        :param file: Path to the media file.
        :param chapter_file: Path to the raw chapter file.
        :param bitrate: Bitrate for re-encoding audio files.
        :param re_encode: Force re-encode all files, even if they are already in .m4a format.
        :param verbose: Verbose mode.
        """
        if not os.path.isfile(file):
            raise FileNotFoundError(f"File not found: {file}")
        
        if not os.path.exists(chapter_file):
            raise FileNotFoundError(f"Chapter file not found: {chapter_file}")

        self.file = os.path.abspath(file)
        self.chapters_file = os.path.abspath(chapter_file)

        self.temp_dir = tempfile.mkdtemp()
        super().__init__(bitrate=bitrate, re_encode=re_encode, 
            verbose=verbose)

    def chapters(self) -> str:
        """
        Convert chapter data from '00:00:01 title' format to ffmetadata format.
        """
        metadata_path = os.path.join(self.temp_dir, "chapters.txt")
        duration = int(super()._get_audio_duration(self.file) * 1000) / 1000
        with open(self.chapters_file, "r", encoding=DEFAULT_ENCODING) as f:
            with open(metadata_path, "w", encoding=DEFAULT_ENCODING) as out:
                # Write ffmetadata header
                out.write(";FFMETADATA1\n")
                chapter_times = []
                chapter_titles = []

                # Parse the input file to extract times and titles
                for idx, line in enumerate(f):
                    parts = line.strip().split(" ", 1)
                    if len(parts) != 2:
                        raise ValueError(f"Invalid chapter format: {line.strip()}")
                    time_str, title = parts
                    # Convert time string (HH:MM:SS) to seconds
                    h, m, s = map(int, time_str.split(":"))
                    current_time = h * 3600 + m * 60 + s
                    chapter_times.append(current_time)
                    chapter_titles.append(f"{idx+1:02d}. {title.strip()}")

                for i in range(len(chapter_times)):
                    start_time = chapter_times[i]
                    end_time = chapter_times[i + 1] if i + 1 < len(chapter_times) else duration
                    out.write("[CHAPTER]\n")
                    out.write("TIMEBASE=1/1000\n")
                    out.write(f"START={start_time * 1000}\n")
                    out.write(f"END={end_time * 1000}\n")
                    out.write(f"title={chapter_titles[i]}\n")

        return metadata_path
    
    def raw_audio(self) -> str:
        """Implementation of the abstract method to get raw audio"""
        output_file = os.path.join(self.temp_dir, "single.m4a")
        super()._convert_to_m4a(input_file=self.file,
            output_file=output_file)
        return output_file
    
    def cleanup(self) -> None:
        """Implementation of the abstract method to clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logging.debug(f"Temporary directory removed: {self.temp_dir}")
        else:
            logging.warning(f"Temporary directory not found: {self.temp_dir}")

def main_build(args : argparse.Namespace) -> None:
    output_file = os.path.join(args.output)

    if not os.path.exists(args.list):
        raise FileNotFoundError(f"List file not found: {args.list}")

    # TODO: archive
    builder : AudioBookBuilder
    if os.path.isdir(args.PATH):
        builder = DirectoryBuilder(directory=args.PATH, 
            keywords_file=args.list,
            bitrate=args.bitrate,
            re_encode=not args.not_re_encode,
            verbose=args.verbose)
    elif os.path.isfile(args.PATH):
        builder = SingleBuilder(file=args.PATH, 
            chapter_file=args.list,
            bitrate=args.bitrate,
            re_encode=not args.not_re_encode,
            verbose=args.verbose)
    else:
        raise FileNotFoundError(f"File or directory not found: {args.PATH}")

    builder.build(output_file=output_file,
        cleanup=not args.not_cleanup)

    print(f"Output file: {output_file}")

def parser_build(subparser: argparse._SubParsersAction) -> None:
    cat_parser = subparser.add_parser("build", aliases=["cat"],
        help="Build an audiobook from media files")
    cat_parser.add_argument("-b", "--bitrate", type=str, default=DEFAULT_BITRATE,
        help="re-encode audio bitrate")
    cat_parser.add_argument("--not-cleanup", action="store_true", default=False,
        help="do not delete temporary files")
    cat_parser.add_argument("--not-re-encode", action="store_true", default=False,
        help="force re-encode all files, even if they are already in .m4a format")
    cat_parser.add_argument("-l", "--list", type=str, default="list.txt",
        help="list file to generate the chapter info",)
    cat_parser.add_argument("-o", "--output", type=str, default="output.m4b",
        help="output file name (with .m4b extension)")
    cat_parser.add_argument("PATH", type=str, 
        help="input directory containing media files, or single media file",)
    cat_parser.set_defaults(func=main_build)
