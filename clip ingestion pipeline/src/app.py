import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path

from src.clip_summaries import export_clip_summaries
from src.config import CLIP_SUMMARY_DIR, TACTICS_DIR
from src.gmi_client import GmiClient
from src.store import RecordStore
from src.coach.agent import answer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "clip.json"

store = RecordStore()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager for loading the database store on startup."""
    global store
    logger.info("Starting FastAPI application. Loading database store...")
    
    # Create data directory if missing
    os.makedirs(BASE_DIR / "data", exist_ok=True)
    
    # Try to load existing db, otherwise create a mock demo dataset if missing so the UI is immediately functional
    if DB_PATH.exists():
        store = RecordStore.load(str(DB_PATH))
    else:
        logger.info("No db found at %s. Creating rich mock tactical database for immediately functional UI...", DB_PATH)
        from src.review.schema import FrameRecord, WindowReview
        mock_records = [
            FrameRecord(
                t=0.0,
                summary="Red team kick-off. Winger wide on the right flank, establishing positional structure.",
                possession_team="Red",
                events=["kick-off", "wing-play"],
                action_tags=["possession"],
                width_maintained=True,
                supporting_options_count=2,
                defensive_structure="loose",
                pressing_intensity="none",
                turnover_third=None,
                sequence_note="Positional structure established."
            ),
            FrameRecord(
                t=1.0,
                summary="Red midfielder slides a quick diagonal pass through the middle third.",
                possession_team="Red",
                events=["pass completed"],
                action_tags=["pass"],
                width_maintained=True,
                supporting_options_count=2,
                defensive_structure="stretched",
                pressing_intensity="none",
                turnover_third=None,
                sequence_note="Rhythm pass completed in midfield."
            ),
            FrameRecord(
                t=2.0,
                summary="Midfield turnover. Blue midfielder intercepts a hasty Red pass in the middle third.",
                possession_team="Blue",
                events=["turnover", "interception"],
                action_tags=["turnover"],
                width_maintained=False,
                supporting_options_count=1,
                defensive_structure="compact",
                pressing_intensity="none",
                turnover_third="middle",
                sequence_note="Turnover in the middle third."
            ),
            FrameRecord(
                t=3.0,
                summary="Red midfielders immediately press the Blue ball carrier, forming a compact defensive triangle.",
                possession_team="Blue",
                events=["defensive-press", "crowding"],
                action_tags=["press"],
                width_maintained=False,
                supporting_options_count=0,
                defensive_structure="compact triangles",
                pressing_intensity="immediate",
                turnover_third=None,
                sequence_note="Defensive counterpress triggered."
            ),
            FrameRecord(
                t=4.0,
                summary="Possession recovered by Red team. Red midfielder tackles Blue and secures the ball in opponent half.",
                possession_team="Red",
                events=["possession-recovered", "tackle"],
                action_tags=["tackle", "possession"],
                width_maintained=False,
                supporting_options_count=2,
                defensive_structure="loose",
                pressing_intensity="none",
                turnover_third=None,
                sequence_note="Possession recovered within 2 seconds (6-second rule met)."
            ),
            FrameRecord(
                t=5.0,
                summary="Red circulating ball in attacking third, maintaining width.",
                possession_team="Red",
                events=["passing-sequence"],
                action_tags=["pass"],
                width_maintained=True,
                supporting_options_count=2,
                defensive_structure="stretched",
                pressing_intensity="none",
                turnover_third=None,
                sequence_note="Build-up play restarted."
            )
        ]
        mock_reviews = [
            WindowReview(
                t_start=0.0,
                t_end=5.0,
                overall_score=8.5,
                passing_score=8.0,
                dribbling_score=7.0,
                possession_score=9.0,
                defending_score=9.5,
                conformance_6_second_rule="Excellent. Red team recovered possession within 2.0 seconds of turnover at 2.0s.",
                conformance_supporting_triangles="Conformed. Red ball carrier maintained at least two passing options consistently.",
                wing_width_analysis="Strong wing play. Right winger stretched Blue block at 0.0s.",
                highlight="Superb immediate counter-press at 3.0s forcing a quick recovery at 4.0s.",
                notes="Red team executed positional structure beautifully. Passing was crisp and the 6-second defensive transition was top class."
            )
        ]
        store = RecordStore(records=mock_records, window_reviews=mock_reviews)
        store.save(str(DB_PATH))

    export_clip_summaries(store, CLIP_SUMMARY_DIR)
        
    yield
    logger.info("Shutting down FastAPI application.")

app = FastAPI(
    title="VLM Soccer Coach Dashboard",
    description="Tactical analytics and query system for soccer gameplay clips.",
    lifespan=lifespan
)

# Setup Jinja2 templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

class AskRequest(BaseModel):
    query: str
    transport: str = "direct"  # "direct" or "rocketride"

def _safe_upload_name(filename: str) -> str:
    name = Path(filename or "tactics.txt").name.strip()
    safe = "".join(ch if ch.isalnum() or ch in " .-_" else "_" for ch in name)
    return safe or "tactics.txt"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Renders the main Coach dashboard."""
    # We pass the store reviews and records to the dashboard for visualization
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "reviews": [w.__dict__ for w in store.reviews()],
            "records": [r.__dict__ for r in store.all_records()]
        }
    )

@app.post("/ask")
async def ask_coach(req: AskRequest):
    """Answers a tactical coaching query using GMI Cloud / RocketRide."""
    logger.info("Received query: %s (transport: %s)", req.query, req.transport)
    
    # Establish GmiClient with selected transport
    client = GmiClient(transport=req.transport)
    try:
        res = await answer(client, req.query, store)
        return JSONResponse(content=res)
    except Exception as e:
        logger.exception("Error handling coach query")
        return JSONResponse(
            status_code=500,
            content={"answer": f"Backend Error: {e}", "cited_timestamps": []}
        )
    finally:
        await client.close()

@app.get("/api/store")
async def get_store():
    """Endpoint to inspect currently loaded records and reviews."""
    return {
        "records": [r.__dict__ for r in store.all_records()],
        "reviews": [w.__dict__ for w in store.reviews()]
    }

@app.get("/api/tactics")
async def list_tactics():
    """Lists tactics files available for RocketRide filesystem indexing."""
    tactics_dir = Path(TACTICS_DIR)
    if not tactics_dir.exists():
        return {"files": []}

    files = []
    for path in sorted(tactics_dir.iterdir()):
        if path.is_file():
            files.append({"filename": path.name, "size": path.stat().st_size})
    return {"files": files}

@app.post("/api/tactics")
async def upload_tactics(request: Request):
    """Saves a tactics document for RocketRide filesystem indexing."""
    contents = await request.body()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded tactics file is empty.")

    tactics_dir = Path(TACTICS_DIR)
    tactics_dir.mkdir(parents=True, exist_ok=True)
    filename = _safe_upload_name(request.headers.get("x-filename", "tactics.txt"))
    path = tactics_dir / filename
    path.write_bytes(contents)

    return {"filename": filename, "size": len(contents), "path": str(path)}
