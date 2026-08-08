import os
import json
import logging
from typing import Dict, Any, List, Optional, TypedDict
from groq import Groq
from langgraph.graph import StateGraph, START, END
from app.services.ai_service import extract_complaint_details
from app.database.session import SessionLocal
from app.models.complaint import Complaint

logger = logging.getLogger(__name__)

# State schema for the 5-Node LangGraph Pipeline
class QMSPipelineState(TypedDict):
    raw_text: str
    complaint_data: Dict[str, Any]
    summary: str
    missing_fields: List[str]
    completeness_score: str
    risk_level: str
    root_cause_analysis: str
    capa_recommendations: str
    is_duplicate: bool
    duplicate_complaint_ids: str


# Initialize Groq Client helper
def get_groq_client() -> Optional[Groq]:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception as e:
        logger.error(f"Error initializing Groq client: {e}")
        return None


# ---------------------------------------------------------
# NODE 1: AI Extractor & Executive Summary Node
# ---------------------------------------------------------
def node_1_extractor_and_summary(state: QMSPipelineState) -> Dict[str, Any]:
    """Node 1: Extracts structured core fields and creates a 2-sentence Executive Summary."""
    raw_text = state.get("raw_text", "")
    
    # Extract 15 core fields using ai_service
    extracted = extract_complaint_details(raw_text)
    
    # Generate 2-sentence summary using Groq LLM
    client = get_groq_client()
    summary_text = ""
    if client:
        try:
            model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
            prompt = (
                "You are an expert Pharmaceutical QMS Auditor. Write a clear, concise 2-sentence Executive Summary "
                f"for the following customer complaint text:\n\n{raw_text}\n\n"
                "Summary (exactly 2 sentences):"
            )
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.2,
                max_tokens=150
            )
            summary_text = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Node 1 Summary Generation Error: {e}")

    if not summary_text:
        prod = extracted.get("product_name") or "Pharmaceutical Product"
        cust = extracted.get("customer_name") or "Customer"
        desc = extracted.get("complaint_description") or "Quality issue reported."
        summary_text = f"Customer complaint reported by {cust} regarding {prod}. {desc[:100]}..."

    return {
        "complaint_data": extracted,
        "summary": summary_text
    }


# ---------------------------------------------------------
# NODE 2: QA Completeness Checker Node
# ---------------------------------------------------------
def node_2_completeness_checker(state: QMSPipelineState) -> Dict[str, Any]:
    """Node 2: Audits missing required QA fields and calculates completeness score."""
    data = state.get("complaint_data", {})
    
    # Mandatory QA Fields to Audit
    required_fields = {
        "customer_name": "Customer Name",
        "product_name": "Product Name",
        "product_strength": "Product Strength",
        "batch_number": "Batch / Lot Number",
        "affected_quantity": "Affected Quantity",
        "manufacturing_date": "Manufacturing Date",
        "expiry_date": "Expiry Date",
        "originating_site_block": "Manufacturing Site / Block",
        "complaint_category": "Complaint Category",
        "severity": "Severity Level"
    }
    
    missing = []
    present_count = 0
    
    for field_key, field_label in required_fields.items():
        val = data.get(field_key)
        if val is None or str(val).strip() == "" or str(val).strip().lower() == "none":
            missing.append(field_label)
        else:
            present_count += 1

    total = len(required_fields)
    score_percentage = int((present_count / total) * 100)
    completeness_score = f"{score_percentage}%"
    
    return {
        "missing_fields": missing,
        "completeness_score": completeness_score
    }


# ---------------------------------------------------------
# NODE 3: Risk & Root Cause Analysis Node
# ---------------------------------------------------------
def node_3_risk_and_root_cause(state: QMSPipelineState) -> Dict[str, Any]:
    """Node 3: Classifies Risk Level (Low to Critical) and identifies top manufacturing root causes."""
    raw_text = state.get("raw_text", "")
    data = state.get("complaint_data", {})
    
    client = get_groq_client()
    risk_level = data.get("severity") or "Major"
    root_cause = ""
    
    if client:
        try:
            model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
            prompt = f"""You are a Senior Quality Assurance Director in pharmaceutical manufacturing.
Analyze the following complaint details:
- Product: {data.get('product_name')}
- Category: {data.get('complaint_category')}
- Description: {data.get('complaint_description')}
- Raw Text: {raw_text}

Provide:
1. Risk Level: (Choose strictly ONE: Low, Medium, High, Critical)
2. Root Cause Analysis: Identify top 2 probable manufacturing, packaging, or supply chain root causes.

Format your output as JSON with keys 'risk_level' and 'root_cause'.
Example:
{{
  "risk_level": "Critical",
  "root_cause": "1. Sealing pressure sensor calibration drift on Filling Line 2 leading to micro-leaks. 2. Thermal degradation during secondary carton transit."
}}"""
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.1,
                max_tokens=250,
                response_format={"type": "json_object"}
            )
            parsed = json.loads(response.choices[0].message.content)
            risk_level = parsed.get("risk_level", risk_level)
            root_cause = parsed.get("root_cause", "")
        except Exception as e:
            logger.error(f"Node 3 Risk & Root Cause Error: {e}")

    if not root_cause:
        root_cause = f"Potential equipment calibration drift or packaging seal failure in {data.get('originating_site_block', 'production site')} requiring QA investigation."

    return {
        "risk_level": risk_level,
        "root_cause_analysis": root_cause
    }


# ---------------------------------------------------------
# NODE 4: CAPA Generator Node
# ---------------------------------------------------------
def node_4_capa_generator(state: QMSPipelineState) -> Dict[str, Any]:
    """Node 4: Recommends structured Corrective and Preventive Actions (CAPA)."""
    data = state.get("complaint_data", {})
    root_cause = state.get("root_cause_analysis", "")
    
    client = get_groq_client()
    capa_text = ""
    
    if client:
        try:
            model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
            prompt = f"""You are a Pharmaceutical Regulatory & CAPA Specialist.
Based on the complaint:
- Product: {data.get('product_name')} (Batch: {data.get('batch_number')})
- Root Cause: {root_cause}

Generate structured CAPA recommendations:
1. Corrective Actions (Immediate containment, quarantine, customer notifications):
2. Preventive Actions (Long-term process modification, equipment re-validation, SOP updates):

Keep response clear and professional."""
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.2,
                max_tokens=300
            )
            capa_text = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Node 4 CAPA Error: {e}")

    if not capa_text:
        batch = data.get('batch_number', 'this batch')
        capa_text = (
            f"• Corrective Action: Issue immediate quarantine for batch {batch} and initiate lab testing.\n"
            "• Preventive Action: Re-validate sealing equipment and update Packaging SOP-QA-102."
        )

    return {
        "capa_recommendations": capa_text
    }


# ---------------------------------------------------------
# NODE 5: Duplicate Complaint Detector Node
# ---------------------------------------------------------
def node_5_duplicate_detector(state: QMSPipelineState) -> Dict[str, Any]:
    """Node 5: Queries PostgreSQL database for existing complaints matching Batch Number or Product Name."""
    data = state.get("complaint_data", {})
    batch = data.get("batch_number")
    product = data.get("product_name")
    
    is_duplicate = False
    dup_details = []
    
    if batch or product:
        db = SessionLocal()
        try:
            query = db.query(Complaint)
            matches = []
            
            # 1. Match exact batch number (if provided)
            if batch and str(batch).strip() and str(batch).lower() != "none":
                matches = query.filter(Complaint.batch_number == batch).all()
            
            # 2. If no batch match, match product_name + customer_name
            if not matches and product:
                matches = query.filter(Complaint.product_name == product).limit(5).all()

            if matches:
                is_duplicate = True
                for m in matches:
                    dup_details.append(
                        f"Complaint ID #{m.id} (Batch: {m.batch_number or 'N/A'}, Customer: {m.customer_name or 'N/A'}, Status: {m.status})"
                    )
        except Exception as e:
            logger.error(f"Node 5 Duplicate Detector DB Error: {e}")
        finally:
            db.close()

    dup_summary = "; ".join(dup_details) if dup_details else "No duplicate complaints detected in QMS database."

    return {
        "is_duplicate": is_duplicate,
        "duplicate_complaint_ids": dup_summary
    }


# ---------------------------------------------------------
# BUILD THE 5-NODE LANGGRAPH PIPELINE
# ---------------------------------------------------------
workflow = StateGraph(QMSPipelineState)

# Add Nodes
workflow.add_node("extractor_summary", node_1_extractor_and_summary)
workflow.add_node("completeness_checker", node_2_completeness_checker)
workflow.add_node("risk_root_cause", node_3_risk_and_root_cause)
workflow.add_node("capa_generator", node_4_capa_generator)
workflow.add_node("duplicate_detector", node_5_duplicate_detector)

# Add Sequential Edges (Node 1 -> Node 2 -> Node 3 -> Node 4 -> Node 5 -> END)
workflow.add_edge(START, "extractor_summary")
workflow.add_edge("extractor_summary", "completeness_checker")
workflow.add_edge("completeness_checker", "risk_root_cause")
workflow.add_edge("risk_root_cause", "capa_generator")
workflow.add_edge("capa_generator", "duplicate_detector")
workflow.add_edge("duplicate_detector", END)

# Compile Graph App
qms_pipeline_app = workflow.compile()


def run_5_node_qms_pipeline(raw_text: str) -> Dict[str, Any]:
    """
    Executes the 5-Node LangGraph Pipeline on raw text input.
    Returns aggregated results from all 5 nodes.
    """
    initial_state = {
        "raw_text": raw_text,
        "complaint_data": {},
        "summary": "",
        "missing_fields": [],
        "completeness_score": "0%",
        "risk_level": "Major",
        "root_cause_analysis": "",
        "capa_recommendations": "",
        "is_duplicate": False,
        "duplicate_complaint_ids": ""
    }
    
    final_state = qms_pipeline_app.invoke(initial_state)
    
    # Merge extracted core fields with all 5-node analysis fields
    complaint_result = dict(final_state.get("complaint_data", {}))
    complaint_result["summary"] = final_state.get("summary", "")
    complaint_result["missing_fields"] = ", ".join(final_state.get("missing_fields", []))
    complaint_result["completeness_score"] = final_state.get("completeness_score", "100%")
    complaint_result["risk_level"] = final_state.get("risk_level", complaint_result.get("severity", "Major"))
    complaint_result["root_cause_analysis"] = final_state.get("root_cause_analysis", "")
    complaint_result["capa_recommendations"] = final_state.get("capa_recommendations", "")
    complaint_result["is_duplicate"] = final_state.get("is_duplicate", False)
    complaint_result["duplicate_complaint_ids"] = final_state.get("duplicate_complaint_ids", "")

    return complaint_result
