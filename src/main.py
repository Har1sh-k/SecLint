from pathlib import Path
from status_logger import logger
from load_config import config_loader
from preprocess.code_getter import reader
from vulnerability_scanner import code_scanner

base_dir = Path(__file__).parent
persist_directory = "./insec_code_kb"
db_collection_name='vulns_insecure'

def main(file_path):
    logger("info", "Starting the application...")
    code_chunks=reader(file_path)
    if code_chunks:
        logger("info", f"Successfully processed {len(code_chunks)} code chunks.")
        logger("info", "Starting vulnerability scanning...")

        recommendations = code_scanner(code_chunks, persist_directory, db_collection_name)

    else:
        logger("warning", "No code chunks were processed.")
        logger("info", "Exiting the application...")
        return
