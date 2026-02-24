from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..database import Base


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stripe_session_id = Column(String, unique=True, nullable=False)
    user_email = Column(String, nullable=False)
    credits = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
