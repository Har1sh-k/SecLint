from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain.docstore.document import Document



def get_all_files(docs_dir):
    loader = DirectoryLoader(
        path=str(docs_dir),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    docs = loader.load()
    return docs

def split_docs_h2(docs):
    splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("##", "section")],
    strip_headers=True,     
    return_each_line=False,
    )
    output=[]
    for doc in docs:
        chunks = splitter.split_text(doc.page_content)
        chunks[0].metadata = {'section':"Vulnerability Name"}
        output.append(make_vuln_doc(chunks))

    return output

def make_vuln_doc(chunks):
    vul_name = explanation = secure_practices = secure_code_example = references = insecure_code = ""
    for chunk in chunks:
        section = chunk.metadata.get("section", "").strip()
        text = chunk.page_content.strip()
        
        if section == "Vulnerability Name":
            vul_name = text
        elif section == "Explanation":
            explanation = text
        elif section == "Secure Coding Practices (OWASP)":
            secure_practices = text
        elif section == "Secure Code Example":
            secure_code_example = text
        elif section == "References":
            references = text
        elif section == "Insecure Code Example":
            insecure_code = text
        else:
            print(f"Unknown section: {section}")

    doc= Document(
        page_content=insecure_code,
        metadata={
            "Vulnerability Name": vul_name,
            "Explanation": explanation,
            "Secure Coding Practices": secure_practices,
            "Secure Code Example": secure_code_example,
            "References": references,
        }
    )
    return doc

def load_kb(docs,persist_dir):
    embeddings = OpenAIEmbeddings()
    
    db = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name="vulns_insecure"
    )
    
    db.persist()
    
    print(f"Embedded and persisted {len(docs)} vulnerability documents.")
    return


def test_retrieval(persist_dir, query, k=2):
    embeddings = OpenAIEmbeddings()
    db = Chroma(
        embedding_function=embeddings,
        persist_directory=persist_dir,
        collection_name='vulns_insecure'
    )
    retriever = db.as_retriever(search_kwargs={'k': k})

    print("Querying with code snippet:\n", query)
    docs = retriever.get_relevant_documents(query)
    if not docs:
        print("No relevant documents found.")
        return
    for i, doc in enumerate(docs, 1):
        print(f"\n=== Match #{i} ===")
        print("Vulnerability Name:", doc.metadata["Vulnerability Name"])
        print("Insecure Example:\n", doc.page_content)
        print("Secure coding practices:", doc.metadata["Secure Coding Practices"])
        print("-" * 40)

    return 


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    docs_dir = base_dir / "security_docs"
    persist_directory = "./insec_code_kb"
    try:
        doc_data=get_all_files(docs_dir)
        data=split_docs_h2(doc_data)
        load_kb(data)
        print("Knowledge base loaded successfully.")

        test_query =  """
                def validate_access():
                abc="xyz"
                if abc == "xyz": print("Insecure code example")
                    return True
                    """
        print(f"Running retrieval for query: '{test_query}'\n")
        test_retrieval(persist_directory, test_query)

    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
    except PermissionError as e:
        print(f"PermissionError: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")