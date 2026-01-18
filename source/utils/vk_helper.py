from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import vk_api
from vk_api.utils import get_random_id
import json
import time


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
            'random_id': 0  # Use dynamic random_id for production to avoid duplicates
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
        # VK execute has a hard limit: up to 25 API.* calls per execute.
        # Some injectors can easily exceed it (e.g. A25 table), so we batch and retry gracefully.

        def extract_screen_name(link: str) -> str:
            if link is None:
                return ''
            s = str(link).strip()
            if not s:
                return ''
            # Drop query/fragment
            s = s.split('?', 1)[0].split('#', 1)[0]
            # If it contains '/', take last segment
            if '/' in s:
                s = s.rsplit('/', 1)[-1]
            # If it contains '@', take part after '@'
            if '@' in s:
                s = s.split('@', 1)[-1]
            return s.strip()

        def api_error_code(err: Exception) -> int | None:
            # vk_api ApiError usually has .code, but be defensive.
            for attr in ('code', 'error_code'):
                v = getattr(err, attr, None)
                if isinstance(v, int):
                    return v
            # Fallback: try to parse like "[13] ..." from string
            try:
                txt = str(err)
                if txt.startswith('['):
                    end = txt.find(']')
                    if end != -1:
                        return int(txt[1:end])
            except Exception:
                pass
            return None

        def execute_with_retry(code: str, attempts: int = 4) -> list:
            delay = 0.6
            for n in range(attempts):
                try:
                    return self.vk_session.method('execute', {'code': code})
                except vk_api.exceptions.ApiError as e:
                    c = api_error_code(e)
                    # 6 = too many requests per second; 13 = execute runtime error (often too many internal calls)
                    if c in (6, 13) and n < attempts - 1:
                        time.sleep(delay)
                        delay *= 1.8
                        continue
                    raise

        # Normalize links to screen names and preserve order
        screen_names: list[str] = [extract_screen_name(l) for l in links]
        out: list[int] = [0] * len(screen_names)
        idxs = [i for i, name in enumerate(screen_names) if name]
        if not idxs:
            return out

        # Batch by 25 (execute limit)
        for start in range(0, len(idxs), 25):
            part_idxs = idxs[start:start + 25]
            part_names = [screen_names[i] for i in part_idxs]

            # Build execute code; json.dumps keeps escaping safe.
            parts = [f'API.utils.resolveScreenName({json.dumps({"screen_name": name}, ensure_ascii=False)})'
                     for name in part_names]
            code = f'return [{",".join(parts)}];'
            response = execute_with_retry(code)

            # Extract object_id if it's a dict, otherwise 0
            for i, resp in zip(part_idxs, response):
                if isinstance(resp, dict) and 'object_id' in resp:
                    try:
                        out[i] = int(resp['object_id'])
                    except Exception:
                        out[i] = 0
                else:
                    out[i] = 0

            # Small delay between executes to avoid request-per-second bursts
            if start + 25 < len(idxs):
                time.sleep(0.35)

        return out

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
