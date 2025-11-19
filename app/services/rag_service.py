from urllib import response
from langchain_ollama.llms import OllamaLLM
from app.services.retriever_service import Retriever
from app.core.config import settings
from app.core.security import get_current_user

retriever = Retriever()

client = OllamaLLM(model=settings.OLLAMA_MODEL)
LEGAL_PROMPT = """
You are an AI Legal Assistant specialized in analyzing contracts and legal documents.

RULES:
1. Use ONLY the information in the context. No external assumptions.
2. If any answer cannot be derived from the document, respond with: "Unknown based on provided document."
3. Extract and summarize:
   - Termination clauses
   - Payment terms
   - Indemnity / Liability
   - Confidentiality
   - Governing law & jurisdiction
   - Obligations of the parties
   - Breach & penalties
4. Use simple but formal legal language.

Do NOT hallucinate. If information is not found, say: "Unknown based on provided document."
"""

FINANCE_PROMPT = """
You are a Finance and Banking AI Assistant. 
Use only the context to extract:
- Loan terms & interest rates
- Repayment rules
- Eligibility criteria
- Penalties & defaults
- Bank policies or compliance rules

Do NOT hallucinate. If information is not found, say: "Unknown based on provided document."
"""
ACADEMIC_PROMPT = """
You are an Academic Research Assistant.
Extract from the context:
- Research topic
- Key findings
- Methodology
- Conclusions
- Citations mentioned

Respond only using information present in the context.
Do NOT hallucinate. If information is not found, say: "Unknown based on provided document."
"""

MEDICAL_PROMPT = """
You are a Medical Document Assistant. 
Extract ONLY what is present in the patient's report:
- Patient history
- Symptoms
- Findings
- Lab results
- Treatments mentioned (if any)

Do NOT hallucinate. If information is not found, say: "Unknown based on provided document."
"""
BUSINESS_PROMPT = """
You are a Business AI Assistant. 
Extract from context:
- Meeting summary
- Decisions taken
- Action items
- Risks / blockers
- Responsibilities

No external assumptions. Use only document context.
Do NOT hallucinate. If information is not found, say: "Unknown based on provided document."
"""

ADMIN_PROMPT = """
You are an Admin-level Document Intelligence Assistant.
Analyze the context and provide the best possible structured answer.
Use only the document content.
"""


def get_role_prompt(role: str):
    role = role.lower()

    if role == "lawyer":
        return LEGAL_PROMPT
    
    if role == "financer":
        return FINANCE_PROMPT
    
    if role == "student":
        return ACADEMIC_PROMPT
    
    if role == "doctor":
        return MEDICAL_PROMPT
    
    if role == "business_man":
        return BUSINESS_PROMPT

    if role == "admin":
        return ADMIN_PROMPT

    # default fallback
    return ACADEMIC_PROMPT


def ask_llm(query: str, context: list[str], current_user) -> str:
    """
    Smart RAG:
    - If context is EMPTY → answer normally (no role prompt)
    - If context has text → use role-based prompt
    """

    # Combine only the first few chunks of context
    context_text = "\n\n".join(context[:7]).strip()

    # CASE 1 — NO DOCUMENT CONTEXT → NORMAL CHAT MODE
    if not context_text:
        prompt = f"""
        You are an AI assistant.

        The user asked:
        "{query}"

        No document context is available.
        Answer normally using your own knowledge.
        """
        try:
            response = client.invoke(prompt)
            return response.strip()
        except Exception as e:
            return f"Error: {e}"

    # CASE 2 — CONTEXT AVAILABLE → USE ROLE PROMPT
    role_prompt = get_role_prompt(current_user.role)

    prompt = f"""
    {role_prompt}

    Context (from user's documents):
    {context_text}

    User Question:
    {query}

    IMPORTANT:
    - Use ONLY the above context.
    - If the answer cannot be found in the context, say:
      "Unknown based on provided document."
    """

    try:
        response = client.invoke(prompt)
        return response.strip()
    except Exception as e:
        return f"Error: {e}"
