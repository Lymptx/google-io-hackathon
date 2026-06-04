from src.ingest.frames import frame_timestamps

def test_frame_timestamps_1fps_30s():
    timestamps = frame_timestamps(30.0, 1.0)
    assert len(timestamps) == 30
    assert timestamps[0] == 0.0
    assert timestamps[-1] == 29.0

def test_frame_timestamps_2fps_5s():
    timestamps = frame_timestamps(5.0, 2.0)
    assert len(timestamps) == 10
    assert timestamps[0] == 0.0
    assert timestamps[1] == 0.5
    assert timestamps[-1] == 4.5

def test_frame_timestamps_invalid():
    assert frame_timestamps(0, 1.0) == []
    assert frame_timestamps(10, 0) == []
    assert frame_timestamps(-5, 1.0) == []
