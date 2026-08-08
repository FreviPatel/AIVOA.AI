import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Load environment variables
load_dotenv()

from app.database.session import engine, Base, get_db
from app.models.complaint import Complaint, ChatMessage
from app.schemas.complaint_schema import (
    ComplaintCreate,
    ComplaintUpdate,
    ComplaintResponse,
    ChatMessageCreate,
    ChatMessageResponse,
)
from app.services.ai_service import extract_complaint_details
from app.services.document_parser import extract_text_from_file
from app.services.ai_pipeline import run_5_node_qms_pipeline
from app.agents.graph import graph_app

# Ensure database tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Powered Customer Complaint Management System API",
    description="Backend API for QMS complaint management, 5-Node LangGraph AI Pipeline, document parsing, and LangGraph AI Copilot agent.",
    version="2.0.0",
)

# Configure CORS middleware
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to AI-Powered Customer Complaint Management System API (5-Node LangGraph Enabled)",
    }


# ==========================================
# Complaint Endpoints
# ==========================================

@app.post(
    "/api/complaints",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer complaint",
)
def create_complaint(
    complaint_in: ComplaintCreate, db: Session = Depends(get_db)
):
    """
    Create a new complaint record in the database.
    """
    db_complaint = Complaint(**complaint_in.model_dump())
    db.add(db_complaint)
    db.commit()
    db.refresh(db_complaint)
    return db_complaint


@app.get(
    "/api/complaints",
    response_model=List[ComplaintResponse],
    summary="List all complaints",
)
def list_complaints(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """
    Retrieve a list of all complaints with pagination support.
    """
    complaints = db.query(Complaint).offset(skip).limit(limit).all()
    return complaints


@app.get(
    "/api/complaints/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Get complaint by ID",
)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    """
    Fetch details of a single complaint by its ID.
    """
    db_complaint = (
        db.query(Complaint).filter(Complaint.id == complaint_id).first()
    )
    if not db_complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID {complaint_id} not found",
        )
    return db_complaint


@app.put(
    "/api/complaints/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Update an existing complaint",
)
def update_complaint(
    complaint_id: int,
    complaint_update: ComplaintUpdate,
    db: Session = Depends(get_db),
):
    """
    Partially or fully update a complaint record by ID.
    """
    db_complaint = (
        db.query(Complaint).filter(Complaint.id == complaint_id).first()
    )
    if not db_complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID {complaint_id} not found",
        )

    update_data = complaint_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_complaint, key, value)

    db.commit()
    db.refresh(db_complaint)
    return db_complaint


# ==========================================
# 5-Node LangGraph File Upload Endpoint
# ==========================================

@app.post(
    "/api/upload-complaint",
    summary="Upload document and process via 5-Node LangGraph AI Pipeline",
)
async def upload_complaint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF/TXT complaint document, parse its text content, execute the 5-Node LangGraph AI Pipeline
    (Extraction & Summary -> Completeness -> Risk & Root Cause -> CAPA -> Duplicate Detector),
    and persist the fully analyzed Complaint and chat history in PostgreSQL.
    """
    file_bytes = await file.read()
    raw_text = await extract_text_from_file(file_bytes, file.filename)

    if not raw_text or not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not extract text content from file '{file.filename}'.",
        )

    # Run full 5-Node LangGraph AI Pipeline
    analyzed_data = run_5_node_qms_pipeline(raw_text)

    # Create new Complaint database record
    new_complaint = Complaint(**analyzed_data)
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)

    # Store user chat message indicating upload
    user_msg = ChatMessage(
        complaint_id=new_complaint.id,
        sender="user",
        message=f"Uploaded document: {file.filename}",
        uploaded_file_name=file.filename,
    )
    db.add(user_msg)

    # Store AI response acknowledging 5-Node pipeline execution
    dup_str = " ⚠️ Duplicate batch detected!" if new_complaint.is_duplicate else ""
    ai_msg = ChatMessage(
        complaint_id=new_complaint.id,
        sender="ai",
        message=(
            f"Parsed document '{file.filename}' through 5-Node AI Pipeline (Complaint ID #{new_complaint.id}). "
            f"Completeness Score: {new_complaint.completeness_score}, Risk Level: {new_complaint.risk_level}.{dup_str}"
        ),
        uploaded_file_name=None,
    )
    db.add(ai_msg)
    db.commit()

    return {
        "complaint_id": new_complaint.id,
        "filename": file.filename,
        "complaint_data": ComplaintResponse.model_validate(new_complaint),
    }


# ==========================================
# 5-Node Copilot Chat Endpoint (LangGraph Agent)
# ==========================================

@app.post(
    "/api/chat",
    response_model=ChatMessageResponse,
    summary="Copilot Chat endpoint powered by 5-Node LangGraph AI Pipeline",
)
def copilot_chat(chat_in: ChatMessageCreate, db: Session = Depends(get_db)):
    """
    Store incoming user message and return an AI copilot response message.
    If complaint_id is None, automatically execute the 5-Node LangGraph AI Pipeline on the message text.
    If complaint_id is NOT None, use LangGraph agent with tool calling to edit complaint fields.
    """
    target_complaint_id = chat_in.complaint_id

    # CASE A: If complaint_id is None, create new Complaint record via 5-Node AI Pipeline
    if target_complaint_id is None:
        analyzed_data = run_5_node_qms_pipeline(chat_in.message)

        # Create new Complaint record from 5-Node AI extracted & analyzed fields
        new_complaint = Complaint(**analyzed_data)
        db.add(new_complaint)
        db.commit()
        db.refresh(new_complaint)

        target_complaint_id = new_complaint.id
        dup_note = " (⚠️ Potential duplicate batch matched in QMS)" if new_complaint.is_duplicate else ""
        ai_response_text = (
            f"I have processed your complaint through the 5-Node AI Pipeline (Complaint ID #{new_complaint.id}){dup_note}. "
            f"Product: '{new_complaint.product_name or 'Pharmaceutical Product'}', Risk Level: '{new_complaint.risk_level}', Completeness: {new_complaint.completeness_score}."
        )
    else:
        # CASE B: If complaint_id is NOT None, invoke LangGraph agent with chat history context
        history = (
            db.query(ChatMessage)
            .filter(ChatMessage.complaint_id == target_complaint_id)
            .order_by(ChatMessage.timestamp.asc())
            .all()
        )

        system_msg = SystemMessage(
            content=(
                "You are an expert AI QMS Assistant for a pharmaceutical company. "
                f"You are currently assisting with Complaint ID #{target_complaint_id}. "
                "If the user asks to correct, edit, or update complaint details, you MUST invoke the `update_complaint_fields` tool. "
                f"Always pass complaint_id={target_complaint_id}. "
                "Make sure keys in the `updates` dictionary match the database schema fields exactly "
                "(e.g., 'batch_number', 'severity', 'customer_name', 'product_name', 'product_strength', 'affected_quantity', etc.). "
                "After using the tool, inform the user clearly that the fields have been updated in the system."
            )
        )
        formatted_messages = [system_msg]
        for msg in history:
            if msg.sender == "user":
                formatted_messages.append(HumanMessage(content=msg.message))
            else:
                formatted_messages.append(AIMessage(content=msg.message))

        # Add current user prompt
        formatted_messages.append(HumanMessage(content=chat_in.message))

        try:
            # Invoke LangGraph workflow
            graph_result = graph_app.invoke({"messages": formatted_messages})
            last_message = graph_result["messages"][-1]
            ai_response_text = str(last_message.content)
        except Exception as e:
            print(f"Error invoking LangGraph agent: {e}")
            ai_response_text = f"I encountered an error processing your update request for Complaint #{target_complaint_id}: {e}"

    # 1. Store user message in copilot_chat_messages
    user_msg = ChatMessage(
        complaint_id=target_complaint_id,
        sender=chat_in.sender or "user",
        message=chat_in.message,
        uploaded_file_name=chat_in.uploaded_file_name,
    )
    db.add(user_msg)

    # 2. Store AI response message in copilot_chat_messages
    ai_msg = ChatMessage(
        complaint_id=target_complaint_id,
        sender="ai",
        message=ai_response_text,
        uploaded_file_name=None,
    )
    db.add(ai_msg)

    db.commit()
    db.refresh(ai_msg)

    return ai_msg
