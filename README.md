# Custom Automated Multimedia Pipeline

A automation pipeline that handles media downloading, concurrent processing, low-level binary image manipulation, and metadata stream interleaving. The project features a Python master script that safely manages external file systems and spins up a native compiled C binary for raw memory-managed image cropping.

## System Architecture & Workflow

The application acts as a structured three-stage data assembly line:
1. **Extraction (Python):** Uses `yt_dlp` to securely stream audio tracks (M4A format) and download widescreen video thumbnails from target multimedia links.
2. **Low-Level Processing (C Binary):** Python hands the raw bitmap thumbnail to a local compiled C utility (`./thumbnail_processing`) via a `subprocess` execution fork. The C program directly parses the file's binary header values, algorithmically detects if there are padding bars, and crops the image into a perfect 1:1 square entirely on the heap.
3. **MUX Interleaving (FFmpeg):** The parent Python script calls native system `ffmpeg` forks to multiplex the audio stream and the  artwork container into a final multimedia file.

---

## Core Engineering Concepts Demonstrated

### 1. Cross-Language Integration & OS Forking
Demonstrates the ability to pass variable data arguments across system runtimes. High-level Python coordinates network operations and filesystem routing, while low-level C handles raw byte manipulation, mirroring real-world industrial software setups.

### 2. Manual Memory Management & Pointer Math (C)
The image-processing module avoids bloated graphical frameworks. It utilizes multi-dimensional pointers (`Pixel **pixels`) to dynamically allocate pixel matrices on the heap using `malloc()` and cleanly disposes of them using `free()` to prevent memory leaks. 

### 3. Binary Specification Parsing
Reads structural metadata directly from byte offsets using pointer typecasting shortcuts:
```c
int width = *(int*)&header[18];
int height = *(int*)&header[22];
```
### Functionality
* **Playlist specific archive** Keeps track of already downloaded songs in the `playlist archive` folder that will be created if it does not exist. Archived songs will be skipped for efficiency to reach new songs added. Because it is playlsit specific, a song that appears in two differnt playlist will not be skipped if already archived in one.
* **Logs errors** Logs errors in `error_log.txt` with the exact time the exception occured and the exception.

### Requirements
1. **Python:** Version 3.x or higher.
2. **FFmpeg:** Requires a valid `ffmpeg` installation added to your environment's system PATH.
3. **C Compiler:** Requires `gcc`, `clang`, or an equivalent standard C compiler to compile the native image processing binary.
4. **Python External Libraries:** * `yt_dlp` (For streaming and extracting video/audio buffers)
   * `Pillow` (For basic image format conversions before heap allocation)
5. **JavaScript Runtime:** Requires `Deno` (configured in the system environment paths) to execute isolated JavaScript background subprocess modules.
