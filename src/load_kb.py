import os
import re
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter


load_dotenv()

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "security_docs"
PERSIST_DIR = "./insec_code_kb"
COLLECTION_NAME = "vulns_insecure"
EMBEDDING_MODEL = "text-embedding-3-small"

EVALUATION_SET = [
    {
        "query_code": """
def check_user_access(user_id, resource_id):
    # Missing authentication and authorization checks
    print(f"User {user_id} granted access to {resource_id}")
    return True
        """,
        "expected_vulnerability": "Missing Authorization Checks"
    },
    {
        "query_code": """
def update_user_role(current_user, target_user, new_role):
    # No check for current_user's role
    database.update_role(target_user, new_role)
    print(f"{current_user} changed {target_user}'s role to {new_role}")
        """,
        "expected_vulnerability": "Missing Role-Based Authorization for Privileged Actions"
    },
    {
        "query_code": """
def store_password(username, password):
    # Insecure: using MD5 (fast, broken hash) with no salt for password
    hash_hex = hashlib.md5(password.encode()).hexdigest()
    save_password_hash(username, hash_hex)
        """,
        "expected_vulnerability": "Password Hashing: Enforce Secure Hash Functions for Passwords"
    },
    {
        "query_code": """
def process_login(username, password):
    try:
        user = auth_login(username, password)
        return f"Welcome {user.name}!"
    except Exception as e:
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        return f"Authentication failed: {e}"
        """,
        "expected_vulnerability": "Debug Mode or Verbose Logging Enabled in Production"
    }
    ]

def load_documents(docs_path: Path) -> List[Document]:
    """Loads all markdown files from a directory."""
    loader = DirectoryLoader(
        path=str(docs_path),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
        use_multithreading=True,
    )
    print(f"Loading documents from {docs_path}...")
    docs = loader.load()
    print(f"Loaded {len(docs)} raw documents.")
    return docs

def _extract_code_from_markdown(markdown_text: str) -> str:
    """Uses regex to robustly extract a Python code block from markdown text."""
    match = re.search(r"```python\s*([\s\S]+?)\s*```", markdown_text)
    if match:
        return match.group(1).strip()
    match = re.search(r"```\s*([\s\S]+?)\s*```", markdown_text)
    if match:
        return match.group(1).strip()
    return markdown_text.strip()

def process_documents(raw_docs: List[Document]) -> List[Document]:
    """Splits and processes raw documents into a structured format for embedding."""
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("##", "section")],
        strip_headers=True,
        return_each_line=False,
    )
    processed_docs = []
    for doc in raw_docs:
        chunks = splitter.split_text(doc.page_content)
        if not chunks:
            continue
        
        chunks[0].metadata = {'section': "Vulnerability Name"}
        
        vuln_data: Dict[str, Any] = {"page_content": ""}
        metadata: Dict[str, str] = {}

        for chunk in chunks:
            section = chunk.metadata.get("section", "N/A").strip()
            text = chunk.page_content.strip()

            if section == "Vulnerability Name":
                metadata["Vulnerability Name"] = text
            elif section == "Insecure Code Example":
                vuln_data["page_content"] = _extract_code_from_markdown(text)
            else:
                metadata[section.replace(" (OWASP)", "")] = text
        
        if vuln_data["page_content"] and metadata.get("Vulnerability Name"):
            content_to_embed = (
                f"Vulnerability Name: {metadata['Vulnerability Name']}\n\n"
                f"Insecure Code Example:\n{vuln_data['page_content']}"
            )
            metadata["Insecure Code Example Content"] = vuln_data["page_content"]
            processed_docs.append(
                Document(page_content=content_to_embed, metadata=metadata)
            )
    print(f"Created {len(processed_docs)} structured vulnerability documents.")
    return processed_docs

def build_or_load_knowledge_base(
    processed_docs: List[Document], 
    persist_path: str, 
    collection_name: str, 
    embedding_model: OpenAIEmbeddings
) -> Chroma:

    if not (Path(persist_path)).exists():
        print(f"Building new vector store at '{persist_path}'...")
        if not processed_docs:
            raise ValueError("No documents processed, cannot build knowledge base.")
        
        vector_store = Chroma.from_documents(
            documents=processed_docs,
            embedding=embedding_model,
            persist_directory=persist_path,
            collection_name=collection_name,
        )
        print("Knowledge base built successfully.")
        return vector_store
    
    print(f"Loading existing vector store from '{persist_path}'...")
    return Chroma(
        persist_directory=persist_path,
        embedding_function=embedding_model,
        collection_name=collection_name
    )

def evaluate_retriever(
    vector_store: Chroma, 
    evaluation_set: List[Dict[str, str]], 
    k: int = 1,
    verbose: bool = True
):
    print("\n--- Running Evaluation ---")
    hit_count = 0
    total_queries = len(evaluation_set)

    for i, item in enumerate(evaluation_set):
        query = item["query_code"]
        expected_vuln = item["expected_vulnerability"]
        
        print(f"\n[{i+1}/{total_queries}] Querying for: '{expected_vuln}'...")
        
        results = vector_store.similarity_search_with_score(query, k=k)

        if not results:
            print("    -> No results found.")
            continue

        top_k_results = [doc.metadata.get("Vulnerability Name") for doc, score in results]

        processed_results = []
        for name in top_k_results:
            name=str(name)
            cleaned_name = name.split("#")[1].strip()
            processed_results.append(cleaned_name)

        if expected_vuln in processed_results:
            hit_count += 1
            print(f"SUCCESS: Found '{expected_vuln}' in top {k} results.")
        else:
            print(f"FAILED: Did not find '{expected_vuln}'.")
            if verbose:
                for j, (doc, score) in enumerate(results, start=1):
                    print("\n    --- Incorrect Match Details ---")
                    print(f"    === Match #{j} (score = {score:.4f}) ===")
                    print("    Vulnerability Name: ", doc.metadata.get("Vulnerability Name", "N/A"))
                    print("    -----------------------------")

    print("\n--- Evaluation Summary ---")
    hit_rate = (hit_count / total_queries) * 100 if total_queries > 0 else 0
    print(f"Hit Rate (Top-{k}): {hit_rate:.2f}% ({hit_count}/{total_queries})")


def main():
    """Main function to run the RAG pipeline."""
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    if not Path(PERSIST_DIR).exists():
        raw_documents = load_documents(DOCS_DIR)
        
        processed_documents = process_documents(raw_documents)
        
        vector_store = build_or_load_knowledge_base(
            processed_docs=processed_documents,
            persist_path=PERSIST_DIR,
            collection_name=COLLECTION_NAME,
            embedding_model=embeddings
        )
    else:
        vector_store = build_or_load_knowledge_base(
            processed_docs=[], 
            persist_path=PERSIST_DIR,
            collection_name=COLLECTION_NAME,
            embedding_model=embeddings
        )

    if vector_store:
        evaluate_retriever(vector_store, EVALUATION_SET, k=1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")