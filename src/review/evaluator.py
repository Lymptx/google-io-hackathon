import logging
import json
import asyncio
from typing import NamedTuple, List, Dict, Any
from pathlib import Path

from src.config import VISION_MODEL, BUCKET_SEC
from src.gmi_client import GmiClient
from src.review.schema import FrameRecord, WindowReview

logger = logging.getLogger(__name__)

class Bucket(NamedTuple):
    t_start: float
    t_end: float
    records: List[FrameRecord]

def bucket_records(records: List[FrameRecord], bucket_sec: float = BUCKET_SEC) -> List[Bucket]:
    """Pure helper that groups frame records into fixed-interval temporal windows."""
    if not records:
        return []
        
    # Sort just in case
    sorted_records = sorted(records, key=lambda r: r.t)
    max_t = sorted_records[-1].t
    
    buckets = []
    t_start = 0.0
    while t_start <= max_t:
        t_end = t_start + bucket_sec
        # Filter records falling in [t_start, t_end)
        bucket_recs = [r for r in sorted_records if t_start <= r.t < t_end]
        if bucket_recs:
            buckets.append(Bucket(t_start=t_start, t_end=t_end, records=bucket_recs))
        t_start = t_end
        
    return buckets

EVALUATOR_PROMPT_TEMPLATE = """You are an elite Soccer Tactical Analyst. Evaluate this {duration}s match chunk ({t_start}s to {t_end}s) against the Coach's Game Plan.

=== ACTIVE COACH GAME PLAN ===
{coach_context}

=== MATCH CHUNK DATA (1 fps FrameRecords) ===
{records_json}

=== INSTRUCTIONS ===
Evaluate the team's performance in this window. Analyze if they conformed to the guidelines or committed violations.
Return a valid JSON object matching this schema EXACTLY:
{{
  "overall_score": float (0.0 to 10.0),
  "passing_score": float (0.0 to 10.0),
  "dribbling_score": float (0.0 to 10.0),
  "possession_score": float (0.0 to 10.0),
  "defending_score": float (0.0 to 10.0),
  "conformance_6_second_rule": "1-sentence review of how well out-of-possession pressing traps conformed to the immediate 6-second rule upon turnover",
  "conformance_supporting_triangles": "1-sentence review of whether the ball carrier had at least two supporting passing options",
  "wing_width_analysis": "1-sentence review of whether width was maintained on the wings to stretch the defensive block",
  "highlight": "1-sentence highlight of the single most tactically significant moment in this window",
  "notes": "General observations or tactical critique of player movements"
}}

Return only a raw JSON object. Do not wrap in backticks or markdown formatting.
"""

def _load_coach_context() -> str:
    """Loads active game plan guidelines."""
    try:
        context_path = Path(__file__).resolve().parent.parent.parent / "coach_context.txt"
        if context_path.exists():
            return context_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("Could not load coach_context.txt: %s", e)
    return "High defensive pressing (6-second rule), positional wing width, and passing triangles."

async def evaluate_bucket(client: GmiClient, bucket: Bucket) -> WindowReview:
    """Invokes the consolidated GMI Critic LLM for a single temporal bucket."""
    logger.debug("Evaluating bucket %s to %ss", bucket.t_start, bucket.t_end)
    
    coach_context = _load_coach_context()
    
    # Serialize bucket records to clean JSON list for the LLM
    records_list = []
    for r in bucket.records:
        records_list.append({
            "t": r.t,
            "summary": r.summary,
            "possession_team": r.possession_team,
            "events": r.events,
            "action_tags": r.action_tags,
            "width_maintained": r.width_maintained,
            "supporting_options_count": r.supporting_options_count,
            "defensive_structure": r.defensive_structure,
            "pressing_intensity": r.pressing_intensity,
            "turnover_third": r.turnover_third,
        })
        
    records_json = json.dumps(records_list, indent=2)
    
    prompt = EVALUATOR_PROMPT_TEMPLATE.format(
        duration=int(bucket.t_end - bucket.t_start),
        t_start=bucket.t_start,
        t_end=bucket.t_end,
        coach_context=coach_context,
        records_json=records_json,
    )
    
    try:
        raw = await client.chat_json(
            messages=[{"role": "user", "content": prompt}],
            model=VISION_MODEL  # Use Flash-Lite for cheap and fast reviews
        )
        
        # Extract and parse with safety fallbacks
        return WindowReview(
            t_start=bucket.t_start,
            t_end=bucket.t_end,
            overall_score=float(raw.get("overall_score", 5.0)),
            passing_score=float(raw.get("passing_score", 5.0)),
            dribbling_score=float(raw.get("dribbling_score", 5.0)),
            possession_score=float(raw.get("possession_score", 5.0)),
            defending_score=float(raw.get("defending_score", 5.0)),
            conformance_6_second_rule=str(raw.get("conformance_6_second_rule", "Not observed.")),
            conformance_supporting_triangles=str(raw.get("conformance_supporting_triangles", "Not observed.")),
            wing_width_analysis=str(raw.get("wing_width_analysis", "Not observed.")),
            highlight=str(raw.get("highlight", "No clear highlight.")),
            notes=str(raw.get("notes", ""))
        )
    except Exception as e:
        logger.error("Failed to evaluate bucket %s to %ss: %s", bucket.t_start, bucket.t_end, e)
        # Fallback WindowReview
        return WindowReview(
            t_start=bucket.t_start,
            t_end=bucket.t_end,
            overall_score=5.0,
            passing_score=5.0,
            dribbling_score=5.0,
            possession_score=5.0,
            defending_score=5.0,
            conformance_6_second_rule="Evaluation failed.",
            conformance_supporting_triangles="Evaluation failed.",
            wing_width_analysis="Evaluation failed.",
            highlight="Error during evaluation.",
            notes=str(e)
        )

async def evaluate_buckets_parallel(client: GmiClient, buckets: List[Bucket]) -> List[WindowReview]:
    """Evaluates all buckets in parallel."""
    logger.info("Starting parallel evaluation of %d buckets...", len(buckets))
    tasks = [evaluate_bucket(client, b) for b in buckets]
    reviews = await asyncio.gather(*tasks)
    logger.info("Finished parallel evaluation.")
    return sorted(reviews, key=lambda x: x.t_start)
