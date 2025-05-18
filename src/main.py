from status_logger import logger
from load_config import config_loader
from preprocess.code_getter import reader

def main(file_path):
    logger("info", "Starting the application...")
    code_chunks=reader(file_path)
