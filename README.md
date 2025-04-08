# MediaCat

Mediacat is a tool to automate the stitching of media files, mainly for the production of audio books.

Mediacat will first generate a list of media files in a directory, extract audio track, then concatenate them into a single media file (AudioBook format `m4b` for now).

## Pre-requisites

- [FFMpeg](https://ffmpeg.org/download.html)

## Usage

1. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

2. Generate the `list` file:

   ```bash
   python -m MediaCat list <path> > list.txt
   ```

   - path: The path to the directory containing the media files.

   - list.txt: The built-in list filename used by MediaCat to concatenate the media files, see steps below.

3. Edit the `list` file, mainly re-ordering the files, or stripping the file names.

    NOTE: 

    - MediaCat has built-in reg-based filter `'-[a-zA-Z0-9-]{11,}$'` to remove the hash from the file names. This is useful for media files download from yt.

    - Do not delete the intervening characters, as this will cause an error in the media concat the next step.

    Examples:

    - ✅(Built-in) `-a-b-c-JXCDcGmuibo.m4a` -> `a-b-c.m4a`

    - ✅ `-a-b-c.m4a` -> `a-b-c.m4a`

    - ❌ `-a-b-c.m4a` -> `-ab-c.m4a`

4. Once the `list` file ('list.txt' as default) is ready, concat the media files:

    ```bash
    python -m MediaCat cat <path>
    ```

## Issues

(TODO)

## TODO

- [ ] Support for reading media files from archiver (e.g. zip, tar, etc.).

- [ ] Customize the chapters prefixes.

- [ ] Multi-process
