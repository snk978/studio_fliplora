import os
import base64
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.parsers import JSONParser
from studio.models import Video, Frame, Video_Final
from django.core.files import File
import shutil
from studio.utils import extract_hd_frames,get_video_duration# Ensure this function is correctly implemented to handle frame count
import uuid, base64
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Video_Final, Frame
from studio.tasks import extract_frames_task
from celery.result import AsyncResult
from studio_bd.celery import app


# Store the grouped frames globally (temporary solution for now)
GLOBAL_FRAME_GROUPS = []  # List of frame groups


@method_decorator(csrf_exempt, name='dispatch')
# class ChatAPIView(APIView):
#     def post(self, request):
#         try:
#             global GLOBAL_FRAME_GROUPS  # <-- ADD THIS LINE

#             # Get the uploaded video file and the frame count from the request
#             video = request.FILES.get('video')
#             start = request.POST.get('start')
#             end = request.POST.get('end')
#             frame_count = int(request.POST.get('frame_count', 120))  # Default to 120 if not provided

#             if not video:
#                 return Response({'error': 'No video file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

#             # Save uploaded video
#             upload_dir = os.path.join(os.getcwd(), "uploads")
#             os.makedirs(upload_dir, exist_ok=True)
#             save_path = os.path.join(upload_dir, video.name)

#             with open(save_path, 'wb+') as destination:
#                 for chunk in video.chunks():
#                     destination.write(chunk)

#             print(f"✅ Video saved at: {save_path}")

#             # Extract frames (now grouped per second)
#             frames_dir = os.path.join(upload_dir, f"{video.name}_frames")
#             os.makedirs(frames_dir, exist_ok=True)

#             # Modify frame extraction function to take the frame count into consideration
#             frame_groups = extract_hd_frames(save_path, frame_count, frames_dir)  # Pass frame count
#             print(f"⚙️ Frame Groups: {frame_groups}")  # Debugging the extracted frame groups

#             # If no frames are extracted
#             if not frame_groups:
#                 return Response({'error': 'No frames extracted from the video'}, status=status.HTTP_400_BAD_REQUEST)

#             # Save the frame groups globally
#             GLOBAL_FRAME_GROUPS = frame_groups  # <-- ADD THIS LINE

#             # Encode frames to base64 and add frame numbers
#             encoded_frames = []
#             frame_counter = 1  # Start frame number from 1

#             for group in frame_groups:
#                 for path in group:
#                     with open(path, "rb") as image_file:
#                         encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
#                         encoded_frames.append({
#                             "src": f"data:image/png;base64,{encoded_string}",
#                             "frame_number": frame_counter
#                         })
#                         frame_counter += 1

#             # Debugging: Check how many frames are encoded
#             print(f"⚡ Total frames encoded: {len(encoded_frames)}")

#             return Response({
#                 'message': f'{len(encoded_frames)} frames extracted.',
#                 'frames': encoded_frames
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             print("❌ Exception:", e)
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# class ChatAPIView(APIView):
#     def post(self, request):
#         try:
#             # Get the uploaded video file and frame count
#             video_file = request.FILES.get('video')
#             frame_count = int(request.POST.get('frame_count', 120))

#             if not video_file:
#                 return Response({'error': 'No video uploaded'}, status=status.HTTP_400_BAD_REQUEST)

#             # Save video to disk
#             upload_dir = os.path.join(os.getcwd(), "uploads")
#             os.makedirs(upload_dir, exist_ok=True)
#             save_path = os.path.join(upload_dir, video_file.name)

#             with open(save_path, 'wb+') as dest:
#                 for chunk in video_file.chunks():
#                     dest.write(chunk)

#             # Get video duration
#             duration = get_video_duration(save_path)
#             # Wrap the saved file using Django's File and save to DB
#             with open(save_path, 'rb') as f:
#                 django_file = File(f)
#                 video_instance = Video.objects.create(
#                     title=video_file.name,
#                     file=django_file,
#                     duration=duration
#                 )

#             # Extract & save frames to DB
#             frames_dir = os.path.join(upload_dir, f"{video_file.name}_frames")
#             grouped_frames = extract_hd_frames(save_path, frame_count, frames_dir, video_instance)

#             if not grouped_frames:
#                 return Response({'error': 'No frames extracted'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             # Fetch frames from DB and encode for frontend
#             frames = Frame.objects.filter(video=video_instance).order_by('frame_number')

#             encoded_frames = []
#             for frame in frames:
#                 base64_data = base64.b64encode(frame.frame_data).decode('utf-8')
#                 encoded_frames.append({
#                     "frame_number": frame.frame_number,
#                     "src": f"data:image/png;base64,{base64_data}"
#                 })

#             return Response({
#                 "video_id": video_instance.id,
#                 "video_title": video_instance.title,
#                 "frames": encoded_frames
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             print("❌ Exception:", e)
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# class ChatAPIView(APIView):
#     def post(self, request):
#         try:
#             video_file = request.FILES.get('video')
#             frame_count = int(request.POST.get('frame_count', 120))

#             if not video_file:
#                 return Response({'error': 'No video uploaded'}, status=status.HTTP_400_BAD_REQUEST)

#             # Read raw video bytes
#             video_data = video_file.read()

#             # Save temp file for processing (FFmpeg requires file input)
#             temp_dir = os.path.join(os.getcwd(), "temp_uploads")
#             os.makedirs(temp_dir, exist_ok=True)
#             temp_path = os.path.join(temp_dir, video_file.name)

#             with open(temp_path, 'wb') as temp_file:
#                 temp_file.write(video_data)

#             # Get video duration
#             duration = get_video_duration(temp_path)

#             # Store video data in DB
#             video_instance = Video.objects.create(
#                 title=video_file.name,
#                 data=video_data,
#                 duration=duration
#             )

#             # Extract frames
#             frames_dir = os.path.join(temp_dir, f"{video_file.name}_frames")
#             grouped_frames = extract_hd_frames(temp_path, frame_count, frames_dir, video_instance)

#             if not grouped_frames:
#                 return Response({'error': 'No frames extracted'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             # Encode frames
#             frames = Frame.objects.filter(video=video_instance).order_by('frame_number')
#             encoded_frames = [{
#                 "frame_number": frame.frame_number,
#                 "src": f"data:image/png;base64,{base64.b64encode(frame.frame_data).decode('utf-8')}"
#             } for frame in frames]

#             return Response({
#                 "video_id": video_instance.id,
#                 "video_title": video_instance.title,
#                 "frames": encoded_frames
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             print("❌ Exception:", e)
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class ChatAPIView(APIView):
#     def post(self, request):
#         temp_path = None
#         frames_dir = None

#         try:
#             video_file = request.FILES.get('video')
#             frame_count = int(request.POST.get('frame_count', 120))

#             if not video_file:
#                 return Response({'error': 'No video uploaded'}, status=status.HTTP_400_BAD_REQUEST)

#             # Read video data from InMemoryUploadedFile or TemporaryUploadedFile
#             video_bytes = video_file.read()

#             # Save temp video to disk for FFmpeg processing
#             upload_dir = os.path.join(os.getcwd(), "uploads")
#             os.makedirs(upload_dir, exist_ok=True)
#             temp_path = os.path.join(upload_dir, video_file.name)

#             with open(temp_path, 'wb') as f:
#                 f.write(video_bytes)

#             # Get duration from temp file
#             duration = get_video_duration(temp_path)

#             # Save video directly to database using BinaryField
#             video_instance = Video_Final.objects.create(
#                 title=video_file.name,
#                 data=video_bytes,
#                 duration=duration
#             )

#             # Extract and save frames
#             frames_dir = os.path.join(upload_dir, f"{video_file.name}_frames")
#             grouped_frames = extract_hd_frames(temp_path, frame_count, frames_dir, video_instance)

#             if not grouped_frames:
#                 return Response({'error': 'No frames extracted'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#             # Encode frames for frontend
#             frames = Frame.objects.filter(video=video_instance).order_by('frame_number')
#             encoded_frames = [
#                 {
#                     "frame_number": frame.frame_number,
#                     "src": f"data:image/png;base64,{base64.b64encode(frame.frame_data).decode('utf-8')}"
#                 }
#                 for frame in frames
#             ]

#             return Response({
#                 "video_id": video_instance.id,
#                 "video_title": video_instance.title,
#                 "frames": encoded_frames
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             print("❌ Exception:", e)
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         finally:
#             if temp_path and os.path.exists(temp_path):
#                 os.remove(temp_path)
#                 print(f"🗑️ Deleted temp video: {temp_path}")

#             if frames_dir and os.path.exists(frames_dir):
#                 shutil.rmtree(frames_dir, ignore_errors=True)
#                 print(f"🧹 Deleted extracted frames directory: {frames_dir}")

# api/views.py


class ChatAPIView(APIView):
    """
    1. Store raw bytes in DB (fast).
    2. Fire & forget Celery task.
    3. Return task_id for polling.
    """

    def post(self, request):
        in_file = request.FILES.get("video")
        fps = int(request.POST.get("frame_count", 120))

        if not in_file:
            return Response({"error": "No video uploaded"}, status=400)

        raw = in_file.read()
        video_obj = Video_Final.objects.create(
            title=in_file.name,
            data=raw,
            duration=0,   # fill later if you want
        )

        # async extraction
        task = extract_frames_task.delay(video_obj.id, fps)

        return Response(
            {"task_id": task.id, "video_id": video_obj.id},
            status=status.HTTP_202_ACCEPTED,
        )
    


class TaskStatusView(APIView):
    def get(self, request, task_id):
        res = AsyncResult(task_id, app=app)
        if res.successful():
            data = res.result
            # fetch frames & base64‑encode for UI
            frames = Frame.objects.filter(video_id=data["video_id"]).order_by("frame_number")
            encoded = [
                {
                    "frame_number": f.frame_number,
                    "src": "data:image/png;base64," + base64.b64encode(f.frame_data).decode()
                } for f in frames
            ]
            return Response({"status": "done", "frames": encoded})
        elif res.failed():
            return Response({"status": "failed"}, status=500)
        else:
            return Response({"status": res.status})
