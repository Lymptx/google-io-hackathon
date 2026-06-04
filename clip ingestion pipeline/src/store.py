import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import List

from src.review.schema import FrameRecord, WindowReview, coerce_record

logger = logging.getLogger(__name__)

class RecordStore:
    """Saves and loads analysis records and reviews from a single JSON database file."""

    def __init__(self, records: List[FrameRecord] = None, window_reviews: List[WindowReview] = None) -> None:
        self.records: List[FrameRecord] = records or []
        self.window_reviews: List[WindowReview] = window_reviews or []

    def all_records(self) -> List[FrameRecord]:
        return self.records

    def reviews(self) -> List[WindowReview]:
        return self.window_reviews

    def save(self, path: str) -> None:
        """Serializes records and window reviews to a JSON file."""
        logger.info("Saving database store to %s", path)
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "records": [asdict(r) for r in self.records],
            "window_reviews": [asdict(w) for w in self.window_reviews]
        }
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info("Store saved successfully.")

    @classmethod
    def load(cls, path: str) -> "RecordStore":
        """Deserializes records and window reviews from a JSON file."""
        logger.info("Loading database store from %s", path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.warning("Store file not found at %s. Returning empty store.", path)
            return cls()
            
        records_raw = data.get("records", [])
        records = [coerce_record(r["t"], r) for r in records_raw]
        
        reviews_raw = data.get("window_reviews", [])
        reviews = []
        for rw in reviews_raw:
            reviews.append(WindowReview(
                t_start=float(rw["t_start"]),
                t_end=float(rw["t_end"]),
                overall_score=float(rw["overall_score"]),
                passing_score=float(rw["passing_score"]),
                dribbling_score=float(rw["dribbling_score"]),
                possession_score=float(rw["possession_score"]),
                defending_score=float(rw["defending_score"]),
                conformance_6_second_rule=str(rw["conformance_6_second_rule"]),
                conformance_supporting_triangles=str(rw["conformance_supporting_triangles"]),
                wing_width_analysis=str(rw["wing_width_analysis"]),
                highlight=str(rw["highlight"]),
                notes=str(rw["notes"])
            ))
            
        logger.info("Loaded %d records and %d reviews", len(records), len(reviews))
        return cls(records=records, window_reviews=reviews)
