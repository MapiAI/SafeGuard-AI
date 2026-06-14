# Endpoint to trigger AI analysis on a message. Runs classification and stores results.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.message import Message
from app.models.case import Case
from app.models.analysis import Analysis
from app.schemas.analysis import AnalysisResponse
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.classifier import classify_message
from app.services.explainer import generate_explanation
from app.services.rag_retriever import retrieve_relevant_docs
from app.services.anonymizer import anonymise_text

router = APIRouter(prefix="/cases/{case_id}/messages", tags=["Analysis"])

@router.post("/{message_id}/analyze", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
def analyze_message(
    case_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify case belongs to current user
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Verify message belongs to case
    message = db.query(Message).filter(Message.id == message_id, Message.case_id == case_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Check if analysis already exists
    existing = db.query(Analysis).filter(Analysis.message_id == message_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Analysis already exists for this message")

    # Step 0 — PII anonymisation before any external AI call
    anonymised = anonymise_text(message.content)
    safe_text = anonymised["anonymised_text"]

    # Step 1 — Fine-tuned DistilBERT gate + bart-large-mnli zero-shot classification
    classification = classify_message(safe_text)

    # Step 2 — RAG retrieval from pgvector knowledge base
    retrieved_docs = retrieve_relevant_docs(
        message=safe_text,
        categories=classification["detected_categories"]
    )

    # Step 3 — OpenAI explanation on anonymised text
    explanation_result = generate_explanation(
        message=safe_text,
        categories=classification["detected_categories"],
        retrieved_docs=retrieved_docs
    )

    # Store analysis — original message stored in DB, anonymised text sent to AI
    analysis = Analysis(
        message_id=message_id,
        risk_score=classification["risk_score"],
        risk_level=classification["risk_level"],
        categories=classification["detected_categories"],
        explanation=explanation_result.get("explanation"),
        response_strategies=explanation_result.get("response_strategies"),
        gate=classification.get("gate"),
        gate_confidence=classification.get("gate_confidence")
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis