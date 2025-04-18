import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import traceback
from utils import IgnoredList, initialize
from utils import VKHelper
from utils.log import *
from bot import *


class Main:
    def __init__(self):
        self.token = initialize()
        self.group_id = 217494619  #230160029

        self.vk_session = vk_api.VkApi(token=self.token)
        self.VK = VKHelper(self.vk_session)

        self.users = UserList(users_path, self.VK)
        print('\n'.join(warnings))

        self.info, self.error = log()
        self.longpoll = VkBotLongPoll(self.vk_session, self.group_id)
        self.ignored = IgnoredList()
        self.info(self.ignored.load_from_file())
        self.info('готов!\n')

    def run(self):
        while True:
            try:
                for event in self.longpoll.listen():
                    self.process_event(event)
            except Exception as e:
                self.error(e)
                traceback.print_exc()

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

    def handle_actions(self, actions: list[dict]):
        if not actions:
            return
        print(actions)
        for action in actions:
            peer_id = action.get('peer_id')
            message = action.get('message', '')
            keyboard = action.get('keyboard')
            attachment = action.get('attachment')
            # message_sync = {
            #     'user_message': {'peer_id': None, 'conversation_message_id': None},
            #     'manager_message': {'peer_id': None, 'conversation_message_id': None}
            # }
            try:
                self.VK.send_message(peer_id, message, keyboard, attachment)
            except Exception as e:
                self.error(f'Ошибка обработки действия: {e}')


if __name__ == '__main__':
    bot = Main()
    bot.run()
