# RAG Assistant endpoint — answers educational questions grounded in knowledge base.
# Includes daily rate limiting per user.

import json
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.usage_log import UsageLog
from app.services.rag_retriever import retrieve_relevant_docs
from app.db.database import get_db

router = APIRouter(prefix="/assistant", tags=["Assistant"])

DAILY_QUESTION_LIMIT = 10

class AssistantQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=300)

SYSTEM_PROMPT = """
You are an educational communication assistant for SafeGuard AI.

Answer EXCLUSIVELY based on the retrieved educational documents provided.
If the answer is not present in the retrieved documents, say:
"I don't have educational resources on this specific topic in my knowledge base."

ALWAYS:
- Use hedged language: "may suggest", "is often associated with"
- Be concise and educational
- Ground every statement in the retrieved documents

NEVER:
- Diagnose individuals or assign mental health labels
- Provide legal or psychological advice
- Recommend ending relationships or reporting someone
- Use knowledge outside of the retrieved documents
"""

@router.post("/ask")
def ask_assistant(
    body: AssistantQuestion,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today().isoformat()

    # Check daily usage
    daily_count = db.query(UsageLog).filter(
        UsageLog.user_id == current_user.id,
        UsageLog.action == "assistant_question",
        UsageLog.date == today
    ).count()

    if daily_count >= DAILY_QUESTION_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit of {DAILY_QUESTION_LIMIT} questions reached. Please try again tomorrow."
        )

    # Retrieve relevant documents
    retrieved_docs = retrieve_relevant_docs(
        message=body.question,
        categories=[]
    )

    user_prompt = f"""
Question: {body.question}

Retrieved educational documents:
{retrieved_docs if retrieved_docs else "No relevant documents found."}

Answer the question based exclusively on the retrieved documents above.
"""

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=400
    )

    # Log usage
    log = UsageLog(
        user_id=current_user.id,
        action="assistant_question",
        date=today
    )
    db.add(log)
    db.commit()

    return {
        "answer": response.choices[0].message.content,
        "questions_remaining": DAILY_QUESTION_LIMIT - daily_count - 1
    }