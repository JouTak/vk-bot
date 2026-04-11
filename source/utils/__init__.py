from .ignored_list import IgnoredList
from .vk_helper import *
import os

from dotenv import load_dotenv


def initialize():
    # Load env vars from local .env if present (does not override existing env)
    load_dotenv(override=False)

    token = os.getenv("BOT_TOKEN")
    group_id = os.getenv("GROUP_ID")

    return token, group_id
