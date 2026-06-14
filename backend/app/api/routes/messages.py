# CRUD endpoints for Message resources. Messages belong to a case.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.message import Message
from app.models.case import Case
from app.schemas.message import MessageCreate, MessageUpdate, MessageResponse
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/cases/{case_id}/messages", tags=["Messages"])

def get_case_or_404(case_id: int, current_user: User, db: Session) -> Case:
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(case_id: int, message_data: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_case_or_404(case_id, current_user, db)
    message = Message(case_id=case_id, **message_data.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

@router.get("/", response_model=list[MessageResponse])
def get_messages(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_case_or_404(case_id, current_user, db)
    return db.query(Message).filter(Message.case_id == case_id).all()

@router.get("/{message_id}", response_model=MessageResponse)
def get_message(case_id: int, message_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_case_or_404(case_id, current_user, db)
    message = db.query(Message).filter(Message.id == message_id, Message.case_id == case_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@router.patch("/{message_id}", response_model=MessageResponse)
def update_message(case_id: int, message_id: int, message_data: MessageUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_case_or_404(case_id, current_user, db)
    message = db.query(Message).filter(Message.id == message_id, Message.case_id == case_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    for field, value in message_data.model_dump(exclude_unset=True).items():
        setattr(message, field, value)
    db.commit()
    db.refresh(message)
    return message

@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(case_id: int, message_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_case_or_404(case_id, current_user, db)
    message = db.query(Message).filter(Message.id == message_id, Message.case_id == case_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(message)
    db.commit()