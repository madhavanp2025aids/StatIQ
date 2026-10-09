"""
main.py — FastAPI entry point for StatGPT backend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import json
import secrets

from .agent import run_agent, reset_history
from .data_loader import (
    get_plfs_raw, get_cpi_raw, get_nas_raw,
    get_iip_raw, get_asi_raw, get_metadata,
    get_literacy_raw, get_poverty_raw
)

# ─────────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="StatGPT API",
    description="AI assistant for official MoSPI statistics — powered by Gemini",
    version="1.0.0",
)

# Allow all origins for local development (tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend
_FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if _FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR)), name="static")


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_reset: bool = False
    session_id: str | None = None


class AuthRequest(BaseModel):
    email: str
    password: str


class ChatResponse(BaseModel):
    answer: str
    data_table: list
    interpretation: str
    source: str
    infographic_stats: list = []
    chart_config: dict | None = None
    error: bool = False
    citations: list = []
    confidence: str = "LOW"
    query_type: str = "GENERAL_QUERY"


# Demo credentials (in production, replace with a real database + hashed passwords)
_DEMO_USERS = {
    "admin@statgpt.in": {"password": "statgpt2024", "name": "Admin"},
    "guest": {"password": "guest", "name": "Guest"},
}

# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_frontend():
    index_path = _FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"status": "ok", "message": "StatGPT API is running. Frontend not found."}


@app.get("/login", include_in_schema=False)
async def serve_login():
    login_path = _FRONTEND_DIR / "login.html"
    if login_path.exists():
        return FileResponse(str(login_path))
    raise HTTPException(status_code=404, detail="Login page not found.")


@app.post("/auth/login")
async def login(req: AuthRequest):
    user = _DEMO_USERS.get(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = secrets.token_urlsafe(32)
    return {"token": token, "name": user["name"], "email": req.email}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "StatGPT"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if req.session_reset:
        reset_history()

    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    result = run_agent(req.message.strip(), session_id=req.session_id)
    return ChatResponse(**result)


@app.post("/reset")
async def reset():
    reset_history()
    return {"status": "ok", "message": "Conversation history cleared."}


@app.get("/datasets")
async def list_datasets():
    meta = get_metadata()
    return {"datasets": meta["datasets"], "disclaimer": meta["disclaimer"]}


@app.get("/datasets/{name}")
async def get_dataset(name: str):
    loaders = {
        "plfs": get_plfs_raw,
        "cpi": get_cpi_raw,
        "nas": get_nas_raw,
        "iip": get_iip_raw,
        "asi": get_asi_raw,
        "literacy": get_literacy_raw,
        "poverty": get_poverty_raw,
    }
    name = name.lower()
    if name not in loaders:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{name}' not found. Available: {list(loaders.keys())}",
        )
    return loaders[name]()


from fastapi import UploadFile, File
from .processor import process_upload, get_session_summary

@app.post("/dataset/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith((".csv", ".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported.")
    try:
        content = await file.read()
        session_id, summary = process_upload(content, file.filename)
        return {"status": "ok", "session_id": session_id, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/dataset/summary/{session_id}")
async def get_summary(session_id: str):
    try:
        return get_session_summary(session_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class IngestRequest(BaseModel):
    pdf_path: str

@app.post("/knowledge/ingest")
async def ingest_document(req: IngestRequest):
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from knowledge.scripts.ingest_pdf import ingest_pdf
    
    try:
        if not Path(req.pdf_path).exists():
            raise HTTPException(status_code=404, detail="File not found")
        ingest_pdf(req.pdf_path)
        return {"status": "ok", "message": f"Successfully ingested {req.pdf_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge/status")
async def knowledge_status():
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from knowledge.vector_store.faiss_store import FaissStore
    
    try:
        store = FaissStore()
        return {
            "status": "ok",
            "index_size": store.index.ntotal if store.index else 0,
            "metadata_entries": len(store.metadata_map)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

