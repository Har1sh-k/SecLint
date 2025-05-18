from status_logger import logger

def reader(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            # call splitter function here
    except FileNotFoundError:
        logger("error", f"File not found: {file_path}")
    except Exception as e:
        logger("error", f"An error occurred: {e}")