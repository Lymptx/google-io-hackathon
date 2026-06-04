import tempfile
import os
from src.review.schema import FrameRecord, WindowReview
from src.store import RecordStore

def test_store_roundtrip():
    r = FrameRecord(
        t=1.0,
        summary="Test frame",
        possession_team="Red",
        events=["event1"],
        action_tags=["pass"],
        width_maintained=True,
        supporting_options_count=2,
        defensive_structure="compact triangles",
        pressing_intensity="immediate",
        turnover_third="middle",
        sequence_note="Seq note"
    )
    w = WindowReview(
        t_start=0.0,
        t_end=5.0,
        overall_score=7.0,
        passing_score=7.5,
        dribbling_score=6.0,
        possession_score=8.0,
        defending_score=6.5,
        conformance_6_second_rule="Rule conformed",
        conformance_supporting_triangles="Triangles met",
        wing_width_analysis="Width utilized",
        highlight="Highlight",
        notes="Notes"
    )
    
    store1 = RecordStore(records=[r], window_reviews=[w])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "db.json")
        store1.save(db_path)
        
        # Load from disk
        store2 = RecordStore.load(db_path)
        
        assert len(store2.records) == 1
        assert store2.records[0].t == 1.0
        assert store2.records[0].summary == "Test frame"
        assert store2.records[0].possession_team == "Red"
        assert store2.records[0].width_maintained is True
        
        assert len(store2.window_reviews) == 1
        assert store2.window_reviews[0].overall_score == 7.0
        assert store2.window_reviews[0].conformance_6_second_rule == "Rule conformed"
