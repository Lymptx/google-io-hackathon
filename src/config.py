"""Central configuration loaded from the .env file.

All other modules import constants from here — this is the single seam
for switching models or endpoints.
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve paths
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)

# ── GMI Cloud endpoint ───────────────────────────────────────────────────────
GMI_BASE_URL: str = "https://api.gmi-serving.com/v1"

# Raises KeyError immediately at import time if the secret is missing (fail fast).
GMI_API_KEY: str = os.environ["GMI_API_KEY"]

# ── Model identifiers ────────────────────────────────────────────────────────
# Using verified GMI Cloud hosted Google models
VISION_MODEL: str = "google/gemini-3.1-flash-lite-preview"
COACH_MODEL: str = "google/gemini-3.1-pro-preview"

# ── Frame-sampling parameters ────────────────────────────────────────────────
SAMPLE_FPS: float = 1.0   # frames per second to extract from video
BUCKET_SEC: int = 5       # seconds per analysis bucket

# ── RocketRide configuration ─────────────────────────────────────────────────
ROCKETRIDE_URI: str = os.environ.get("ROCKETRIDE_URI", "ws://127.0.0.1:5565")
ROCKETRIDE_APIKEY: str = os.environ.get("ROCKETRIDE_APIKEY", "MYAPIKEY")
ROCKETRIDE_PIPE_PATH: str = str(BASE_DIR / "pipelines" / "coach.pipe")

logger.debug(
    "Config loaded: base_url=%s vision_model=%s coach_model=%s rocketride_uri=%s",
    GMI_BASE_URL,
    VISION_MODEL,
    COACH_MODEL,
    ROCKETRIDE_URI,
)
