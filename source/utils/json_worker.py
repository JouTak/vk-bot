import os
import json


def is_file_accessible(filepath: str) -> bool:
    if not os.path.exists(filepath):
        return False
    if not os.path.isfile(filepath):
        return False
    if not os.access(filepath, os.R_OK):
        return False
    return True


def is_json(myjson: str) -> bool:
    try:
        json.loads(myjson)
    except ValueError as e:
        return False
    return True
