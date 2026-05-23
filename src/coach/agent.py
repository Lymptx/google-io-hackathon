import logging
import json
from pathlib import Path
from typing import Dict, Any, List

from src.config import COACH_MODEL
from src.gmi_client import GmiClient
from src.store import RecordStore

logger = logging.getLogger(__name__)

def build_context(store: RecordStore) -> str:
    """Renders all frame records and window reviews into a compact, highly structured text context for the LLM."""
    lines = []
    
    # 1. Append WindowReviews (high-level summaries)
    lines.append("=== TACTICAL WINDOW REVIEWS (5s Intervals) ===")
    for rw in store.reviews():
        lines.append(
            f"[{rw.t_start}s - {rw.t_end}s] "
            f"Overall Score: {rw.overall_score}/10, Passing: {rw.passing_score}, Defending: {rw.defending_score}\n"
            f"  - 6-Sec Rule: {rw.conformance_6_second_rule}\n"
            f"  - Supporting Triangles: {rw.conformance_supporting_triangles}\n"
            f"  - Wing Width: {rw.wing_width_analysis}\n"
            f"  - Highlight: {rw.highlight}\n"
            f"  - Notes: {rw.notes}\n"
        )
        
    # 2. Append FrameRecords (granular timeline)
    lines.append("=== RAW GAMEPLAY TIMELINE (1 fps) ===")
    for r in store.all_records():
        lines.append(
            f"t={r.t}s | Possession: {r.possession_team or 'None'} | "
            f"Summary: {r.summary} | "
            f"Tags: {', '.join(r.action_tags)} | "
            f"Width: {r.width_maintained} | "
            f"Passing Options: {r.supporting_options_count} | "
            f"Defending: {r.defensive_structure} | "
            f"Pressing: {r.pressing_intensity}"
        )
        
    return "\n".join(lines)

def _load_coach_context() -> str:
    """Loads tactical philosophy context."""
    try:
        context_path = Path(__file__).resolve().parent.parent.parent / "coach_context.txt"
        if context_path.exists():
            return context_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning("Could not load coach_context.txt: %s", e)
    return "High defensive pressing (6-second rule), positional wing width, and passing triangles."

COACH_AGENT_SYSTEM_PROMPT = """You are the elite AI Soccer Coaching Assistant, an expert advisor to the Head Coach.
Your tactical philosophy matches the Active Game Plan below.

=== ACTIVE GAME PLAN ===
{coach_context}

=== ROLE & RULES ===
1. You answer the coach's natural-language questions based ONLY on the provided Match Ingestion Context.
2. Be brief, direct, and professional in your answers (limit to 3-4 concise sentences).
3. If the coach asks about specific events, cite the precise timestamps (in seconds) of the frames or windows you used.
4. You MUST return a valid JSON object matching this schema EXACTLY:
{{
  "answer": "Detailed answer matching coach's query",
  "cited_timestamps": [float]  // list of timestamps (seconds) cited in the answer
}}

Return only a raw JSON object. Do not wrap in backticks or markdown formatting.
"""

async def answer(client: GmiClient, query: str, store: RecordStore) -> Dict[str, Any]:
    """Uses the GmiClient (routed through GMI direct or RocketRide) to answer the coach's query."""
    logger.info("Answering coach query: %s", query)
    
    coach_context = _load_coach_context()
    ingest_context = build_context(store)
    
    sys_prompt = COACH_AGENT_SYSTEM_PROMPT.format(coach_context=coach_context)
    user_prompt = f"### QUESTION FROM HEAD COACH:\n{query}\n\n### MATCH INGESTION CONTEXT:\n{ingest_context}"
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        raw = await client.chat_json(messages, model=COACH_MODEL)
        
        # Ensure correct output keys
        return {
            "answer": str(raw.get("answer", "I could not formulate an answer.")),
            "cited_timestamps": [float(x) for x in raw.get("cited_timestamps", [])]
        }
    except Exception as e:
        logger.error("Failed to generate coach answer: %s", e)
        return {
            "answer": f"Error during analysis: {e}",
            "cited_timestamps": []
        }
