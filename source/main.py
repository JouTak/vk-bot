import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import traceback
from utils import IgnoredList, initialize
from utils import VKHelper
from utils.log import *
from bot import *


class Main:
    def __init__(self):
        self.token, self.group_id = initialize()

        self.vk_session = vk_api.VkApi(token=self.token)
        self.VK = VKHelper(self.vk_session)
        self.info, self.error = log()
        self.longpoll = VkBotLongPoll(self.vk_session, self.group_id)
        self.ignored = IgnoredList()
        self.info(self.ignored.load_from_file())
        self.users = UserList(users_path, self.VK)
        print('\n'.join(warnings))

        self.info('готов!\n')

    def run(self):
        while True:
            try:
                for event in self.longpoll.listen():
                    self.process_event(event)
            except Exception as e:
                self.error(e)
                self.VK.send_messages([{'peer_id': uid, 'message': str(e)} for uid in admin])
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

    def handle_actions(self, actions: list[dict]) -> int:
        if not actions:
            return 0
        counter = 0
        for i in range(0, len(actions), 25):
            chunk = actions[i:min(i + 25, len(actions))]
            responses = self.VK.send_messages(chunk)
            for action, response in zip(chunk, responses):
                if not response:
                    # print('Something wrong with', action)
                    continue
                else:
                    # print('Success with', action)
                    counter += 1
        return counter


if __name__ == '__main__':
    bot = Main()
    bot.run()
