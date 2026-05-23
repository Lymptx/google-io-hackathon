import logging
import time
from typing import Optional

from src.gmi_client import GmiClient
from src.ingest.frames import sample_frames
from src.ingest.analyze import analyze_frames_parallel
from src.review.evaluator import bucket_records, evaluate_buckets_parallel
from src.store import RecordStore

logger = logging.getLogger(__name__)

async def ingest_clip(
    video_path: str,
    out_path: str,
    client: Optional[GmiClient] = None,
    max_frames: Optional[int] = None,
) -> RecordStore:
    """Orchestrates the entire offline/startup video ingestion pipeline."""
    start_time = time.time()
    logger.info("Starting ingestion pipeline for %s...", video_path)
    
    if client is None:
        client = GmiClient(transport="direct")
        
    # 1. Sample frames at 1 fps
    frames = sample_frames(video_path, max_frames=max_frames)
    if not frames:
        raise ValueError(f"No frames sampled from video: {video_path}")
        
    # 2. Concurrently analyze frames
    records = await analyze_frames_parallel(client, frames)
    
    # 3. Group records into buckets
    buckets = bucket_records(records)
    
    # 4. Concurrently evaluate buckets
    reviews = await evaluate_buckets_parallel(client, buckets)
    
    # 5. Create store and save to disk
    store = RecordStore(records=records, window_reviews=reviews)
    store.save(out_path)
    
    elapsed = time.time() - start_time
    logger.info(
        "Ingestion pipeline completed in %.2fs. Processed %d frames and %d buckets.",
        elapsed, len(records), len(buckets)
    )
    return store
