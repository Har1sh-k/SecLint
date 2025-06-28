from typing import List, Dict, Any
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.tools import tool
from status_logger import logger
from dotenv import load_dotenv
from tools.security_kb import get_best_practices

load_dotenv()


@tool
def understand_context(code_snippet: str) -> str:
    """
    Analyze and remember the snippet’s purpose/use.
    """
    llm = ChatOpenAI(model="gpt-4", temperature=0.0)
    prompt = f"""
            You are a contextual analyzer. Given this code snippet, provide a concise description of what it does, its intended use, and any relevant environment or dependencies:

            {code_snippet}
            Focus on clarity and precision, as this will guide future recommendations."""
    msg = HumanMessage(content=prompt)
    summary = llm([msg]).content.strip()
    return summary

@tool
def fetch_secure_coding_guidelines(code_snippet: str) -> str:
    """    Use the RAG to fetch relevant secure coding guidelines based on the code snippet.
    Expects metadata to include:
        - code_snippet (str): The code snippet to analyze.
        """
    best_practices = get_best_practices(code_snippet)
    return best_practices

@tool
def generate_recommendations(code_snippet: str, metadata: dict) -> str:
    """
    Use the LLM to produce concrete, prioritized remediation steps.
    Expects metadata to include:
      - context (from understand_context)
      - best_practices (from fetch_best_practices)
    """
    llm = ChatOpenAI(model="gpt-4", temperature=0.0)
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

