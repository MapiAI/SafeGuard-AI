from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# SQLAlchemy model for the Message entity. 
# Each message belongs to a case and has one associated analysis.
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    content = Column(String, nullable=False)
    author_alias = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="messages")
    analysis = relationship("Analysis", back_populates="message", uselist=False, cascade="all, delete-orphan")