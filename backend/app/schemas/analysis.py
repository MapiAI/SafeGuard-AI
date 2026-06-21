from pydantic import BaseModel
from datetime import datetime
from typing import Any

# Pydantic schemas for returning Analysis results. 
# Analysis is created by the AI pipeline, not directly by the user.
class AnalysisResponse(BaseModel):
    id: int
    message_id: int
    risk_score: float | None
    risk_level: str | None
    categories: Any | None
    explanation: str | None
    response_strategies: Any | None
    gate: str | None
    gate_confidence: float | None
    context_risk_level: str | None = None
    context_note: str | None
    created_at: datetime

    class Config:
        from_attributes = True
