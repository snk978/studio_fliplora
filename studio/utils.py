# This Python script uses FFmpeg and FFprobe to extract a specific number of HD frames from a video and groups those frames per second. Below is a breakdown of how the code works and what each part does:

# 🔧 Function 1: get_video_duration(input_path)
# Purpose:
# Gets the duration (in seconds) of the input video file using FFprobe.

# How it works:

# Runs FFprobe via subprocess.run to fetch video metadata.

# Extracts the duration value from the metadata.

# Returns the duration as a float.

# Failsafes:

# If FFprobe fails, it prints a warning and returns 0.

# 🎞️ Function 2: extract_hd_frames(input_path, frame_count, output_dir=None)
# Purpose:
# Extracts a specified number of HD frames from a video and groups them by second.

# 1. Setup:
# Gets the video file's base name (without extension).

# Sets or creates the output directory for frames.

# Builds the output pattern: frame_0001.png, frame_0002.png, etc.

# 2. Get Video Duration:
# Calls get_video_duration() to get total seconds.

# If the duration is invalid (<= 0), it prints an error and exits.

# 3. Calculate Frame Extraction Rate (fps):
# fps = frame_count / duration — calculates how many frames to extract per second.

# If fps is invalid, the function exits.

# 4. Run FFmpeg Command:
# bash
# Copy
# Edit
# ffmpeg -i input_path -vf fps={fps} -q:v 2 output_pattern
# Extracts frames at the calculated fps.

# -q:v 2 ensures high-quality output (for PNG or JPEG).

# Saves the frames to the output directory.

# 5. Post-Processing:
# Collects all PNG frame files.

# Sorts the list of frame file paths.

# If no frames were found, it exits.

# 6. Group Frames Per Second:
# frames_per_second = ceil(total_frames / duration)

# Loops over the sorted frame paths and groups them by second.

# Each group contains approximately the number of frames extracted in 1 second.

# ✅ Output:
# Returns a list of frame groups:

# python
# Copy
# Edit
# [
#   ["frame_0001.png", "frame_0002.png", ...],  # Second 1
#   ["frame_0010.png", "frame_0011.png", ...],  # Second 2
#   ...
# ]
# 🧠 Summary of the Logic:
# Step	Action
# 1	Get video duration using FFprobe
# 2	Calculate appropriate FPS to match desired total frames
# 3	Extract frames using FFmpeg
# 4	Group the frames per second
# 5	Return list of grouped frames

# This is a great structure for use in applications like video preview generation, flipbook creation, or video summarization.


import subprocess
import os
import math

def get_video_duration(input_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of",
             "default=noprint_wrappers=1:nokey=1", input_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return int(float(result.stdout))
    except Exception as e:
        print("⚠️ Could not get video duration:", e)
        return 0

# def extract_hd_frames(input_path, frame_count, output_dir=None):
#     base_name = os.path.splitext(os.path.basename(input_path))[0]

#     # Ensure a valid output directory is specified
#     if output_dir is None:
#         output_dir = os.path.join(os.path.dirname(input_path), f"{base_name}_hd_frames")
#     os.makedirs(output_dir, exist_ok=True)

#     output_pattern = os.path.join(output_dir, "frame_%04d.png")

#     # Get the duration of the video
#     duration = get_video_duration(input_path)
#     print(f"⏱️ Duration of video: {duration:.2f} seconds")

#     # If no valid duration, abort the extraction process
#     if duration <= 0:
#         print("❌ Invalid video duration.")
#         return []

#     # Calculate fps based on the selected frame count
#     fps = frame_count / duration
#     if fps <= 0:
#         print("❌ Invalid fps value. FPS must be greater than 0.")
#         return []

#     command = ["ffmpeg", "-accurate_seek", "-i", input_path, "-vf", f"fps={fps:.6f}", "-vsync", "vfr", "-q:v", "2", output_pattern]


#     try:
#         print(f"🎬 Running FFmpeg command: {' '.join(command)}")
#         subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#         # Gather all frame paths
#         frame_paths = sorted([os.path.join(output_dir, f) for f in os.listdir(output_dir)
#                               if f.endswith(".png")])

#         if not frame_paths:
#             print("❌ No frames were extracted.")
#             return []

#         # Group frames per second
#         frames_per_second = math.ceil(len(frame_paths) / duration) if duration else 1

#         grouped_frames = []
#         for i in range(0, len(frame_paths), frames_per_second):
#             group = frame_paths[i:i + frames_per_second]
#             grouped_frames.append(group)

#         print(f"📂 Total groups created: {len(grouped_frames)}")
#         return grouped_frames

#     except subprocess.CalledProcessError as e:
#         print("❌ Error during frame extraction:", e.stderr.decode())
#         return []

#     except Exception as e:
#         print("⚠️ Unexpected error:", e)
#         return []

# import uuid
import io
import math
import subprocess
from django.core.files import File
from .models import Frame
from PIL import Image
import numpy as np


import os
import subprocess
import math
from io import BytesIO
from PIL import Image
from .models import Frame

def extract_hd_frames(temp_path, frame_count, output_dir, video_instance):
    os.makedirs(output_dir, exist_ok=True)

    # Get video duration
    duration = get_video_duration(temp_path)
    print(f"⏱️ Duration of video: {duration:.2f} seconds")

    if duration <= 0:
        print("❌ Invalid video duration.")
        return []

    fps = frame_count / duration
    if fps <= 0:
        print("❌ Invalid fps value.")
        return []

    output_pattern = os.path.join(output_dir, "frame_%04d.png")
    command = [
        "ffmpeg", "-i", temp_path, "-vf", f"fps={fps:.6f}", "-vsync", "vfr", "-q:v", "2", output_pattern
    ]

    try:
        print(f"🎬 Running FFmpeg command: {' '.join(command)}")
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        frame_files = sorted([
            os.path.join(output_dir, f) for f in os.listdir(output_dir)
            if f.endswith(".png")
        ])

        if not frame_files:
            print("❌ No frames extracted.")
            return []

        frame_counter = 1
        grouped_frames = []
        frames_per_second = math.ceil(len(frame_files) / duration) if duration else 1

        for i in range(0, len(frame_files), frames_per_second):
            group = frame_files[i:i + frames_per_second]
            grouped_frames.append(group)

        for group in grouped_frames:
            for path in group:
                with open(path, "rb") as img_file:
                    Frame.objects.create(
                        video=video_instance,
                        frame_number=frame_counter,
                        frame_data=img_file.read()
                    )
                    frame_counter += 1

        print(f"📦 Saved {frame_counter - 1} frames to the database.")
        return grouped_frames

    except subprocess.CalledProcessError as e:
        print("❌ FFmpeg error:", e.stderr.decode())
        return []
