from typing import List, Dict, Any
from langchain_core.messages import HumanMessage
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
    prompt = f"""
            You are a contextual analyzer. Given this code snippet, provide a concise description of what it does, its intended use, and any relevant environment or dependencies:

            {code_snippet}
            Focus on clarity and precision, as this will guide future recommendations."""
    msg = HumanMessage(content=prompt)
    summary = llm([msg]).content.strip()
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
def generate_recommendations(code_snippet: str, metadata: dict) -> str:
    """
    Produce concrete remediation steps, using stored context + guidelines.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
    context        = metadata.get("context", "")
    best_practices = metadata.get("best_practices", "")
    prompt = f"""
You are a Secure code reviewer. Based on the following:
- Context: {context}
- Best Practices: {best_practices}
- Code Snippet: {code_snippet}

Provide a numbered list of actionable, prioritized recommendations to remediate any issues.
"""
    msg = HumanMessage(content=prompt)
    return llm([msg]).content.strip()

