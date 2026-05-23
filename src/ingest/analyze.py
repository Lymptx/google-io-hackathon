import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List

from src.config import VISION_MODEL
from src.gmi_client import GmiClient
from src.ingest.frames import FrameRef
from src.review.schema import FrameRecord, coerce_record

logger = logging.getLogger(__name__)

ANALYZE_PROMPT = """Analyze this tactical birdseye-view soccer gameplay frame.
Return a valid JSON object matching this schema EXACTLY:
{
  "summary": "Brief 1-sentence description of the current action in the frame",
  "possession_team": "Red" or "Blue" or "None" (which team has control of the ball),
  "events": ["list of notable tactical actions occurring in this frame, e.g. pass, pressing, turnover, winger run"],
  "action_tags": ["pass", "dribble", "shot", "tackle", "press", "turnover", "possession", "off-ball-run"],
  "width_maintained": true or false (is the team in possession using wide positions on the wings to stretch the opponent block),
  "supporting_options_count": integer (0, 1, or 2+; how many clear short passing options are supporting the ball carrier in a triangle),
  "defensive_structure": "compact triangles" or "stretched" or "loose" or "unknown" (describing the defending team's compactness),
  "pressing_intensity": "immediate" or "delayed" or "none" (if possession was just lost, did nearest defenders immediately press),
  "turnover_third": "defensive" or "middle" or "attacking" or "None" (if a turnover just occurred, in which third of the pitch did it happen)
}

Focus strictly on positional structure and tactical guidelines. Return only a raw JSON object. Do not wrap in backticks or markdown formatting.
"""

async def analyze_frame(client: GmiClient, ref: FrameRef) -> FrameRecord:
    """Analyze a single frame using the vision LLM."""
    logger.debug("Running vision analysis on frame t=%ss", ref.t)
    try:
        raw = await client.vision_json(ref.jpeg_b64, ANALYZE_PROMPT, VISION_MODEL)
        return coerce_record(ref.t, raw)
    except Exception as e:
        logger.error("Failed to analyze frame t=%ss: %s", ref.t, e)
        # Return fallback record
        return coerce_record(ref.t, {})

async def analyze_frames_parallel(client: GmiClient, refs: List[FrameRef]) -> List[FrameRecord]:
    """Analyzes a list of frames concurrently using asyncio.gather."""
    logger.info("Starting parallel analysis of %d frames...", len(refs))
    
    tasks = [analyze_frame(client, ref) for ref in refs]
    records = await asyncio.gather(*tasks)
    
    # Sort by timestamp
    records = sorted(records, key=lambda r: r.t)
    logger.info("Finished parallel analysis.")
    return records
