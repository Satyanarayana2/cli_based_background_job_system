import logging
import os
from queuectl import config

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "data", "logs")
LOG_FILE = os.path.join(LOG_DIR, "queuectl.log")

def setup_logging():
    """
    Configure logging to both console and file.
    Reads log level from config.json.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    cfg = config.load_config()
    log_level_name = cfg.get("log_level", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    # Clear any old handlers to prevent duplicate logs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

def log_info(msg):
    logging.info(msg)

def log_warning(msg):
    logging.warning(msg)

def log_error(msg):
    logging.error(msg)

def log_debug(msg):
    logging.debug(msg)

def log_critical(msg):
    logging.critical(msg)
