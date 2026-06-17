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
