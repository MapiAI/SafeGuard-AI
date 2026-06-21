from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# SQLAlchemy model for the Case entity. 
# A case groups messages from the same context (workplace, relationship).
class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    subject_alias = Column(String, nullable=True)
    relationship_summary = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="cases")
    messages = relationship("Message", back_populates="case", cascade="all, delete-orphan")