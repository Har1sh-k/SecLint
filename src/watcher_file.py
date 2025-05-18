from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from status_logger import logger
from load_config import config_loader
from main import main

from time import sleep
import os

class EventHandler(FileSystemEventHandler):
    def on_any_event(self, event: FileSystemEvent):
        if (event.event_type == 'modified' or event.event_type == 'created') and (event.src_path.endswith('.py') or event.src_path.endswith('.js')):
            logger("info",f"File detected: {event.src_path}")
            main(event.src_path)
            

if __name__ == "__main__":
    config = config_loader()
    file_source= config.get("file_source")

    try:
        if not file_source:
            raise ValueError("File source not specified in the configuration.")
        elif not os.path.exists(file_source):
            raise FileNotFoundError(f"File source path does not exist: {file_source}")
    except ValueError as e:
        logger("critical", f"Error: {e}")
        raise
    
    event_handler = EventHandler()
    observer = Observer()
    observer.schedule(event_handler, file_source, recursive=True)
    observer.start()

    logger("info", f"Monitoring started on: {file_source}")
    try:
        while True:
            sleep(1)
            pass
    except KeyboardInterrupt:
        observer.stop()
    finally:
        observer.stop()
        observer.join()
        logger("info", "Monitoring stopped.")