import pytest
from src.review.schema import FrameRecord, WindowReview
from src.review.evaluator import bucket_records, evaluate_bucket, evaluate_buckets_parallel, Bucket

def _dummy_record(t):
    return FrameRecord(
        t=t,
        summary="",
        possession_team="Red",
        events=[],
        action_tags=[],
        width_maintained=True,
        supporting_options_count=2,
        defensive_structure="compact triangles",
        pressing_intensity="none",
        turnover_third=None
    )

def test_bucket_records_5s():
    records = [_dummy_record(0.0), _dummy_record(2.5), _dummy_record(4.9), _dummy_record(5.0), _dummy_record(9.9)]
    buckets = bucket_records(records, bucket_sec=5.0)
    
    assert len(buckets) == 2
    assert buckets[0].t_start == 0.0
    assert buckets[0].t_end == 5.0
    assert len(buckets[0].records) == 3
    
    assert buckets[1].t_start == 5.0
    assert buckets[1].t_end == 10.0
    assert len(buckets[1].records) == 2

class MockChatClient:
    async def chat_json(self, messages, model):
        return {
            "overall_score": 8.0,
            "passing_score": 8.5,
            "dribbling_score": 7.0,
            "possession_score": 9.0,
            "defending_score": 7.5,
            "conformance_6_second_rule": "Conformed.",
            "conformance_supporting_triangles": "Triangles maintained.",
            "wing_width_analysis": "Wings utilized.",
            "highlight": "Great winger pass.",
            "notes": "Excellent performance."
        }

@pytest.mark.asyncio
async def test_evaluate_bucket():
    client = MockChatClient()
    bucket = Bucket(t_start=0.0, t_end=5.0, records=[_dummy_record(1.0)])
    review = await evaluate_bucket(client, bucket)
    
    assert isinstance(review, WindowReview)
    assert review.overall_score == 8.0
    assert review.passing_score == 8.5
    assert review.conformance_6_second_rule == "Conformed."
