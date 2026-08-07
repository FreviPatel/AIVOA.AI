import io
import PyPDF2


async def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extract text content from uploaded file bytes (PDF, TXT, EML, etc.).
    """
    if not file_bytes:
        return ""

    filename_lower = filename.lower()

    try:
        if filename_lower.endswith(".pdf"):
            pdf_stream = io.BytesIO(file_bytes)
            reader = PyPDF2.PdfReader(pdf_stream)
            extracted_pages = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted_pages.append(text)
            return "\n".join(extracted_pages).strip()

        elif filename_lower.endswith((".txt", ".eml", ".csv", ".log")):
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1", errors="ignore")

        else:
            # General fallback attempt for unlisted text formats
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1", errors="ignore")

    except Exception as e:
        print(f"Error extracting text from document '{filename}': {e}")
        return ""
