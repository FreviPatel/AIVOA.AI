import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def parse_date_safe(date_str):
    """Safely parse various date string formats into a datetime.date object."""
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    return None


def extract_complaint_details(raw_text: str) -> dict:
    """
    Parses raw complaint text into structured JSON matching the Complaint database schema
    using the Groq API with gemma2-9b-it model.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        print("Warning: Valid GROQ_API_KEY is not set in environment variables.")
        return _fallback_extraction(raw_text)

    try:
        client = Groq(api_key=api_key)

        system_prompt = (
            "You are a Quality Assurance expert for a pharmaceutical manufacturing company.\n"
            "Your task is to analyze raw customer complaint text and extract all relevant details "
            "into a strict JSON object.\n\n"
            "The JSON output MUST contain the following keys:\n"
            ' - "complaint_source": (string, e.g. "Customer Email", "Call Center", "Web Portal")\n'
            ' - "customer_name": (string, or null if not provided)\n'
            ' - "product_name": (string, or null if not provided)\n'
            ' - "product_strength": (string, e.g. "500mg", "10ml", or null)\n'
            ' - "batch_number": (string, or null if not provided)\n'
            ' - "affected_quantity": (string, e.g. "50 bottles", "1 carton", or null)\n'
            ' - "manufacturing_date": (string in YYYY-MM-DD format, or null)\n'
            ' - "expiry_date": (string in YYYY-MM-DD format, or null)\n'
            ' - "originating_site_block": (string, or null)\n'
            ' - "impacted_non_product_materials": (string, or null)\n'
            ' - "complaint_category": (string, e.g. "Packaging Defect", "Contamination", "Labeling Issue", "Efficacy", "Adverse Event")\n'
            ' - "complaint_description": (string, detailed summary of the issue)\n'
            ' - "severity": (MUST be strictly one of: "Minor", "Major", or "Critical")\n'
            ' - "suggested_next_action": (string, recommended QA investigation step)\n'
            ' - "initial_risk_assessment": (string, initial risk impact statement)\n\n'
            "CRITICAL INSTRUCTIONS:\n"
            "1. Output ONLY a valid JSON object. Do not include markdown codeblocks (```json), explanation, or conversational text.\n"
            "2. If a field is not present in the text, set its value to null.\n"
            "3. Ensure the severity is strictly one of: 'Minor', 'Major', or 'Critical'."
        )

        # Try active Groq models: llama-3.3-70b-versatile first, fallback to llama-3.1-8b-instant
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_text},
                ],
                temperature=0.1,
                max_tokens=1000,
            )
        except Exception as model_err:
            print(f"Primary model {model_name} error ({model_err}). Retrying with llama-3.1-8b-instant...")
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_text},
                ],
                temperature=0.1,
                max_tokens=1000,
            )


        raw_response = response.choices[0].message.content.strip()

        # Clean markdown code blocks if present
        cleaned_response = raw_response
        if cleaned_response.startswith("```"):
            cleaned_response = re.sub(r"^```(?:json)?\n?", "", cleaned_response)
            cleaned_response = re.sub(r"\n?```$", "", cleaned_response).strip()

        extracted_data = json.loads(cleaned_response)

        # Convert date strings to datetime.date objects for database compatibility
        if "manufacturing_date" in extracted_data:
            extracted_data["manufacturing_date"] = parse_date_safe(extracted_data["manufacturing_date"])
        if "expiry_date" in extracted_data:
            extracted_data["expiry_date"] = parse_date_safe(extracted_data["expiry_date"])

        # Validate severity
        if extracted_data.get("severity") not in ["Minor", "Major", "Critical"]:
            extracted_data["severity"] = "Major"

        return extracted_data

    except Exception as e:
        print(f"Error extracting complaint details with Groq API: {e}")
        return _fallback_extraction(raw_text)


def _fallback_extraction(raw_text: str) -> dict:
    """Fallback extraction dictionary if LLM call or JSON parsing fails."""
    return {
        "complaint_source": "Raw Input",
        "customer_name": None,
        "product_name": None,
        "product_strength": None,
        "batch_number": None,
        "affected_quantity": None,
        "manufacturing_date": None,
        "expiry_date": None,
        "originating_site_block": None,
        "impacted_non_product_materials": None,
        "complaint_category": "General Complaint",
        "complaint_description": raw_text[:500] if raw_text else "No description provided",
        "severity": "Major",
        "suggested_next_action": "Initial QA review required",
        "initial_risk_assessment": "Pending risk triage",
    }
