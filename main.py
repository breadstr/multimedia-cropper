from PIL import Image
from pathlib import Path
from multiprocessing import Pool
import yt_dlp
import sys
import os
import subprocess
import re
import time

# Configuration for JavaScript runtime (adjust path for your system environment)
js_runtime = {"deno:/usr/bin/deno"}

def getPlaylistID(playlist_url: str) -> str:
    match = re.search(r"list=([A-Za-z0-9_-]+)", playlist_url)

    if match:
        return match.group(1)

    else:
        return "unknow_playlist"

def writeExeption(url: str, error_msg : str) -> None:
    with open("error_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{ time.ctime(time.time())} Summary: {url}\n{error_msg}\n")
        f.write("-" * 15 + "\n\n")

def convertThumbnail(thumbnail_name: str) -> str:

    with Image.open(thumbnail_name) as img:
        rbg_img = img.convert("RGB") #convert to rgb so that it becoms compatible to the c script
        bmp_name = os.path.splitext(thumbnail_name)[0] + ".bmp"
        rbg_img.save(bmp_name,"BMP")

    return bmp_name

def addCoverart(audio : str, thumbnail : str, directory : str, track_number: str) -> None:

    temp_output = audio + ".tagged.m4a"

    cmd = [
        "ffmpeg", "-y",
        "-i", audio,
        "-i", thumbnail,
        "-map", "0:0",        # Map the audio
        "-map", "1:0",        # Map the image
        "-map_metadata", "0", # Copy global metadata from the original audio
        "-map_metadata:s:a", "0:s:a", # Copies stream-specific metadata
        "-c:a", "copy",       # Keep audio as-is
        '-metadata', f'track={track_number}', # Set track number
        "-c:v", "png",        # Convert BMP to PNG (standard for M4A covers)
        "-disposition:v", "attached_pic", 
        temp_output
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        os.replace(temp_output, os.path.join(directory,audio))

    except subprocess.CalledProcessError:
        if os.path.exists(temp_output):
            os.remove(temp_output)
        raise

def dlThumbnail(url: str) -> str: #>:) gets thumbnail
    yt_opt = {
        'runtime:': js_runtime,
        "writethumbnail" : True,
        "skip_download" : True,
        "noplaylist" : True,
        "retries": 10,
        "fragment_retries": 10,
        "outtmpl" : "%(id)s.%(ext)s"
    }
    
    with yt_dlp.YoutubeDL(yt_opt) as ydl:

        info = ydl.extract_info(url, download=False)
        
        file_name = info.get("id")
        
        ydl.download([url])
        
    for file in os.listdir("./"):
        if file.startswith(os.path.splitext(file_name)[0]):
            if file.lower().endswith(('.jpg', '.jpeg', 'webp', '.png')):
                return file
    
    return None

def dlAudio(url: str) -> str:  
    ydl_opts = {
        'runtime:': js_runtime,
        "format" : "m4a/bestaudio/best", 
        "noplaylist" : True, 
        "retries": 10,
        "fragment_retries": 10,
        "postprocessors" : [
        {        
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        },
        {"key": "FFmpegMetadata", # This line adds the Artist, Title, etc.
            "add_chapters": True,    # If the video has chapters, they become M4A chapters!
            "add_metadata": True,
        }
        
        ],
        "keepvideo": False, 
        "outtmpl" : "%(title)s.%(ext)s"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(url, download=False)
        audio_name = ydl.prepare_filename(info)

        ydl.download([url])

        return audio_name
    
def extractPlaylist(playlist_url: str) -> list:
    ydl_opts = {
        'extract_flat': True, 
        'quiet': True, 
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(playlist_url, download=False)

        video_urls = []
        if 'entries' in result:
            for entry in result['entries']:
                if "url" in entry:
                    video_urls.append(entry["url"])
      
        return video_urls

def getUrls(playlist_link: str) -> list:

    print("Fetching playlist from Youtube (may take a while)...")
    urls = extractPlaylist(playlist_link)
       
    return urls

def processOneUrl(url: str, playlist_archive: str, video_id: str, track_num: str, anchor_time : str, directory: Path = Path.cwd()) -> None:

    time.sleep(2)

    audio = dlAudio(url)
    time.sleep(3)
    filename = dlThumbnail(url)
    if not filename:
        raise ValueError("Thumbnail file does not exist.")
        
    bmp_name = convertThumbnail(filename)
    
    try:
        subprocess.run(["./thumbnail_processing", bmp_name], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"C Program Crashed on {filename}: {e}")
        
    addCoverart(audio, bmp_name, directory, track_num)

    final_file_path = os.path.join(directory, audio)
    if os.path.exists(final_file_path):

        fake_time = anchor_time + track_num
        
        os.utime(final_file_path, (fake_time, fake_time))

    if os.path.exists(filename): 
        os.remove(filename)

    if os.path.exists(bmp_name):
        os.remove(bmp_name)
    
    if os.path.exists(audio) and Path(directory).resolve() != Path("./").resolve():
        os.remove(audio)

    with open(playlist_archive, "a") as f:
        f.write(f"{video_id}\n")

def getExsitingSongIDs(archive_file):
    if not os.path.exists(archive_file):
        (Path.cwd() / "playlist archive").mkdir(parents=True, exist_ok=True)

    done_ids = set()
    if os.path.exists(archive_file):
        with open(archive_file, "r") as f:
            done_ids = set(line.strip() for line in f)

    return done_ids

def worker_wrapper(args):
    """
    This wrapper unpacks the arguments for each process worker 
    and handles crashes so one bad song doesn't kill the whole pool.
    """
    url, playlist_archive, video_id, track_num, anchor_time, directory = args
    try:
        processOneUrl(url, playlist_archive, video_id, track_num, anchor_time, directory)
        return (video_id, True)
    except Exception as e:
        writeExeption(url, str(e))
        return (video_id, False)

def main() -> int:
    playlist_url = "YOUR_PLAYLIST_URL_HERE"
    save_directory = "OUTPUT DIRECTORY HERE"
    playlist_id = getPlaylistID(playlist_url)
    archive_file = os.path.join(Path.cwd() / "playlist archive",f"{playlist_id}.txt")
    urls_to_download = getUrls(playlist_url)
    done_ids = getExsitingSongIDs(archive_file)
    cur_time = time.time()

    pending_tasks = []

    for track_num, url in enumerate(urls_to_download):
        try:
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            else:
                video_id = url.split("=")[1]
                
            if video_id not in done_ids:
                pending_tasks.append((url, archive_file, video_id, track_num, cur_time, save_directory))

            else:
                print(f"\033[92m{video_id}\033[0m already exists, moving to next song.")

        except Exception as e:  
            writeExeption(url, e)

    if not pending_tasks:
        print("Everything is up to date!")
        return 0

    with Pool() as pool:
        # pool.imap streams the results back to main in order as they finish
        results = pool.imap(worker_wrapper, pending_tasks)
        
        for video_id, success in results:
            if success:
                print(f"\033[94mSuccessfully processed and archived:\033[0m {video_id}")
            else:
                print(f"\033[91mFailed:\033[0m {video_id}. Check error_log.txt")

    return 0

if __name__ == "__main__":
    sys.exit(main())
