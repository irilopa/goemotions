import os
import logging
from logging.handlers import RotatingFileHandler
from .config import settings

def setup_logging(app):
    if not os.path.exists(settings.LOG_DIR):
        os.makedirs(settings.LOG_DIR)
    
    handler = RotatingFileHandler(
        os.path.join(settings.LOG_DIR, settings.LOG_FILE),
        maxBytes=settings.MAX_BYTES,
        backupCount=settings.BACKUP_COUNT
    )
    
    handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
