from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader



def get_all_files(docs_dir):
    loader = DirectoryLoader(
        path=str(docs_dir),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    docs = loader.load()
    print(f"Loaded {len(docs)} documents from {docs_dir}")
    print(f"First document content: {docs[0].page_content[:100]}...")  



if __name__ == "__main__":
    base_dir = Path(__file__).parent
    docs_dir = base_dir / "security_docs"
    try:
        get_all_files(docs_dir)
    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
    except PermissionError as e:
        print(f"PermissionError: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")