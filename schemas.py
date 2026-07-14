"""
schemas.py — pydantic models matching the JSON schemas from your prompt
templates. Used to validate LLM output before trusting it.

pip install pydantic
"""

from pydantic import BaseModel
from typing import List, Literal


class Insight(BaseModel):
    domain: str
    pain_point: str
    affected_group: str
    evidence_gap: str
    supporting_excerpt_ids: List[str]
    confidence: Literal["high", "medium", "low"]


class Idea(BaseModel):
    problem_statement: str
    target_user: str
    suggested_approach: str
    tech_angle: str
    difficulty: Literal["beginner", "intermediate", "advanced"]
    feasibility_score: int
    impact_score: int


class IdeaList(BaseModel):
    ideas: List[Idea]