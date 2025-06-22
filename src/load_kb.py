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



if __name__ == "__main__":
    base_dir = Path(__file__).parent
    docs_dir = base_dir / "security_docs"
    persist_directory = "./insec_code_kb"
    try:
        doc_data=get_all_files(docs_dir)
        data=split_docs_h2(doc_data)
        load_kb(data)
        print("Knowledge base loaded successfully.")

        #test the knowledge base

    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")
    except PermissionError as e:
        print(f"PermissionError: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")