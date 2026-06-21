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

    # Step 1 — Retrieve last 3 analyzed messages from case (relationship context)
    previous_messages = []
    previous = (
        db.query(Message)
        .join(Analysis)
        .filter(Message.case_id == case_id, Message.id != message_id)
        .order_by(Message.timestamp.desc())
        .limit(3)
        .all()
    )
    for m in reversed(previous):
        previous_messages.append({
            "content": m.content,
            "risk_level": m.analysis.risk_level,
            "categories": m.analysis.categories or []
        })

    # Step 1b — Check if relationship history contains toxic patterns
    high_risk_history = any(
        m["risk_level"] in ["high", "medium"]
        for m in previous_messages
    )

    # Step 2 — Fine-tuned DistilBERT gate + bart-large-mnli zero-shot classification
    # strict=False lowers gate threshold when toxic history is present
    classification = classify_message(safe_text, strict=not high_risk_history)

    # Step 3 — RAG retrieval from pgvector knowledge base
    retrieved_docs = retrieve_relevant_docs(
        message=safe_text,
        categories=classification["detected_categories"]
    )

    # Step 4 — OpenAI explanation on anonymised text with relationship context
    explanation_result = generate_explanation(
        message=safe_text,
        categories=classification["detected_categories"],
        retrieved_docs=retrieved_docs,
        previous_messages=previous_messages,
        relationship_summary=case.relationship_summary or ""
    )

    # Step 5 — Update relationship summary on case
    if explanation_result.get("updated_summary"):
        case.relationship_summary = explanation_result["updated_summary"]
        db.commit()
        
    # Step 6 — Override context_risk_level if no toxic history and message is none risk
    context_risk_level = explanation_result.get("context_risk_level")
    if classification["risk_level"] == "none" and not high_risk_history:
        context_risk_level = "none"
    
    # Step 6b — Override context_risk_level to high if current message is high and history contains high
    high_in_history = any(m["risk_level"] == "high" for m in previous_messages)
    if classification["risk_level"] == "high" and high_in_history:
        context_risk_level = "high"
    
    # Step 6c — A high risk message can never have context low
    if classification["risk_level"] == "high" and context_risk_level == "low":
        context_risk_level = "medium"

    # Store analysis — original message stored in DB, anonymised text sent to AI
    analysis = Analysis(
        message_id=message_id,
        risk_score=classification["risk_score"],
        risk_level=classification["risk_level"],
        categories=classification["detected_categories"],
        explanation=explanation_result.get("explanation"),
        response_strategies=explanation_result.get("response_strategies"),
        gate=classification.get("gate"),
        gate_confidence=classification.get("gate_confidence"),
        context_note=explanation_result.get("context_note"),
        context_risk_level=context_risk_level,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis

@router.get("/{message_id}/analysis", response_model=AnalysisResponse)
def get_analysis(
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

    # Get analysis
    analysis = db.query(Analysis).filter(Analysis.message_id == message_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return analysis