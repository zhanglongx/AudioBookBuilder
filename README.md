# MediaCat

Mediacat is a tool to automate the stitching of media files, mainly for the production of audio books.

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

   - list.txt: It's the built-in list filename used by MediaCat to concatenate the media files.

3. Edit the `list` file, mainly re-ordering the files, or stripping the file names.

    NOTE: 

    - MediaCat has built-in reg-based filter `-[a-zA-Z0-9-]{11,}$` to remove the hash from the file names. This is useful for media files download from yt.

    - Do not delete the intervening characters, as this will cause an error in the media concat the next step.

    Examples:

    - ✅ `-a-b-c.mp4` -> `a-b-c.mp4`

    - ❌ `-a-b-c.mp4` -> `-ab-c.mp4`

4. Concat the media files:

    ```bash
    python -m MediaCat cat <path>
    ```

## Issues

(TODO)

## TODO

- [ ] Support for reading media files from archiver (e.g. zip, tar, etc.)
