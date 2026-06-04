from src.review.schema import coerce_record, FrameRecord

def test_coerce_record_full():
    raw = {
        "summary": "Midfielder receives ball under pressure",
        "possession_team": "Red",
        "events": ["pass completed", "pressing"],
        "action_tags": ["pass", "press"],
        "width_maintained": True,
        "supporting_options_count": 2,
        "defensive_structure": "compact triangles",
        "pressing_intensity": "immediate",
        "turnover_third": "middle",
        "sequence_note": "Possession secured under pressure"
    }
    record = coerce_record(5.0, raw)
    
    assert record.t == 5.0
    assert record.summary == "Midfielder receives ball under pressure"
    assert record.possession_team == "Red"
    assert record.events == ["pass completed", "pressing"]
    assert record.action_tags == ["pass", "press"]
    assert record.width_maintained is True
    assert record.supporting_options_count == 2
    assert record.defensive_structure == "compact triangles"
    assert record.pressing_intensity == "immediate"
    assert record.turnover_third == "middle"
    assert record.sequence_note == "Possession secured under pressure"

def test_coerce_record_missing():
    raw = {}
    record = coerce_record(10.0, raw)
    
    assert record.t == 10.0
    assert record.summary == ""
    assert record.possession_team is None
    assert record.events == []
    assert record.action_tags == []
    assert record.width_maintained is False
    assert record.supporting_options_count == 0
    assert record.defensive_structure == "unknown"
    assert record.pressing_intensity == "none"
    assert record.turnover_third is None
    assert record.sequence_note == ""

def test_coerce_record_wrong_types():
    raw = {
        "summary": 12345,
        "possession_team": None,
        "events": "single event string",
        "action_tags": None,
        "width_maintained": "true",
        "supporting_options_count": "3",
        "defensive_structure": None,
        "pressing_intensity": 9.5,
        "turnover_third": "wrong_third",
        "sequence_note": {}
    }
    record = coerce_record(15.0, raw)
    
    assert record.t == 15.0
    assert record.summary == "12345"
    assert record.possession_team is None
    assert record.events == ["single event string"]
    assert record.action_tags == []
    assert record.width_maintained is True
    assert record.supporting_options_count == 3
    assert record.defensive_structure == "None"
    assert record.pressing_intensity == "9.5"
    assert record.turnover_third is None
    assert record.sequence_note == "{}"
