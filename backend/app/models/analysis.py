from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

# SQLAlchemy model for the Analysis entity. 
# Stores AI classification results, explanation, and response strategies for a message.
class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    categories = Column(JSON, nullable=True)
    explanation = Column(String, nullable=True)
    response_strategies = Column(JSON, nullable=True)
    gate = Column(String, nullable=True)
    gate_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("Message", back_populates="analysis")