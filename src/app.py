import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path

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
        logger.info("No db found at %s. Initialising empty store.", DB_PATH)
        store = RecordStore()
        
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

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Renders the main Coach dashboard."""
    # We pass the store reviews and records to the dashboard for visualization
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
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
