import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.session import Base


class Complaint(Base):
    """
    SQLAlchemy ORM Model representing a Customer Complaint in the QMS system.
    Includes 5-Node AI Pipeline analysis fields.
    """
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    complaint_source = Column(String(100), nullable=True)
    customer_name = Column(String(255), nullable=True)
    product_name = Column(String(255), nullable=True)
    product_strength = Column(String(100), nullable=True)
    batch_number = Column(String(100), nullable=True)
    affected_quantity = Column(String(100), nullable=True)
    manufacturing_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    originating_site_block = Column(String(255), nullable=True)
    impacted_non_product_materials = Column(Text, nullable=True)
    complaint_category = Column(String(100), nullable=True)
    complaint_description = Column(Text, nullable=True)
    severity = Column(String(50), nullable=True)
    suggested_next_action = Column(Text, nullable=True)
    initial_risk_assessment = Column(Text, nullable=True)
    
    # 5-Node AI Pipeline Analysis Fields
    summary = Column(Text, nullable=True)
    missing_fields = Column(Text, nullable=True)
    completeness_score = Column(String(50), nullable=True)
    risk_level = Column(String(50), nullable=True)
    root_cause_analysis = Column(Text, nullable=True)
    capa_recommendations = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, default=False, nullable=True)
    duplicate_complaint_ids = Column(Text, nullable=True)

    status = Column(String(50), default="Pending Triage", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    chat_messages = relationship("ChatMessage", back_populates="complaint", cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    SQLAlchemy ORM Model representing Copilot AI Chat Messages associated with complaints.
    """
    __tablename__ = "copilot_chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True)
    sender = Column(String(50), nullable=False)  # 'user' or 'ai'
    message = Column(Text, nullable=False)
    uploaded_file_name = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    complaint = relationship("Complaint", back_populates="chat_messages")
