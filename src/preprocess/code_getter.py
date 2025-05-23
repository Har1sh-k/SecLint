from status_logger import logger
from preprocess.code_splitter import split_code
import os

def reader(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            file_name = os.path.basename(file_path)
            logger("info", f"Chunking code from {file_name}...")
            split_codes = split_code(content, file_name)
            logger("debug", f"Code split into {len(split_codes)} chunks.")
            
    except FileNotFoundError:
        logger("error", f"File not found: {file_path}")
    except Exception as e:
        logger("error", f"An error occurred: {e}")