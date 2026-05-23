#!/usr/bin/env python3
"""CLI script to run the offline gameplay ingestion pipeline."""

import argparse
import asyncio
import logging
import sys

from src.pipeline import ingest_clip

# Configure logging to show pipeline progress nicely in the terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("run_ingest")

async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest soccer gameplay video, run parallel frame analysis, and save tactical critiques."
    )
    parser.add_argument("video", type=str, help="Path to the video file (e.g. clip.mp4)")
    parser.add_argument(
        "--out", "-o",
        type=str,
        default="data/clip.json",
        help="Path where to save the analysis JSON store (default: data/clip.json)"
    )
    parser.add_argument(
        "--max-frames", "-f",
        type=int,
        default=None,
        help="Maximum number of frames to sample (for quick testing/demos)"
    )
    parser.add_argument(
        "--transport", "-t",
        type=str,
        default="direct",
        choices=["direct", "rocketride"],
        help="GmiClient transport to use (default: direct)"
    )
    
    args = parser.parse_args()
    
    from src.gmi_client import GmiClient
    client = GmiClient(transport=args.transport)
    
    try:
        logger.info("Initializing VLM Soccer Coach Ingestion Ingest CLI...")
        await ingest_clip(
            video_path=args.video,
            out_path=args.out,
            max_frames=args.max_frames,
            client=client
        )
        logger.info("Ingestion completed successfully! Ingested database saved to: %s", args.out)
    except Exception as e:
        logger.exception("Ingestion pipeline failed")
        sys.exit(1)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
