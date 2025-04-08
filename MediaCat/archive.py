
import shutil
import tempfile
import zipfile
import tarfile

from pathlib import Path
from typing import Optional

PREFIX = "media_cat_"

class UnsupportedArchiveFormat(Exception):
    """Raised when an unsupported archive format is encountered"""
    pass

class ArchiveExtractor:
    def __init__(self, archive_path: str):
        self.archive_path = Path(archive_path)
        self.temp_dir: Optional[Path] = None

    def __enter__(self) -> Path:
        self.temp_dir = Path(tempfile.mkdtemp(prefix=PREFIX))
        self._extract_archive()
        return self.temp_dir

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _extract_archive(self) -> None:
        if not self.archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {self.archive_path}")

        suffix = self.archive_path.suffix.lower()

        if suffix == ".zip":
            self._extract_zip()
        elif suffix in [".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz"]:
            self._extract_tar()
        elif suffix in [".gz", ".bz2", ".xz"]:
            self._extract_single_file()
        else:
            raise UnsupportedArchiveFormat(f"Unsupported archive format: {suffix}")

    def _extract_zip(self) -> None:
        with zipfile.ZipFile(self.archive_path, "r") as zf:
            zf.extractall(self.temp_dir)

    def _extract_tar(self) -> None:
        if self.temp_dir is None:
            raise ValueError("Temporary directory has not been initialized")
            
        with tarfile.open(self.archive_path, "r:*") as tf:
            tf.extractall(self.temp_dir)

    def _extract_single_file(self) -> None:
        import gzip, bz2, lzma

        open_fn_map = {
            ".gz": gzip.open,
            ".bz2": bz2.open,
            ".xz": lzma.open,
        }

        suffix = self.archive_path.suffix.lower()
        open_fn = open_fn_map.get(suffix)

        if open_fn is None:
            raise UnsupportedArchiveFormat(f"Unsupported single-file compression: {suffix}")

        if self.temp_dir is None:
            raise ValueError("Temporary directory has not been initialized")
            
        # FIXME: Assume it's compressing a single file, extract to the same filename without suffix
        output_name = self.archive_path.stem
        output_path = self.temp_dir / output_name

        with open_fn(self.archive_path, "rb") as f_in, open(output_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
