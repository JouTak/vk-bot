import logging
import os
from pathlib import Path

logger = logging.getLogger()

formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%d.%m.%y %H:%M:%S")

# Prefer configurable path; default is Docker-friendly, but must not crash locally.
log_path = Path(os.getenv("LOG_PATH", "/app/data/py.log"))
try:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(str(log_path), mode="a", encoding="utf-8")
except Exception:
    # Fallback: no file logging if path is not writable/available (keeps app working locally).
    file_handler = None

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger.setLevel(logging.DEBUG)
if file_handler is not None:
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log():
    def info(_, error=False):
        if error:
            logger.error(_)
        else:
            logger.info(_)

    def warn(_):
        logger.warning(_)

    def error(_):
        logger.error(_)

    return info, warn, error
