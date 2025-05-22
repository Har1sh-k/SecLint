from status_logger import logger
from preprocess.code_splitter import split_code

def reader(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            split_codes = split_code(content)
    except FileNotFoundError:
        logger("error", f"File not found: {file_path}")
    except Exception as e:
        logger("error", f"An error occurred: {e}")