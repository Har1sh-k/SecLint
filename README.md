<div align="center">

# SecLint  
### Code Vulnerability Analysis Agent

*<em>A context-aware vulnerability scanner for Python code</em>*  

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://opensource.org/licenses/AGPL-3.0)

</div>

A Python-based AI agent for detecting insecure code patterns in a Python project and providing context-based remediation suggestions. It leverages a Retrieval-Augmented Generation (RAG) approach with OpenAI embeddings and ChromaDB for vector storage.


## High-Level Overview

SecLint is an AI-powered code vulnerability analysis tool that:

* **Monitors** your project directory for Python file changes.
* **Chunks** code using Python's Abstract Syntax Tree (AST) to isolate functions, classes, and global statements while still retaining the code logic.
* **Understands Context** of the code snippets’ purpose and behavior through an LLM-driven analysis step.
* **Retrieves** relevant secure coding guidelines from a local knowledge base (ChromaDB) built on OWASP practices.
* **Generates** contextual remediation recommendations with GPT-4/o4-mini-high.

Unlike traditional static code analyzers, SecLint leverages a contextual LLM-driven RAG pipeline to provide best practices and actionable guidance that are relevant to your use case.

---


## Installation

Before installing and running SecLint, ensure you have **OpenAI API Key**. An OpenAI API key is required for the LLM components. SecLint uses the OpenAI GPT-4 model via LangChain; make sure to set your API key as an environment variable (`OPENAI_API_KEY`) or in a `.env` file. The tool will automatically load environment variables using `python-dotenv`.

To set up SecLint on your local machine, follow these steps:

1. **Clone the Repository:** Clone the SecLint repository to your local system:

   ```bash
   git clone https://github.com/Har1sh-k/SecLint.git
   cd SecLint
   ```
2. **Create a Virtual Environment (optional):** It’s good practice to use a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```
3. **Install Dependencies:** Install the required Python packages.

   ```bash
   pip install -r requirements.txt
   ```
4. **Configure API Access:** Create a `.env` file in the project root (or otherwise set environment variables) with your OpenAI credentials:

   ```bash
   echo "OPENAI_API_KEY=<your-openai-key>" > .env
   ```

   This key is required to run the LLM queries. SecLint will load this automatically at runtime.

5. **Adjust Configuration:** The file `src/config.yaml` contains default configuration (the path to analyze), which should be modified as needed.

6. **Build Knowledge Base:** *(Recommended prior to first use)* Run the knowledge base ingestion script to prepare the vector store of security guidelines (see [RAG Setup](#rag-setup-knowledge-base) below for details):

   ```bash
   python src/load_kb.py
   ```

   This will parse the markdown files under `src/security_docs` and embed them into a local Chroma vector database for quick retrieval. If this step is skipped, SecLint will still run, but it may not retrieve any best-practice guidelines for code analysis.


---

## Usage

SecLint can be used to scan a Python file (or potentially a project) for vulnerabilities and get detailed explanations and remediation steps. Currently, the tool is invoked via the Python API/CLI:


* **Automated Directory Analysis:** *Planned:*  The watcher script (`watcher_file.py`) will monitor your directory: it listens for file-save events on `.py` files and automatically scans each saved file.

* **Single File Analysis:** Alternatively, to analyze one file without the watcher, run the `main.py` module and provide the target file path. You can use the Python REPL or an interactive environment:

  ```python
  from src import main
  main.main("path/to/your/script.py")
  ```

After running SecLint on a file, the output will be printed to the console. The output is a structured report containing, for each code snippet analyzed:

* **Context:** A brief description of what the snippet does, provided by the LLM.
* **Severity:** Critical | High | Medium | Low | None (if no vulnerabilities).
* **Best Practices:** Relevant secure coding guidelines retrieved from the LLM based on knowledge base.
* **Recommendation Summary:** A list of concrete remediation steps suggested by the AI agent and a final summary assessment for the snippet (or a note if no issues were found).

---

## Code Structure

The SecLint project is organized into modules, each handling a different aspect of the analysis. Below is a brief overview of the major files and their roles:

* **`watcher_file.py`**: Monitors a target directory for `.py` file changes and triggers analysis.
* **`src/preprocess/code_getter.py`**: Reads files and prepares raw code for splitting.
* **`src/preprocess/code_splitter.py`**: Uses the AST to break code into functions, classes, and global statements.
* **`src/vulnerability_scanner.py`**: Orchestrates the ReAct agent workflow over code chunks.
* **`src/tools/vuln_tools.py`**: Defines LLM-callable tools: `understand_context`, `fetch_secure_coding_guidelines`, `generate_recommendations`.
* **`src/tools/security_kb.py`**: Interfaces with the ChromaDB vector store to retrieve best-practice metadata.
* **`src/load_kb.py`**: Builds or refreshes the RAG knowledge base from Markdown docs.
* **`src/security_docs/`**: Markdown source files with vulnerability descriptions and OWASP secure coding practices.
    - Classification Rationale: [OWASP Secure Coding Practices Quick Reference Guide – Checklist](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/stable-en/02-checklist/05-checklist.html)

*(Additionally, there may be configuration or helper files not listed here. For instance, `config.yaml` holds default settings like the file path to scan, which could be utilized in future enhancements.)*

---

## RAG Setup (Knowledge Base)
1. Run:

   ```bash
   python src/load_kb.py
   ```
   * Splits documents by headings and creates `Document` objects
   * Embeds insecure code examples via OpenAI embeddings
   * Stores them in `insec_code_kb/` ChromaDB collection `vulns_insecure`

2. At runtime, agent performs similarity search with snippet embeddings and returns OWASP-based best practices.

---

## Workflow in Detail

Putting it all together, here is the step-by-step workflow of SecLint when analyzing Python files:

1. **Watcher Initialization:** Launch `watcher_file.py` with the `config.yaml` file to specify the directory to monitor. The watcher uses `watchdog` to listen for file save events on `.py` files.
2. **File Detection & Read:** Upon detecting a save event, the watcher logs the update and invokes the `reader` function to load the changed source file.
3. **Code Chunking:** The `code_splitter.split_code` utility parses the file’s AST and splits it into distinct chunks (functions, classes, global statements), each accompanied by metadata (function/class name, type, start/end lines). 
4. **Agent Setup:** SecLint instantiates a Secure Coding Agent:
   * Configures a system prompt and three custom tools: `understand_context`, `fetch_secure_coding_guidelines`, and `generate_recommendations`.
   * Uses the ReAct pattern to orchestrate tool execution.
5. **Chunk Analysis Loop:** For each code chunk:
   * **Context Understanding:** Calls `understand_context(chunk)`, where the LLM returns a concise summary of the snippet’s purpose.
   * **Guideline Retrieval:** Calls `fetch_secure_coding_guidelines(chunk)`, performing a similarity search in the ChromaDB knowledge base to retrieve relevant OWASP-based best practices.
   * **Recommendation Generation:** Calls `generate_recommendations(chunk, best_practices)`, prompting the LLM to produce JSON-formatted remediation steps that leverage both context and retrieved guidelines.
6. **Result Aggregation:** Aggregates the outputs—context, best practices, recommendations, final summary, and severity—into a structured result object for each chunk.
7. **Reporting:** Prints a consolidated report to the console, either as a JSON array or a formatted summary, detailing findings and remediation guidance for each code chunk.
8. **Completion:** After processing all chunks, SecLint starts monitoring the directory again to repeat the process.

This workflow ensures continuous, context-aware vulnerability scanning throughout development, with minimal manual intervention.

---

## Extending the Knowledge Base

To extend SecLint’s knowledge base, add new vulnerability guidelines in Markdown format to the `src/security_docs/` directory. Each file should be named `<vulnerability_name>.md` and follow this structure:
```markdown
# Vulnerability Name 

## Explanation
A concise description of the vulnerability and its implications.

## Insecure Example
A code snippet demonstrating the insecure pattern.

## OWASP Practices
A list of relevant OWASP or CWE guidelines (e.g., use parameterized queries, validate input).

## Secure Example
A corrected code snippet illustrating secure remediation.

## References
- Link to OWASP or CWE documentation.
- Other external resources.
```
- Classification Rational: [OWASP Secure Coding Practices Quick Reference Guide – Checklist](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/stable-en/02-checklist/05-checklist.html)

After adding or updating documents, rebuild the knowledge base:

```bash
python src/load_kb.py
```

This will ingest and index your new content into the ChromaDB collection (`vulns_insecure`), making them available for runtime retrieval..

---


**Note:** While SecLint is a powerful assistant, it is not a substitute for thorough security reviews by experts. The LLM’s suggestions are based on patterns and the provided knowledge base; complex or subtle vulnerabilities might not be fully recognized. However, SecLint excels at providing human-readable insights and justifications, making it a valuable tool for anyone looking to improve the security of their Python code.

<div align="center">

© 2025 [Har1sh-k](https://github.com/Har1sh-k) • 📜 **Licensed under the [AGPLv3](LICENSE)** 📜

</div>
