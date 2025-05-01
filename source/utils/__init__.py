from .ignored_list import IgnoredList
from .VKHelper import *
import os


def initialize():
    # with open('token.txt', 'r') as f:
    #     token = f.readline()
    token = os.getenv('BOT_TOKEN')
    group_id = os.getenv('GROUP_ID')

    return token, group_id