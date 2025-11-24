from urllib import response
from langchain_ollama.llms import OllamaLLM
from app.services.retriever_service import Retriever
from app.core.config import settings
from app.core.security import get_current_user

retriever = Retriever()

client = OllamaLLM(model=settings.OLLAMA_MODEL)
LEGAL_PROMPT = """
Role: Legal Assistant  
Focus on: obligations, liabilities, confidentiality, termination, jurisdiction, payments.  
Use precise legal language but stay concise.


Do NOT hallucinate. If information is not found, say: "Unknown based on provided document."
"""
FINANCE_PROMPT = """
Role: Finance Assistant  
Focus on: loan terms, interest rates, repayment rules, eligibility, penalties, compliance.  
Keep answers numeric and rule-based.


Do NOT hallucinate. If information is not found, say: "Unknown based on provided document."
"""
ACADEMIC_PROMPT = """
Role: Academic Research Assistant  
Focus on: topic, methodology, findings, results, citations, conclusions.  
Keep answers concise and factual.

Respond only using information present in the context.
Do NOT hallucinate. If information is not found, say: "Unknown based on provided document."
"""

MEDICAL_PROMPT = """
Role: Medical Report Assistant  
Focus on: symptoms, history, findings, lab results, diagnosis indicators, treatments mentioned.  
Avoid giving medical advice—only interpret the report.
Respond only using information present in the context.

Do NOT hallucinate. If information is not found, say: "Unknown based on provided document."
"""
BUSINESS_PROMPT = """
Role: Business/Meeting Assistant  
Focus on: decisions, action items, risks, blockers, responsibilities, KPIs.  
Keep responses structured and clear.
Respond only using information present in the context.
Do NOT hallucinate. If information is not found, say: "Unknown based on provided document."
"""

ADMIN_PROMPT = """
Role: Admin Document Intelligence Assistant  
Provide the clearest and most structured answer possible using only document context.
Do NOT hallucinate. If information is not found, say: "Unknown based on provided document."
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
