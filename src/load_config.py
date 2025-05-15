import yaml
import os

from status_logger import logger

def config_loader(config_path="src/config.yaml"):
    config = None
    try:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as e:
        logger("critical", f"Error parsing configuration YAML file: {e}")
    except FileNotFoundError as e:
        logger("critical", f"Configuration file not found: {e}")
    except Exception as e:
        logger("critical", f"An unexpected error occurred while loading config: {e}")
    finally:
        if config:
            logger("info", "Configuration loaded successfully.")
        else:
            logger("error", "Failed to load configuration.")
        return config
    