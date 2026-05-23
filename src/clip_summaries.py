from pathlib import Path

from src.review.schema import FrameRecord
from src.store import RecordStore


def export_clip_summaries(store: RecordStore, out_dir: str) -> Path:
    """Write a compact text summary for RocketRide filesystem indexing."""
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "clip_summary.md"

    lines = ["# Soccer Clip Tactical Summary", ""]

    reviews = store.reviews()
    records = store.all_records()
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
