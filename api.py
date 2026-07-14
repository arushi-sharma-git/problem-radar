"""
api.py — Week 3: FastAPI layer over the insights/ideas Postgres tables.

Run with:
    uvicorn api:app --reload

Then open http://127.0.0.1:8000/docs for the interactive Swagger UI —
that's your demo interface, no frontend code needed.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from psycopg2.extras import RealDictCursor
import psycopg2
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum

from db import get_connection

app = FastAPI(
    title="problem-radar API",
    description="Browse clusters of real-world problems, extracted insights, and student project ideas.",
    version="1.0.0",
)

# Allows the standalone frontend.html (opened as a local file, origin "null")
# to call this API. Fine for a local demo; for real deployment, restrict
# allow_origins to your actual frontend's domain instead of "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------- DB dependency (guarantees the connection closes, even on error) ----------

def get_db():
    try:
        conn = get_connection()
    except psycopg2.OperationalError:
        raise HTTPException(status_code=503, detail="Database is unavailable right now. Please try again shortly.")
    try:
        yield conn
    finally:
        conn.close()


# ---------- Global fallback: never leak a raw traceback to the client ----------

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong processing that request."},
    )


# ---------- Response models ----------
# (separate from schemas.py's LLM-output models, since these represent DB rows
# with extra fields like id/cluster_id/created_at)

class DifficultyEnum(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class ClusterSummary(BaseModel):
    cluster_id: int
    domain: str
    confidence: str
    article_count: int


class InsightOut(BaseModel):
    id: int
    cluster_id: int
    domain: str
    pain_point: str
    affected_group: str
    evidence_gap: str
    confidence: str
    article_ids: List[int]


class IdeaOut(BaseModel):
    id: int
    problem_statement: str
    target_user: str
    suggested_approach: str
    tech_angle: str
    difficulty: str
    feasibility_score: int
    impact_score: int


# ---------- Endpoints ----------

@app.get("/clusters", response_model=List[ClusterSummary])
def list_clusters(conn=Depends(get_db)):
    """All clusters with their theme/domain, confidence, and article count."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT cluster_id, domain, confidence, array_length(article_ids, 1) AS article_count
        FROM insights
        ORDER BY cluster_id
    """)
    return cur.fetchall()


@app.get("/clusters/{cluster_id}/insight", response_model=InsightOut)
def get_cluster_insight(cluster_id: int, conn=Depends(get_db)):
    """The extracted insight for one cluster."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM insights WHERE cluster_id = %s", (cluster_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"No insight found for cluster_id={cluster_id}")
    return row


@app.get("/clusters/{cluster_id}/ideas", response_model=List[IdeaOut])
def get_cluster_ideas(cluster_id: int, conn=Depends(get_db)):
    """The generated project ideas for one cluster."""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id FROM insights WHERE cluster_id = %s", (cluster_id,))
    insight_row = cur.fetchone()
    if not insight_row:
        raise HTTPException(status_code=404, detail=f"No insight found for cluster_id={cluster_id}")

    cur.execute("SELECT * FROM ideas WHERE insight_id = %s", (insight_row["id"],))
    return cur.fetchall()


@app.get("/ideas", response_model=List[IdeaOut])
def list_ideas(
    difficulty: Optional[DifficultyEnum] = Query(None, description="Filter by difficulty level"),
    domain: Optional[str] = Query(None, description="Substring match against the cluster's domain"),
    conn=Depends(get_db),
):
    """Browse all ideas across all clusters, optionally filtered by
    difficulty and/or domain — the main student-facing endpoint."""
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT ideas.* FROM ideas
        JOIN insights ON ideas.insight_id = insights.id
        WHERE 1=1
    """
    params = []
    if difficulty:
        query += " AND ideas.difficulty = %s"
        params.append(difficulty.value)
    if domain:
        query += " AND insights.domain ILIKE %s"
        params.append(f"%{domain}%")

    cur.execute(query, params)
    return cur.fetchall()


@app.get("/")
def root():
    return {
        "message": "problem-radar API — see /docs for interactive endpoints",
        "endpoints": ["/clusters", "/clusters/{cluster_id}/insight", "/clusters/{cluster_id}/ideas", "/ideas"],
    }