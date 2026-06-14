from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import traceback
import time
from utils import IgnoredList, initialize
from utils.db.db import init_engine
from utils.log import *
from bot import *
import requests
from requests.exceptions import ConnectionError
from urllib3.exceptions import MaxRetryError
from http.client import RemoteDisconnected
import re


class Main:
    def __init__(self):
        self.token, self.group_id = initialize()

        # Initialize DB engine (DATABASE_URL from env/.env)
        init_engine()

        self.vk_session = vk_api.VkApi(token=self.token)
        self.VK = VKHelper(self.vk_session, self.group_id)
        self.info, self.warn, self.error = log()
        self.longpoll = VkBotLongPoll(self.vk_session, self.group_id)
        self.ignored = IgnoredList()
        self.info(self.ignored.load_from_file())
        self.users = UserList(users_path, self.VK)

        # Inject Y26 event data
        try:
            from utils.storage.inject_y26 import inject_y26
            stats = inject_y26(self.VK)
            source = stats.get("source", "none")
            if source != "none":
                print(f"[Y26] Source: {source}, upserted: {stats.get('upserted', 0)}, skipped: {stats.get('skipped', 0)}")
            if stats.get("errors"):
                for err in stats["errors"]:
                    print(f"[Y26] {err}")
        except Exception as e:
            print(f"[Y26] Injection error: {e}")

        if warnings:
            self.warn('\n'.join(warnings))
        self.info('Готов!\n')

    def run(self):
        while True:
            for event in self.longpoll.listen():
                self.process_event(event)

    def process_event(self, event):
        if event.type == VkBotEventType.MESSAGE_NEW:
            self.handle_message_new(event)
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            self.handle_message_event(event)

    def handle_message_new(self, event):
        result = process_message_new(self, event, self.VK, self.ignored)
        self.handle_actions(result)

    def handle_message_event(self, event):
        result = process_message_event(self, event, self.VK)
        self.handle_actions(result)

    def handle_actions(self, actions: list[dict]) -> dict:
        """
        Send messages and return stats with errors.
        
        Returns dict with:
            - sent: number of successfully sent messages
            - failed: list of (peer_id, error_msg) tuples
        """
        if not actions:
            return {"sent": 0, "failed": []}
        
        result = {"sent": 0, "failed": []}
        
        for i in range(0, len(actions), 25):
            chunk = actions[i:i + 25]
            try:
                responses = self.VK.send_messages(chunk)
                for action, response in zip(chunk, responses):
                    if isinstance(response, dict) and response.get("error"):
                        err = response["error"]
                        error_msg = err.get("error_msg", str(err))
                        result["failed"].append((action.get("peer_id"), error_msg))
                    elif response:
                        result["sent"] += 1
                    else:
                        result["failed"].append((action.get("peer_id"), "Пустой ответ"))
            except Exception as e:
                # If whole batch failed
                for action in chunk:
                    result["failed"].append((action.get("peer_id"), str(e)))
        
        return result


if __name__ == '__main__':
    bot = Main()

    while True:
        try:
            bot.run()
        except requests.exceptions.ReadTimeout:
            pass
        except (ConnectionError, MaxRetryError, RemoteDisconnected) as e:
            # Transient network errors (DNS failures, connection drops) — retry with backoff
            print(f"[Network] {type(e).__name__}: {e}")
            time.sleep(1)
        except OSError as e:
            # Only catch network-related OSError subclasses
            if isinstance(e, (ConnectionResetError, BrokenPipeError, TimeoutError)):
                print(f"[Network] {type(e).__name__}: {e}")
                time.sleep(1)
            else:
                raise  # Re-raise unexpected OSError
        except Exception as e:
            bot.error(e)
            bot.VK.send_messages([{'peer_id': uid, 'message': str(e)} for uid in admin])
            traceback.print_exc()
