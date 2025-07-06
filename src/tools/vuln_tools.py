from typing import List, Dict, Any
from langchain_core.messages import SystemMessage,HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.tools import tool
from status_logger import logger
from dotenv import load_dotenv
from tools.security_kb import get_best_practices

load_dotenv()

_memory_store: Dict[str, Dict[str, str]] = {}

@tool
def understand_context(code_snippet: str) -> str:
    """
    Analyze and remember the snippet’s purpose/use.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
    system_prompt = (
        """You are a code context analyzer. Given a code snippet, you provide a concise, 
        precise summary of its functionality, intended use, and any necessary environment or dependencies."""
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=code_snippet),
    ]
    summary = llm.invoke(messages).content.strip()
    _memory_store.setdefault(code_snippet, {})["context"] = summary
    return summary

@tool
def fetch_secure_coding_guidelines(code_snippet: str) -> str:
    """    RAG lookup for secure-coding guidelines
        """
    guidelines = get_best_practices(code_snippet) or "No best-practices found."
    _memory_store.setdefault(code_snippet, {})["best_practices"] = guidelines
    return guidelines

@tool
def generate_recommendations(code_snippet: str, best_practices: str) -> str:
    """
    Produce concrete remediation steps, using stored context + guidelines.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
    system_prompt = (
        "You are a secure code reviewer. Given the snippet context, secure coding guidelines, and the snippet itself, "
        "generate a JSON object with these keys:\n"
        "  - severity: one of Critical, High, Medium, Low, or None if no vulnerabilities.\n"
        "  - best_practices: a list of relevant secure coding principles.\n"
        "Remember: Do not include the practice 'Conduct Thorough Code Reviews and Testing'.\n"
        "Ensure the output is valid JSON."
    )
    context = _memory_store.get(code_snippet, {}).get("context", "No context available.")
    user_content = (
        f"Context:\n{context}\n\n"
        f"Secure Coding Guidelines:\n{best_practices}\n\n"
        f"Code Snippet:\n{code_snippet}"
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content),
    ]
    response = llm.invoke(messages).content.strip()
    return response

