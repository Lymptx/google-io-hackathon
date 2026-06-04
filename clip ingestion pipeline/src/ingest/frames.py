import cv2
import base64
import logging
from typing import NamedTuple, List, Optional

logger = logging.getLogger(__name__)

class FrameRef(NamedTuple):
    t: float
    jpeg_b64: str

def frame_timestamps(duration_sec: float, fps: float) -> List[float]:
    """Generates pure timestamps at a given rate."""
    if duration_sec <= 0 or fps <= 0:
        return []
    
    num_frames = int(duration_sec * fps)
    return [float(i) / fps for i in range(num_frames)]

def sample_frames(video_path: str, fps: float = 1.0, max_frames: Optional[int] = None) -> List[FrameRef]:
    """Samples frames from a video at a fixed FPS, returning list of base64 JPEG references."""
    logger.info("Sampling frames from video %s at %s fps", video_path, fps)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video file: {video_path}")
        
    try:
        # Get video properties
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        
        if video_fps <= 0 or total_frames <= 0:
            raise ValueError(f"Invalid video metadata: FPS={video_fps}, frames={total_frames}")
            
        duration_sec = total_frames / video_fps
        logger.info("Video specs: FPS=%s, total_frames=%s, duration=%ss", video_fps, total_frames, duration_sec)
        
        timestamps = frame_timestamps(duration_sec, fps)
        if max_frames:
            timestamps = timestamps[:max_frames]
            
        sampled = []
        for t in timestamps:
            # Seek to milliseconds
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
            ret, frame = cap.read()
            if not ret:
                logger.warning("Could not read frame at timestamp %ss", t)
                continue
                
            # Compress to JPEG
            success, buffer = cv2.imencode(".jpg", frame)
            if not success:
                logger.warning("Could not encode frame at timestamp %ss", t)
                continue
                
            # Convert to base64
            b64_str = base64.b64encode(buffer).decode("utf-8")
            sampled.append(FrameRef(t=t, jpeg_b64=b64_str))
            
        logger.info("Successfully sampled %d frames", len(sampled))
        return sampled
        
    finally:
        cap.release()
