from pathlib import Path
from status_logger import logger
from load_config import config_loader
from preprocess.code_getter import reader
from vulnerability_scanner import code_scanner



def main(file_path):
    logger("info", "Starting the application...")
    code_chunks=reader(file_path)
    if code_chunks:
        logger("info", f"Successfully processed {len(code_chunks)} code chunks.")
        logger("info", "Starting vulnerability scanning...")

        code_scanner(code_chunks)

    else:
        logger("warning", "No code chunks were processed.")
        logger("info", "Exiting the application...")
        return

if __name__ == "__main__":
    config = config_loader()
    file_source = "D:\\GIT\\git repos\\test_secLint\\hey.py"

    if not file_source:
        logger("critical", "File source not specified in the configuration.")
        raise ValueError("File source not specified in the configuration.")

    file_path = Path(file_source)
    if not file_path.exists():
        logger("critical", f"File source path does not exist: {file_path}")
        raise FileNotFoundError(f"File source path does not exist: {file_path}")

    main(file_path)