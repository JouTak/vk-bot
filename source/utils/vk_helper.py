from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import vk_api
from vk_api.utils import get_random_id
import json


class VKHelper:
    """
    A helper class to simplify interactions with the VK API,
    especially for sending messages and resolving links.
    """
    def __init__(self, vk_session, group_id):
        """
        Initializes the VKHelper with a VK API session.

        Args:
            vk_session: An initialized vk_api.VkApi session object.
        """
        self.vk = vk_session.get_api()
        self.vk_session = vk_session
        self.group_id = group_id

    def lsend(self, id, text):
        """
        Sends a private message to a specific user (legacy function).

        Args:
            id (int): The user ID to send the message to.
            text (str): The message text.
        """
        print('sended to ' + str(id))
        self.vk_session.method('messages.send', {'user_id': id, 'message': text, 'random_id': 0})

    def lsend_with_a(self, id, text, attachment):
        """
        Sends a private message with an attachment to a specific user (legacy function).

        Args:
            id (int): The user ID.
            text (str): The message text.
            attachment (str): Attachment string (e.g., 'photo123_456').
        """
        print(f'Sending to chat: {id}')
        self.vk_session.method('messages.send',
                               {'user_id': id, 'message': text, 'attachment': attachment, 'random_id': 0})

    def send(self, id, text):
        """
        Sends a message to a chat (legacy function).

        Args:
            id (int): The chat ID to send the message to.
            text (str): The message text.
        """
        print(f'Sending to chat: {id}')
        self.vk_session.method('messages.send', {'chat_id': id, 'message': text, 'random_id': 0})

    def send_message(self, peer_id, message, keyboard=None, attachment=None):
        """
        Sends a message to a peer (user or chat) with optional keyboard and attachment.

        This is a more flexible and robust message sending method.

        Args:
            peer_id (int): The peer ID (user ID or chat ID).
            message (str): The message text.
            keyboard (dict, optional): Dictionary representing a VK keyboard. Defaults to None.
            attachment (str, optional): Attachment string. Defaults to None.

        Raises:
            Exception: If there's an API error during message sending.
        """
        payload = {
            'peer_id': peer_id,
            'message': message,
            'random_id': 0 # Use dynamic random_id for production to avoid duplicates
        }
        if keyboard is not None:
            payload['keyboard'] = keyboard
        if attachment is not None:
            payload['attachment'] = attachment

        try:
            self.vk.messages.send(**payload)
        except vk_api.exceptions.ApiError as e:
            raise Exception(f'Ошибка отправки сообщения: {e}')

    def links_to_uids(self, links: list[str]) -> list[int]:
        """
        Resolves a list of VK links (i.g., screen names) to their corresponding user IDs.

        Uses VK's `execute` method to perform multiple `utils.resolveScreenName` calls
        in a single API request, which is efficient.

        Args:
            links (list[str]): A list of VK screen names or links.

        Returns:
            list[int]: A list of resolved user IDs (0 if not resolved).
        """
        parts = [f'API.utils.resolveScreenName({{"screen_name": "{link}"}})' for link in links]
        code = f'return [{",".join(parts)}];'
        response = self.vk_session.method("execute", {"code": code})
        # Extract object_id if it's a dict, otherwise default to 0 (for unresolved or non-user links)
        return [i['object_id'] if isinstance(i, dict) and 'object_id' in i.keys() else '0' for i in response]

    def send_messages(self, messages: list[dict]) -> list[dict]:
        """
        Sends multiple messages efficiently using VK's `execute` method.

        Each message dictionary should contain 'peer_id' and 'message'.
        Adds 'group_id' and 'random_id' to each message payload.

        Args:
            messages (list[dict]): A list of message dictionaries.

        Returns:
            list[dict]: The response from the VK API for each message sent.
        """
        for d in messages:
            d['group_id'] = self.group_id
            d['random_id'] = get_random_id()
        # Serialize each message payload to JSON for the execute method
        parts = [f'API.messages.send({json.dumps(d, ensure_ascii=False)})' for d in messages]
        code = f'return [{",".join(parts)}];'
        response = self.vk_session.method("execute", {"code": code})
        return response


def create_keyboard(buttons):
    """
    Creates an inline keyboard with callback buttons from a list of button definitions.

    Args:
        buttons (list[dict]): Each dict should have keys 'label', 'payload', 'color', and optionally 'newline'.

    Returns:
        str | None: JSON string of the keyboard or None if no buttons provided.
    """
    keyboard = VkKeyboard(inline=True)
    for button in buttons:
        if button.get('newline'):
            keyboard.add_line()
        keyboard.add_callback_button(
            label=button['label'],
            payload=button['payload'],
            color=getattr(VkKeyboardColor, button['color'].upper())
        )
    return keyboard.get_keyboard() if buttons else None


def create_standard_keyboard(buttons):
    """
    Creates a non-inline keyboard with regular buttons from a list of button definitions.

    Args:
        buttons (list[dict]): Each dict should have keys 'label', 'payload', 'color', and optionally 'newline'.

    Returns:
        str: JSON string of the keyboard.
    """
    keyboard = VkKeyboard(inline=False)
    for button in buttons:
        if button.get('newline'):
            keyboard.add_line()
        keyboard.add_button(
            label=button['label'],
            payload=button['payload'],
            color=getattr(VkKeyboardColor, button['color'].upper())
        )
    return keyboard.get_keyboard()


def create_link_keyboard(buttons):
    """
    Creates an inline keyboard with open link buttons from a list of button definitions.

    Args:
        buttons (list[dict]): Each dict should have keys 'label', 'payload', and 'link', and optionally 'newline'.

    Returns:
        str: JSON string of the keyboard.
    """
    keyboard = VkKeyboard(inline=True)
    for button in buttons:
        if button.get('newline'):
            keyboard.add_line()
        keyboard.add_openlink_button(
            label=button['label'],
            payload=button['payload'],
            link=button['link']
        )
    return keyboard.get_keyboard()
