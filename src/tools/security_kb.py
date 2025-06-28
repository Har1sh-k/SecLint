from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from pathlib import Path
from status_logger import logger
from dotenv import load_dotenv
load_dotenv()


def get_best_practices(code_snippet):
    persist_directory = "./insec_code_kb"
    print(persist_directory)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    kb = Chroma(
        embedding_function=embeddings,
        persist_directory=persist_directory,
        collection_name="vulns_insecure"
    )
    docs = kb.similarity_search(code_snippet, k=1)
    if not docs:
        logger("info", "No best-practices found for this snippet.")
        return None
    best_practices = "\n\n".join(doc.metadata.get("Secure Coding Practices", "N/A") for doc in docs)
    return best_practices

