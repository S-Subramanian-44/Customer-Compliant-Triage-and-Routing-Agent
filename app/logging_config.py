import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, 'agent.log')

def setup_logging(level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(ch_formatter)

    # Rotating file handler
    fh = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5)
    fh.setLevel(level)
    fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    fh.setFormatter(fh_formatter)

    # Avoid adding multiple handlers on repeated setup
    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger