"""Central configuration loaded from the .env file.

All other modules import constants from here — this is the single seam
for switching models or endpoints.
"""

import logging
import hashlib
import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve paths
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)

# ── GMI Cloud endpoint ───────────────────────────────────────────────────────
GMI_BASE_URL: str = "https://api.gmi-serving.com/v1"

# Required for real GMI calls; kept optional at import time so tests, CLI help,
# and RocketRide-only paths can load without local secrets.
GMI_API_KEY: str = os.environ.get("GMI_API_KEY", "")

# ── Model identifiers ────────────────────────────────────────────────────────
# Using verified GMI Cloud hosted Google models
VISION_MODEL: str = "google/gemini-3.1-flash-lite-preview"
COACH_MODEL: str = "google/gemini-3.1-pro-preview"

# ── Frame-sampling parameters ────────────────────────────────────────────────
SAMPLE_FPS: float = 1.0   # frames per second to extract from video
BUCKET_SEC: int = 5       # seconds per analysis bucket
ANALYZE_CONCURRENCY: int = int(os.environ.get("ANALYZE_CONCURRENCY", "4"))
EVALUATE_CONCURRENCY: int = int(os.environ.get("EVALUATE_CONCURRENCY", "3"))
CLIP_SUMMARY_DIR: str = os.environ.get(
    "ROCKETRIDE_CLIP_SUMMARY_PATH",
    str(BASE_DIR / "data" / "clip_summaries"),
)
TACTICS_DIR: str = os.environ.get(
    "ROCKETRIDE_TACTICS_PATH",
    str(BASE_DIR / "data" / "tactics"),
)

# ── RocketRide configuration ─────────────────────────────────────────────────
ROCKETRIDE_URI: str = os.environ.get("ROCKETRIDE_URI", "ws://127.0.0.1:5565")
ROCKETRIDE_APIKEY: str = os.environ.get("ROCKETRIDE_APIKEY", "MYAPIKEY")
ROCKETRIDE_PIPE_PATH: str = os.environ.get(
    "ROCKETRIDE_PIPE_PATH",
    str(BASE_DIR / "pipelines" / "coach.pipe"),
)
ROCKETRIDE_SOURCE: str = os.environ.get("ROCKETRIDE_SOURCE", "chat_1")

def _default_rocketride_task_token(pipe_path: str, source: str) -> str:
    try:
        digest_source = Path(pipe_path).read_bytes()
    except OSError:
        digest_source = pipe_path.encode("utf-8")
    digest_source += f"\0{source}".encode("utf-8")
    return f"soccer-coach-{hashlib.sha1(digest_source).hexdigest()[:12]}"

ROCKETRIDE_TASK_TOKEN: str = os.environ.get(
    "ROCKETRIDE_TASK_TOKEN",
    _default_rocketride_task_token(ROCKETRIDE_PIPE_PATH, ROCKETRIDE_SOURCE),
)

logger.debug(
    "Config loaded: base_url=%s vision_model=%s coach_model=%s rocketride_uri=%s",
    GMI_BASE_URL,
    VISION_MODEL,
    COACH_MODEL,
    ROCKETRIDE_URI,
)
