# AudioBookBuilder

AudioBookBuilder(ABB) is a tool to automate the stitching of media files, mainly for the production of audio books.

ABB receives input in two ways, file directory or single file. In directory mode, multiple media files are stored in the directory, and ABB will combine them into one audio-book file; in single file mode, the user has to provide an additional chapter file, and ABB will create the audio-book file based on the chapter file.

ABB will add a built-in digital prefix in format of `02d. ` to the chapter title.

## Pre-requisites

- [FFMpeg](https://ffmpeg.org/download.html)

## Usage

1. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

2. Use the right mode for your needs.

### Directory Mode

1. Generate the `list` file:

   ```bash
   python -m abb list <path> > list.txt
   ```

   - path: The path to the directory containing the media files.

   - list.txt: The built-in list filename used by AudioBookBuilder to concatenate the media files, see steps below.

2. Edit the `list` file, mainly re-ordering the files, or stripping the file names.

    NOTE: 

    - AudioBookBuilder has built-in reg-based filter `'-[a-zA-Z0-9-]{11,}$'` to remove the hash from the file names. This is useful for media files download from yt.

    - Do not delete the intervening characters, as this will cause an error in the media concat the next step.

    Examples:

    - ✅(Built-in) `-a-b-b-JXCDcGmuibo.m4a` -> `a-b-b.m4a`

    - ✅ `-a-b-b.m4a` -> `a-b-b.m4a`

    - ❌ `-a-b-b.m4a` -> `-ab-b.m4a`

3. Once the `list` file ('list.txt' as default) is ready, concat the media files:

    ```bash
    python -m abb build <path>
    ```

    - path: The path to the directory containing the input media files.

### Single File Mode

1. Generate the `list` file

    The `list` file is a text file containing the start time and the chapter name, separated by a space. The start time should be in the format `HH:MM:SS`, and the chapter name can be any string. For example:

    ```
    00:00:00    chapter 1
    00:10:00    chapter 2
    00:20:00    chapter 3
    ```

2. Build the audio-book file:

    ```bash
    python -m abb build <path>
    ```

    - path: The path to the input media file.

## Issues

(TODO)

## TODO

- [ ] Extend directory mode, by supporting for reading media files from archiver (e.g. zip, tar, etc.).

- [ ] Customize the chapters prefixes.

- [ ] Multi-process
