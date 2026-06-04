from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass(frozen=True)
class FrameRecord:
    t: float
    summary: str
    possession_team: Optional[str]
    events: List[str]
    action_tags: List[str]
    
    # Specific tactical indicators mapped to coach_context.txt
    width_maintained: bool
    supporting_options_count: int  # Ball carrier passing options (0, 1, 2+)
    defensive_structure: str      # e.g., "compact triangles", "stretched", "loose"
    pressing_intensity: str        # e.g., "immediate", "delayed", "none"
    turnover_third: Optional[str]   # "defensive", "middle", "attacking"
    sequence_note: str = ""

@dataclass(frozen=True)
class WindowReview:
    t_start: float
    t_end: float
    overall_score: float
    passing_score: float
    dribbling_score: float
    possession_score: float
    defending_score: float
    conformance_6_second_rule: str
    conformance_supporting_triangles: str
    wing_width_analysis: str
    highlight: str
    notes: str

def coerce_record(t: float, raw: dict) -> FrameRecord:
    """Defensively coerces a dictionary from GMI Cloud into a FrameRecord."""
    if not isinstance(raw, dict):
        raw = {}
        
    summary = str(raw.get("summary", ""))
    
    poss_team = raw.get("possession_team")
    if poss_team is not None:
        poss_team = str(poss_team)
        if poss_team.lower() in ("none", "null", ""):
            poss_team = None
            
    # Coerce list fields
    events_raw = raw.get("events", [])
    if isinstance(events_raw, list):
        events = [str(x) for x in events_raw]
    else:
        events = [str(events_raw)] if events_raw else []
        
    tags_raw = raw.get("action_tags", [])
    if isinstance(tags_raw, list):
        action_tags = [str(x) for x in tags_raw]
    else:
        action_tags = [str(tags_raw)] if tags_raw else []
        
    # Coerce tactical indicators
    width_maintained = raw.get("width_maintained")
    if isinstance(width_maintained, bool):
        pass
    elif isinstance(width_maintained, str):
        width_maintained = width_maintained.lower() in ("true", "yes", "1")
    else:
        width_maintained = False
        
    try:
        supporting_options_count = int(raw.get("supporting_options_count", 0))
    except (ValueError, TypeError):
        supporting_options_count = 0
        
    defensive_structure = str(raw.get("defensive_structure", "unknown"))
    pressing_intensity = str(raw.get("pressing_intensity", "none"))
    
    turnover_third = raw.get("turnover_third")
    if turnover_third is not None:
        turnover_third = str(turnover_third)
        if turnover_third.lower() not in ("defensive", "middle", "attacking"):
            turnover_third = None
            
    sequence_note = str(raw.get("sequence_note", ""))
    
    return FrameRecord(
        t=t,
        summary=summary,
        possession_team=poss_team,
        events=events,
        action_tags=action_tags,
        width_maintained=width_maintained,
        supporting_options_count=supporting_options_count,
        defensive_structure=defensive_structure,
        pressing_intensity=pressing_intensity,
        turnover_third=turnover_third,
        sequence_note=sequence_note,
    )
