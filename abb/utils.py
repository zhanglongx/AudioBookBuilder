from __future__ import annotations

from typing import Set


def is_media_extension(ext: str) -> bool:
    """
    Check whether a file extension is a common media format (audio or video).

    Args:
        ext: File extension, e.g. "mp4", ".mp3", "MKV"

    Returns:
        True if the extension is a common media format, otherwise False.
    """
    if not ext:
        return False

    # Normalize extension: remove leading dot and convert to lowercase
    normalized_ext: str = ext.lower().lstrip(".")

    audio_extensions: Set[str] = {
        "mp3",
        "wav",
        "flac",
        "aac",
        "ogg",
        "m4a",
        "wma",
        "aiff",
        "alac",
        "opus",
        "amr"
    }

    video_extensions: Set[str] = {
        "mp4",
        "mkv",
        "avi",
        "mov",
        "wmv",
        "flv",
        "webm",
        "m4v",
        "3gp",
        "mpeg",
        "mpg"
    }

    common_media_extensions: Set[str] = audio_extensions | video_extensions

    return normalized_ext in common_media_extensions
