# api/tasks.py
import os, subprocess, math, base64, shutil, uuid
from celery import shared_task
from django.conf import settings
from .models import Video_Final, Frame
from .utils import get_video_duration   # keep your helper

FFMPEG_BIN = "ffmpeg"   # or full path

@shared_task(bind=True)
def extract_frames_task(self, video_id: int, fps: int):
    """
    1. Pull raw video bytes from DB.
    2. Stream to FFmpeg -> PNGs in /tmp.
    3. Persist frames back to DB (or S3).
    4. Return lightweight payload (IDs or pre‑b64).
    """
    video = Video_Final.objects.get(id=video_id)

    # --- step 0) write temp video to disk (FFmpeg likes files) ---
    tmp_uid = uuid.uuid4().hex
    video_tmp = f"/tmp/{tmp_uid}.mp4"
    with open(video_tmp, "wb") as f:
        f.write(video.data)

    frames_dir = f"/tmp/frames_{tmp_uid}"
    os.makedirs(frames_dir, exist_ok=True)

    # --- step 1) run ffmpeg ---
    output_pattern = os.path.join(frames_dir, "frame_%04d.png")
    cmd = [
        FFMPEG_BIN, "-i", video_tmp,
        "-vf", f"fps={fps}",
        "-vsync", "vfr", "-q:v", "31",
        output_pattern,
    ]
    subprocess.run(cmd, check=True)

    # --- step 2) save frames ---
    frame_files = sorted(
        f for f in os.listdir(frames_dir) if f.endswith(".png")
    )
    db_objs = []
    for idx, fname in enumerate(frame_files, start=1):
        with open(os.path.join(frames_dir, fname), "rb") as fh:
            db_objs.append(
                Frame(
                    video=video,
                    frame_number=idx,
                    frame_data=fh.read(),   # Bytea in DB
                )
            )
    Frame.objects.bulk_create(db_objs, batch_size=500)

    # --- step 3) cleanup temp files ---
    os.remove(video_tmp)
    shutil.rmtree(frames_dir, ignore_errors=True)

    # --- step 4) craft result (only metadata => tiny JSON) ---
    return {
        "total_frames": len(db_objs),
        "video_id": video.id,
    }
