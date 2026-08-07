import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from app.database.session import SessionLocal
from app.models.complaint import Complaint

load_dotenv()


@tool
def update_complaint_fields(complaint_id: int, updates: dict = None, **kwargs) -> str:
    """
    Update fields of an existing complaint in the database.
    'complaint_id': ID of the complaint to update.
    'updates': A dictionary of field-value pairs to update.
    """
    field_updates = {}
    if updates and isinstance(updates, dict):
        field_updates.update(updates)
    if kwargs:
        field_updates.update(kwargs)

    db = SessionLocal()
    try:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            return f"Error: Complaint with ID {complaint_id} not found."

        updated_keys = []
        for key, value in field_updates.items():
            if key != "complaint_id" and hasattr(complaint, key):
                setattr(complaint, key, value)
                updated_keys.append(key)

        db.commit()
        db.refresh(complaint)
        return f"Successfully updated complaint #{complaint_id}. Updated fields: {', '.join(updated_keys)}."
    except Exception as e:
        db.rollback()
        return f"Error updating complaint #{complaint_id}: {str(e)}"
    finally:
        db.close()



tools = [update_complaint_fields]

api_key = os.getenv("GROQ_API_KEY")
model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

llm = ChatGroq(
    model=model_name,
    temperature=0,
    api_key=api_key,
)

llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = (
    "You are an expert AI QMS Assistant for a pharmaceutical company. "
    "You assist users in managing and updating customer complaints in the database. "
    "If the user asks to correct, edit, or update complaint details, you MUST invoke the `update_complaint_fields` tool. "
    "Make sure the keys in the `updates` dictionary match the database schema fields exactly "
    "(e.g., 'batch_number', 'severity', 'customer_name', 'product_name', 'product_strength', 'affected_quantity', etc.). "
    "After using the tool, inform the user clearly that the fields have been updated in the system."
)


def chatbot_node(state: MessagesState):
    """
    Chatbot node that processes messages and decides whether to call tools or respond directly.
    """
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}



builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition)
builder.add_edge("tools", "chatbot")

graph_app = builder.compile()
