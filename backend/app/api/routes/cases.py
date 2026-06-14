# CRUD endpoints for Case resources. A case groups messages from the same context.

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/cases", tags=["Cases"])

@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(case_data: CaseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = Case(user_id=current_user.id, **case_data.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)
    return case

@router.get("/", response_model=list[CaseResponse])
def get_cases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Case).filter(Case.user_id == current_user.id).all()

@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(case_id: int, case_data: CaseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    for field, value in case_data.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    db.commit()
    db.refresh(case)
    return case

@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    db.delete(case)
    db.commit()