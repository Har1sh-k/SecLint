from pathlib import Path

def get_all_files(docs_dir):  
    if not docs_dir.is_dir():
        raise FileNotFoundError(f"Could not find security_docs at: {docs_dir}")

    md_files = list(docs_dir.glob("**/*.md"))

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        print(f"Loaded {md_file.name} with {len(content)} characters.")




if __name__ == "__main__":
    base_dir = Path(__file__).parent
    docs_dir = base_dir / "security_docs"
    try:
        get_all_files(docs_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")