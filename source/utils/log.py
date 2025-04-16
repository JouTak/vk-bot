import logging

logger = logging.getLogger()

formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%d.%m.%y %H:%M:%S")

file_handler = logging.FileHandler("py.log", mode="a")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log():
    def info(_):
        logger.info(_)
    def warn(_):
        logger.warning(_)
    def error(_):
        logger.error(_)

    return info, error