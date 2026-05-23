from src.clip_summaries import export_clip_summaries
from src.review.schema import FrameRecord, WindowReview
from src.store import RecordStore


def test_export_clip_summaries(tmp_path):
    record = FrameRecord(
        t=1.0,
        summary="Red midfielder finds the winger.",
        possession_team="Red",
        events=["pass"],
        action_tags=["pass"],
        width_maintained=True,
        supporting_options_count=2,
        defensive_structure="stretched",
        pressing_intensity="none",
        turnover_third=None,
    )
    review = WindowReview(
        t_start=0.0,
        t_end=5.0,
        overall_score=8.0,
        passing_score=8.5,
        dribbling_score=7.0,
        possession_score=8.0,
        defending_score=7.5,
        conformance_6_second_rule="No turnover observed.",
        conformance_supporting_triangles="Two support options were present.",
        wing_width_analysis="Width was maintained.",
        highlight="Quick pass into the wide channel.",
        notes="Good attacking structure.",
    )

    path = export_clip_summaries(RecordStore([record], [review]), str(tmp_path))
    text = path.read_text(encoding="utf-8")

    assert path.name == "clip_summary.md"
    assert "Window 0.0s to 5.0s" in text
    assert "Red midfielder finds the winger." in text
    assert "support_options=2" in text
