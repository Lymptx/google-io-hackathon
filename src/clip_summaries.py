from pathlib import Path

from src.review.schema import FrameRecord
from src.store import RecordStore


def export_clip_summaries(store: RecordStore, out_dir: str) -> Path:
    """Write a compact text summary and chunk it into individual .txt files for parsing."""
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Clean up old generated clip_*.txt files from previous runs
    for path in output_dir.glob("clip_*.txt"):
        try:
            path.unlink()
        except OSError:
            pass
            
    reviews = store.reviews()
    records = store.all_records()
    
    # 2. Generate individual .txt files for each window review matching the mock schema
    for review in reviews:
        t_start = int(review.t_start)
        t_end = int(review.t_end)
        clip_id = f"clip_{t_start:03d}_{t_end:03d}"
        txt_path = output_dir / f"{clip_id}.txt"
        
        # Determine match phase from majority possession
        window_records = [r for r in records if review.t_start <= r.t < review.t_end]
        possession_teams = [r.possession_team for r in window_records if r.possession_team]
        if possession_teams:
            maj_team = max(set(possession_teams), key=possession_teams.count)
            match_phase = f"{maj_team} team build-up and midfield play."
        else:
            match_phase = "Settled possession / transition phase."
            
        # Compile unique events and tags for coaching tags
        tags = set()
        for r in window_records:
            if r.action_tags:
                tags.update(r.action_tags)
            if r.events:
                tags.update(r.events)
        coaching_tags = ", ".join(sorted(list(tags))) if tags else "possession, tactics"
        
        # Primary theme from highlight or notes
        primary_theme = review.highlight or "Tactical build-up progression."
        
        # Build Detailed Sequence combining notes, frame summaries and reviews
        seq_parts = []
        seq_parts.append(f"During this window, the team's overall tactical rating was {review.overall_score}/10.")
        if review.notes:
            seq_parts.append(review.notes)
            
        for r in window_records:
            if r.summary:
                seq_parts.append(f"At {r.t:.1f}s: {r.summary}")
                
        seq_parts.append(
            f"Observed Coaching Performance:\n"
            f"- 6-Second Pressing Rule: {review.conformance_6_second_rule}\n"
            f"- Passing Triangles & Options: {review.conformance_supporting_triangles}\n"
            f"- Wing Spacing & Width: {review.wing_width_analysis}"
        )
        
        detailed_sequence = "\n\n".join(seq_parts)
        
        content = [
            f"Clip ID: {clip_id}",
            f"Match Phase: {match_phase}",
            f"Timestamp: {review.t_start:.1f}s-{review.t_end:.1f}s",
            f"Primary Theme: {primary_theme}",
            "",
            "Detailed Sequence:",
            detailed_sequence,
            "",
            f"Observed Coaching Tags: {coaching_tags}"
        ]
        
        txt_path.write_text("\n".join(content), encoding="utf-8")
        
    # Also write the master markdown file for fallback/UI references
    output_path = output_dir / "clip_summary.md"
    lines = ["# Soccer Clip Tactical Summary", ""]
    
    if reviews:
        for review in reviews:
            lines.extend(
                [
                    f"## Window {review.t_start:.1f}s to {review.t_end:.1f}s",
                    f"Overall score: {review.overall_score}/10",
                    f"Passing score: {review.passing_score}/10",
                    f"Dribbling score: {review.dribbling_score}/10",
                    f"Possession score: {review.possession_score}/10",
                    f"Defending score: {review.defending_score}/10",
                    f"6-second rule: {review.conformance_6_second_rule}",
                    f"Supporting triangles: {review.conformance_supporting_triangles}",
                    f"Wing width: {review.wing_width_analysis}",
                    f"Highlight: {review.highlight}",
                    f"Notes: {review.notes}",
                    "",
                    "Frame evidence:",
                ]
            )
            window_records = [r for r in records if review.t_start <= r.t < review.t_end]
            lines.extend(_format_records(window_records))
            lines.append("")
    else:
        lines.extend(["## Frame Timeline", "", "Frame evidence:"])
        lines.extend(_format_records(records))
        lines.append("")
        
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _format_records(records: list[FrameRecord]) -> list[str]:
    if not records:
        return ["- No frame records available."]
        
    lines = []
    for record in records:
        tags = ", ".join(record.action_tags) if record.action_tags else "none"
        events = ", ".join(record.events) if record.events else "none"
        lines.append(
            "- "
            f"t={record.t:.1f}s | possession={record.possession_team or 'None'} | "
            f"summary={record.summary} | events={events} | tags={tags} | "
            f"width={record.width_maintained} | support_options={record.supporting_options_count} | "
            f"defense={record.defensive_structure} | pressing={record.pressing_intensity}"
        )
    return lines
