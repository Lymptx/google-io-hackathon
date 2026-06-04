import pytest
from src.review.schema import FrameRecord, WindowReview
from src.store import RecordStore
from src.coach.agent import build_context, answer

def test_build_context():
    r = FrameRecord(
        t=1.0,
        summary="Test frame",
        possession_team="Red",
        events=[],
        action_tags=["pass"],
        width_maintained=True,
        supporting_options_count=2,
        defensive_structure="compact triangles",
        pressing_intensity="none",
        turnover_third=None
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
    store = RecordStore(records=[r], window_reviews=[w])
    context = build_context(store)
    
    assert "t=1.0s" in context
    assert "Overall Score: 7.0/10" in context
    assert "Rule conformed" in context

class MockCoachAgentClient:
    async def chat_json(self, messages, model):
        return {
            "answer": "Red conformed to the 6-second rule by pressing immediately at 3.0s.",
            "cited_timestamps": [3.0]
        }

@pytest.mark.asyncio
async def test_coach_agent_answer():
    client = MockCoachAgentClient()
    store = RecordStore(records=[], window_reviews=[])
    res = await answer(client, "Did we follow the 6-second rule?", store)
    
    assert res["answer"] == "Red conformed to the 6-second rule by pressing immediately at 3.0s."
    assert res["cited_timestamps"] == [3.0]
