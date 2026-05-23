import pytest
from src.ingest.frames import FrameRef
from src.ingest.analyze import analyze_frame, analyze_frames_parallel
from src.review.schema import FrameRecord

class MockClient:
    async def vision_json(self, image_b64, prompt, model):
        return {
            "summary": "Red midfielder passes to right winger",
            "possession_team": "Red",
            "events": ["pass"],
            "action_tags": ["pass"],
            "width_maintained": True,
            "supporting_options_count": 2,
            "defensive_structure": "compact triangles",
            "pressing_intensity": "none",
            "turnover_third": None
        }

@pytest.mark.asyncio
async def test_analyze_frame():
    client = MockClient()
    ref = FrameRef(t=2.0, jpeg_b64="test")
    record = await analyze_frame(client, ref)
    
    assert isinstance(record, FrameRecord)
    assert record.t == 2.0
    assert record.summary == "Red midfielder passes to right winger"
    assert record.possession_team == "Red"
    assert record.width_maintained is True
    assert record.supporting_options_count == 2

@pytest.mark.asyncio
async def test_analyze_frames_parallel():
    client = MockClient()
    refs = [
        FrameRef(t=2.0, jpeg_b64="test"),
        FrameRef(t=1.0, jpeg_b64="test")
    ]
    records = await analyze_frames_parallel(client, refs)
    
    assert len(records) == 2
    # Ensure they are sorted by timestamp
    assert records[0].t == 1.0
    assert records[1].t == 2.0
