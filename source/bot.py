# -*- coding: utf-8 -*-
from utils.query_helper import MinecraftServerQuery
from utils.vk_helper import *
from utils.storage.user_store import User, UserList
# NOTE: legacy file-based user_list module is kept in repo but should not be imported after DB migration.
# Using db-backed UserList from utils.storage.user_store instead.
users_path = ""
warnings = []
inject_a25 = lambda *args, **kwargs: None

# DB: isu, uid, fio, grp, nck, {a24: {...}, s25: {...}, ...}

spartakiada_subs_path = './subscribers/spartakiada{}.txt'

admin = [297002785, 275052029, 325899178, 229488682]

itmocraft_ip = 'craft.itmo.ru'
joutak_ip = 'mc.joutak.ru'
joutak_link = 'https://joutak.ru'
form_link = 'https://forms.yandex.ru/u/6501f64f43f74f18a8da28de/'
telegram_link = 't.me/itmocraft'
discord_link = 'https://discord.gg/YVj5tckahA'
vk_link = 'https://vk.com/widget_community.php?act=a_subscribe_box&oid=-217494619&state=1|ITMOcraft'

info_message = (
    f'Добро пожаловать в клуб любителей Майнкрафта ITMOcraft! Наш клуб — комьюнити итмошников, которым нравится играть '
    f'в майнкрафт во всех его проявлениях: Выживание, моды, мини-игры: если во что-то можно играть, '
    f'мы создаём для этого условия. Недавно мы получили от университета ещё большие мощности, '
    f'поэтому с этой спартакиады мини-игры будут играться на постоянной основе! IP: {itmocraft_ip}. '
    f'Наша альма-матер — SMP JouTak. Это сервер с шестилетней историей '
    f'(без вайпов, без приватов, без случайных людей), в итмошном районе которого мы вместе уже построили Кронву, '
    f'Вязьму и даже Ленсовета, а игроки возводят свои проекты, болтают в войсике и просто отдыхают. '
    f'Более того, мы регулярно проводим там ивенты, самое время залететь на сервер 😇 '
    f'(+30дней, если у тебя лицензия)\n'
    f'Как это сделать?\n'
    f'1) Почитай информацию о том, что мы делаем, на нашем сайте: {joutak_link}\n'
    f'2) Заполняй анкету, чтобы мы с тобой связались: {form_link}\n'
    f'3) Следи за новостями в нашем телеграм канале: {telegram_link}.\n'
    f'Помогая нашему продвижению, ты делаешь ивенты масштабнее, а сервера круче!\n'
    f'P.S.: Плашку в ису "Член клуба ITMOcraft" тоже можно получить после заполнения этой анкеты, по желанию.\n'
    f'Если есть вопросы, в том числе по спартакиаде, пиши "АДМИН"!\n'
    f'\n'
    f'P.P.S.: У нас скоро начнётся осенняя Спартакиада, если хочешь, можешь зарегистрироваться: '
    f'[Зве, вставь сюда ссылку на регу]'
)

a25_message = '''
Вот твои данные за осеннюю Спартакиаду по Майнкрафту 2025!

ИСУ:
{isu}

Ник:
{nck}

Команда:
{met_a25_cmd}

Обязательно проверь все данные, только в случае несоответствий или важных вопросов напиши в ответ "АДМИН"
Читай о нас подробнее на сайте https://joutak.ru/minigames и других разделах
(Сообщение тестовое, будет дополняться)
'''.strip()

y25_message = '''
Вот твои данные по выезду в Ягодное 2025!

Едешь ли ты: 
{met_y25_ugo}

Ник:
{nck}

ФИО:
{fio}

Номер телефона:
{met_y25_nmb}

Планируешь ли взять бельё в ягодном:
{met_y25_bed}

Как планируешь добираться до Ягодного:
{met_y25_way}{part2}

В каком домике ты живёшь:
{met_y25_liv}

P.S.: У нас сейчас проходит осенняя Спартакиада по Майнкрафту 2025! Скорей беги регистрироваться!
[Зве, вставь сюда ссылку на регу]
'''.strip()

y25_second_part = '''

Номер машины:
{met_y25_car}
'''.rstrip()

s25_message = '''
Вот твои данные за весеннюю Спартакиаду по Майнкрафту 2025!

ИСУ:
{isu}

Ник:
{nck}

Участвуешь ли ты в первом этапе (BlockParty):
Да

Проходишь ли в следующий этап (AceRace):
{met_s25_wr1}

Поставят ли 10 баллов:
{met_s25_h10}

Рекорд раундов в BlockParty:
{met_s25_rr1}
{part2}{part3}
Обязательно проверь все данные, только в случае несоответствий или важных вопросов напиши в ответ "АДМИН"
Читай о нас подробнее на сайте https://joutak.ru/minigames и других разделах

P.S.: У нас сейчас проходит осенняя Спартакиада по Майнкрафту 2025! Скорей беги регистрироваться!
[Зве, вставь сюда ссылку на регу]
'''.strip()

s25_second_part = '''
Рекорд в AceRace:
{met_s25_rr2}

Проходишь ли ты в финал (SurvivalGames):
{met_s25_wr2}

'''

s25_third_part = '''
Место в финале:
{met_s25_fnl}

'''.lstrip()

a24_message = '''
Вот твои данные за осеннюю Спартакиаду по Майнкрафту 2024!

Ник:
{met_a24_nck}

Участвуешь ли ты в первом этапе:
Да

Использовал ли ты все попытки:
{met_a24_lr1}

Проходишь ли в следующий этап:
{met_a24_wr1}

Поставят ли 10 баллов:
{met_a24_h10}

{part2}{part3}
Обязательно проверь все данные, только в случае несоответствий или важных вопросов напиши в ответ "АДМИН"
Читай о нас подробнее на сайте https://joutak.ru/minigames и других разделах

P.S.: У нас сейчас проходит осенняя Спартакиада по Майнкрафту 2025! Скорей беги регистрироваться!
[Зве, вставь сюда ссылку на регу]
'''.strip()

a24_second_part = '''
Проходишь ли ты в финал:
{met_a24_wr2}

Ещё не отыграл в финале:
{met_a24_nyt}
'''

a24_third_part = '''
Победил ли в финале:
{met_a24_fnl}

'''.lstrip()


def flat_info2text() -> dict[str]:
    """
   Builds a flattened dictionary mapping user info keys and nested metadata keys
   to their corresponding textual representations.

   Combines top-level user info fields with nested metadata fields, prefixing metadata keys
   using the format 'met_<event>_<key>'. Also includes special boolean text fields.

   Returns:
       dict[str, Any]: A dictionary mapping flattened field names to text values.
    """
    result = {key: value for key, value in zip(User.keys[:-1], User.info2text[:-1])}
    for n, key in enumerate(tokens[3][:-1]):
        result[key] = User.info2text[n]
    for n, event in enumerate(tokens[4]):
        for key in tokens[5][n]:
            result[f'met_{event}_{key}'] = User.info2text[5][event][key]
    result['met_a24_h10'] = User.b2t
    result['met_s25_h10'] = User.b2t
    return result


tokens = (
    ('|', '&'),
    ('->', '!>'),
    ('==', '!=', '>>', '>=', '<<', '<='),
    User.keys,
    tuple(User.info2text[5].keys()),
    tuple(tuple(value.keys()) for value in User.info2text[5].values())
)
User.flat_i2t = flat_info2text()


def check_condition(cond: str, errors: list = None) -> str | None:
    """
    Validates a condition string against expected token structures.

    Recursively parses the condition, checking for syntax correctness,
    proper token usage, and argument counts based on predefined token groups.

    Args:
        cond (str): The condition string to check.
        errors (list, optional): Accumulator for error messages during recursion.

    Returns:
        str | None: 'ok' if no errors found, else a string containing error messages.
                    Returns None during recursion if errors are collected.
    """
    is_first = errors is None
    if is_first is True:
        errors = []

    # Check for tokens in the first token group (e.g., logical operators)
    if any(token in cond for token in tokens[0]):
        for token in tokens[0]:
            if token in cond:
                # Recursively validate each sub-condition separated by this token
                for c in cond.split(token):
                    check_condition(c, errors)
        # If this is the top-level call, return 'ok' or error messages
        if is_first is True:
            return 'ok' if len(errors) == 0 else '\n'.join(errors)
        return

    # Check for tokens in the second token group (e.g., metadata identifiers)
    elif any(token in cond for token in tokens[1]):
        for token in tokens[1]:
            if token in cond:
                c = cond.split(token)
                if len(c) > 2:
                    errors.append(f'A | too many args in "{cond}"')
                if len(c) < 2:
                    errors.append(f'B | not enough args in "{cond}"')
                # Recursively check first part of condition
                if c[0] not in tokens[4]:
                    check_condition(c[0], errors)
                # Validate second part of the condition
                if c[1] != 'met':
                    errors.append(f'C | token "{c[1]}" in "{cond}" is unknown')
        if is_first is True:
            return 'ok' if len(errors) == 0 else '\n'.join(errors)
        return

    # Check for tokens in the third token group (e.g., comparison operators)
    elif any(token in cond for token in tokens[2]):
        for token in tokens[2]:
            if token in cond:
                c = cond.split(token)
                if len(c) > 2:
                    errors.append('D | too many args in ' + cond)
                if len(c) < 2:
                    errors.append('E | not enough args in ' + cond)
                # Recursively validate left part of condition
                check_condition(c[0], errors)
                t = c[0].split('.')
                # Validate that base token exists in accepted tokens
                if t[0] not in tokens[3]:
                    errors.append(f'F | token "{t[0]}" in "{cond}" is unknown')
                # Validate argument types depending on token structure
                if len(t) == 1 and c[0] in tokens[2] and not User.text2info_check[tokens[2].index(c[0])](c[1]):
                    errors.append(f'G | token "{c[1]}" in "{cond}" has wrong type')
                elif len(t) == 3 and t[0] == 'met' and t[1] in tokens[4] and t[2] in tokens[5][tokens[4].index(t[1])]:
                    if not User.text2info_check[5][t[1]][t[2]](c[1]):
                        errors.append(f'H | token "{c[1]}" in "{cond}" has wrong type')
        if is_first is True:
            return 'ok' if len(errors) == 0 else '\n'.join(errors)
        return

    # Handle conditions with dots (likely nested metadata references)
    elif '.' in cond:
        c = cond.split('.')
        if c[0] == 'met':
            # Check presence of nested tokens
            if len(c) == 2:
                errors.append(f'I | token "{c[1]}" in "{cond}" is unknown')
            elif len(c) == 3:
                if c[1] not in tokens[4]:
                    errors.append(f'J | token "{c[1]}" in "{cond}" is unknown')
                elif c[2] not in tokens[5][tokens[4].index(c[1])]:
                    errors.append(f'K | token "{c[2]}" in "{cond}" is unknown')
            else:
                errors.append('L | too many args in ' + cond)
        else:
            errors.append(f'M | token "{c[0]}" in "{cond}" is unknown')
        if is_first is True:
            return 'N | not enough conditions'
        return

    # Condition token not recognized in any token list
    elif cond not in tokens[3]:
        errors.append(f'O | token "{cond}" is unknown')
    else:
        # Final check if at top-level with no errors but no token match
        if is_first is True:
            return 'P | no matches with any token' if len(errors) == 0 else '\n'.join(errors)
        return


def eval_condition(user: tuple, cond: str) -> bool:
    """
      Evaluates a complex boolean condition string against a user's information.

      The condition string supports logical operators ('|' for OR, '&' for AND)
      and specific checks for the presence or absence of metadata keys.
      It can also compare user's data fields against specified values using
      comparison operators (implicitly derived from `tokens[2]`).

      Condition types:
          - `A | B`: True if condition A OR condition B is true.
          - `A & B`: True if condition A AND condition B is true.
          - `key->`: True if 'key' exists in user's metadata (`user[5]`).
          - `key!>`: True if 'key' does NOT exist in user's metadata (`user[5]`).
          - `field_name.sub_field_name[comparison_op] value`: Compares a user's data field
            (e.g., 'met.event.property == "value"') after type conversion.

      Args:
          user (tuple): A tuple representing the user's information, typically
                        parsed from `User.info2text` format.
                        Expected structure: `user[5]` contains metadata keys.
          cond (str): The condition string to evaluate.

      Returns:
          bool: True if the condition evaluates to true for the given user, False otherwise.
      """
    if '|' in cond:
        return any(eval_condition(user, i) for i in cond.split('|'))
    if '&' in cond:
        return all(eval_condition(user, i) for i in cond.split('&'))
    if '->' in cond:
        # Return True if the key (before '->') exists in user[5] (metadata dictionary)
        c = cond.split('->')
        return c[0] in user[5].keys()
    if '!>' in cond:
        # Return True if the key (before '!>') does NOT exist in user[5]
        c = cond.split('!>')
        return c[0] not in user[5].keys()
    # Check if one of the comparison tokens (e.g. '==', '!=', '>>', etc.) is in the condition string
    for n, token in enumerate(tokens[2]):
        if token in cond:
            c = cond.split(token)  # Split condition on the comparison operator
            i = c[0].split('.')  # Extract possible nested keys
            # Find index of the main field in tokens[3] to get user's corresponding value and formatter
            index = tokens[3].index(i[0])
            v = user[index]
            f = User.text2info[index]
            if i[0] == 'met':
                # For 'met' fields (nested metadata), verify keys existence stepwise
                if i[1] not in v.keys():
                    return False
                if i[2] not in v[i[1]].keys():
                    return False
                v = v[i[1]][i[2]]
                f = f[i[1]][i[2]]
            # Define tuple of predicate functions corresponding to tokens[2] order
            predicate = (v.__eq__, v.__ne__, v.__gt__, v.__ge__, v.__lt__, v.__le__)
            return predicate[n](f(c[1]))
    # If condition could not be parsed or matched, return False by default
    return False


def flat_info(info: User.info2text) -> dict[str]:
    """
    Flattens a structured user info object into a single-level dictionary for easier access.

    This function processes specific fields from the `info` object and its nested 'metadata' dictionary.
    It extracts direct info fields and transforms metadata event data into
    flat keys (e.g., 'met_a24_rr1').

    Args:
        info (User.info2text): The structured user information object.
                               Expected structure: tuple/list where index 3 contains
                               direct info fields and index 5 contains metadata events.

    Returns:
        dict[str]: A dictionary where keys are flattened string representations
                   of user info fields and their corresponding values.
    """
    result = {}
    for n, key in enumerate(tokens[3][:-1]):
        result[key] = info[n]
    for n, event in enumerate(tokens[4]):
        if event not in info[5].keys():
            continue
        elif event == 'a24':
            result['met_a24_h10'] = info[5][event]['lr1'] is True
        elif event == 's25':
            result['met_s25_h10'] = info[5][event]['rr1'] != 0
        for key in tokens[5][n]:
            result[f'met_{event}_{key}'] = info[5][event][key]
    return result


def format_message(msg: str, user: User.info2text, **additional) -> str:
    """
    Formats a message by replacing placeholders with user info values processed by
    a dict mapping field names to formatting functions applied to user info before formatting.

    Args:
        msg (str): Message template with placeholders.
        user (User.info2text): User info object.
        **additional: Extra values for formatting.

    Returns:
        str: Formatted message string.
    """
    return msg.format(**{key: User.flat_i2t[key](value) for key, value in flat_info(user.info).items()}, **additional)


def sender(self, condition: str, msg: str) -> list[dict]:
    """
     Sends a formatted message to all users matching a specified condition.

     Parameters:
         condition (str): The condition string to evaluate for each user (must be valid for eval_condition).
         msg (str): The message template to format and send.

     Returns:
         list[dict]: A list of dictionaries for each recipient, each containing:
             - 'peer_id': the user ID to send the message to,
             - 'message': the formatted message string.
         If the condition check fails, returns a list of error messages for all admins.
     """
    check = check_condition(condition)
    if check_condition(condition) != 'ok':
        return [{'peer_id': uid, 'message': 'Condition issue:\n' + check} for uid in admin]
    users: UserList = self.users
    result = []
    for isu in users.keys():
        user = users.get(isu)
        if not user:
            continue
        uid = int(user.uid)
        # skip invalid/system uids (legacy semantics)
        if 0 <= uid <= 1:
            continue
        if eval_condition(user.info, condition) is True:
            result.append({'peer_id': uid, 'message': format_message(msg, user)})
    return result


def process_message_event(self, event, vk_helper) -> list[dict] | None:
    """
    NOTE: This function is currently not used.

    Processes a new message_event (callback button) from a user.
    """
    pl = event.object.get('payload')
    tts = ''
    sender = int(pl['sender'])
    if not pl:
        return
    return [{
        'peer_id': sender,
        'message': tts,
    }]


def process_message_new(self, event, vk_helper, ignored) -> list[dict] | None:
    """
    Handles a new incoming message from a user.

    Depending on the message type (private or chat), user ID, and message content, performs different actions:
        - Private messages:
            - Admin commands such as 'stop', 'reload', 'sender', and 'add_users'.
            - Support request handling with an ignore list mechanism.
            - Checks if the user is a member of the group.
            - Formats and sends messages based on user-specific metadata.

        - Chat messages:
            - Currently no implemented logic (reserved for future features).

    Args:
        event: The event object containing message information.
        vk_helper: Helper object for VK API interactions.
        ignored: Object managing the list of ignored users.

    Returns:
        list[dict] | None:
           A list of dictionaries with parameters for sending messages
           (including 'peer_id', 'message', and optionally 'keyboard' and 'attachment'),
           or None if no reply is needed.

    Notes:
        - The 'stop' command terminates the script.
        - The 'reload' command reloads the user list.
        - The 'sender' command dispatches messages to groups of users.
        - The 'add_users' command adds dummy users to the database.
    """
    users: UserList = self.users
    uid = event.message.from_id

    # Retrieve user's first and last name from VK API for personalized responses
    user_get = vk_helper.vk.users.get(user_ids=uid)
    user_get = user_get[0]  # The API returns a list, even for a single user_id
    uname = user_get['first_name']
    username = user_get['last_name']

    msg: str = event.message.text
    msgs = msg.split()  # Split message into words for command parsing
    if not msg:
        # If the message text is empty, no further processing needed for this path.
        # Consider if other logic (e.g., handling attachments) is required here.
        return

    # --- PRIVATE MESSAGES HANDLER ---
    # This block handles messages sent directly to the bot, not in group chats.
    if not event.from_chat:
        # ADMIN COMMANDS
        if uid in admin:
            if msgs[0] == 'stop':  # Shuts down the bot process (typically leads to container restart)
                exit()
            elif msgs[0] == 'reload':  # Forces a reload of the user list from storage
                return [{'peer_id': uid, 'message': 'Success' if self.users.load() else 'Failed'}]
            elif msgs[0] == 'sender':  # Dispatches a custom message to a group of users based on a condition
                # Refresh DB-backed user cache (uid_to_isu) before sending
                try:
                    self.users.load()
                except Exception:
                    pass
                if len(msgs) > 2:  # Extracts the condition and the message text for the sender function
                    result = sender(self, msgs[1], msg.removeprefix(msgs[0]).strip().removeprefix(msgs[1]).strip())
                    count = self.handle_actions(result)  # Executes the sending actions
                    tts = f'Готово. Всего разослано {count} сообщений'
                elif len(msgs) == 2:
                    tts = 'Нет сообщения'
                else:
                    tts = 'Нет аргумента'
                return [{
                    'peer_id': uid,
                    'message': tts
                }]
            elif msgs[0] == 'add_users':  # Adds specified user IDs as 'dummy' users to the database
                errors = dict[str: str]()
                for i in set(msgs[1:]):
                    try:
                        if int(i) in users.uid_to_isu.keys():
                            raise Exception(f'User {i} is already in database')
                        users.add((-1, int(i), '', '', '', {}))  # Add user with default empty metadata
                    except Exception as e:
                        errors[i] = str(e)
                if errors:  # Formats error messages for the admin
                    tts = '\n'.join(f'Ошибка при добавлении "{key}":\n{errors[key]}\n' for key in errors.keys())
                else:
                    tts = 'Успешный успех!'

                # Save changes to the user list only if any users were successfully added
                if len(set(msgs)) - len(errors.keys()) - 1 != 0:
                    users.save()
                return [{
                    'peer_id': uid,
                    'message': f'{tts}\n{len(set(msgs)) - len(errors.keys()) - 1} пользователей были успешно добавлены!'
                }]

        # --- SUPPORT CONVERSATION HANDLING ---
        # Skips further processing if the user is currently ignored AND not attempting to call admin
        if ignored.is_ignored(uid) and 'админ' not in msg.lower():
            return

        # handling messages, that initiating or ending a support request
        if 'админ' in msg.lower():
            link = f'https://vk.com/gim{self.group_id}?sel={uid}'
            buttons = [{'label': 'прямая ссылка', 'payload': {'type': 'userlink'}, 'link': link}]
            link_keyboard = create_link_keyboard(buttons)
            # User was ignored, now wants to cancel the call to admin
            if ignored.is_ignored(uid):
                self.info(ignored.remove(uid))
                self.info(ignored.save_to_file())
                tts = 'Надеюсь, вопрос снят!'
                atts = f'{uname} {username} больше не вызывает!'
                buttons = [{'label': 'ПОЗВАТЬ АДМИНА', 'payload': {'type': 'callmanager'}, 'color': 'positive'}]
                keyboard = create_standard_keyboard(buttons)
            # User is calling for admin support
            else:
                self.info(ignored.add(uid))
                self.info(ignored.save_to_file())
                tts = 'Принято, сейчас позову! Напиши свою проблему следующим сообщением. ' \
                      'Когда вопрос будет решён, ещё раз напиши команду или нажми на кнопку.'
                atts = f'{uname} {username} вызывает!'
                buttons = [{'label': 'СПАСИБО АДМИН', 'payload': {'type': 'uncallmanager'}, 'color': 'negative'}]
                keyboard = create_standard_keyboard(buttons)
            # Return messages for both the user and all admins
            return [
                {
                    'peer_id': uid,
                    'message': tts,
                    'keyboard': keyboard,
                    'attachment': None
                },
                *[
                    {
                        'peer_id': uid,
                        'message': atts,
                        'keyboard': link_keyboard,
                        'attachment': None
                    } for uid in admin
                ]
            ]

        # --- DEFAULT MESSAGE RESPONSE LOGIC ---
        # Determines the bot's response based on user's group membership and metadata
        if vk_helper.vk_session.method('groups.isMember', {'group_id': self.group_id, 'user_id': uid}) == 0:
            tts = info_message  # User is not a member of our group
        elif uid in users.uid_to_isu:
            isu = users.uid_to_isu[uid]
            user = users.get(isu)
            # Check specific metadata keys to tailor the response
            if 'a25' in user.met.keys():
                tts = format_message(a25_message, user)
            elif 'y25' in user.met.keys() and user.met['y25']['ugo'] != 0:
                tts = format_message(y25_message, user,
                                     part2=(
                                         format_message(y25_second_part, user) if user.met['y25']['way'] == 2 else ''))
            elif 's25' in user.met.keys():
                tts = format_message(s25_message, user,
                                     part2=(format_message(s25_second_part, user) if user.met['s25']['wr1'] else ''),
                                     part3=(format_message(s25_third_part, user) if user.met['s25']['wr2'] else ''))
            elif 'a24' in user.met.keys():
                tts = format_message(a24_message, user,
                                     part2=format_message(a24_second_part, user) if user.met['a24']['wr1'] else '',
                                     part3=format_message(a24_third_part, user) if user.met['a24']['wr2'] else '')
            else:
                tts = info_message  # No specific metadata matched
        else:
            tts = info_message  # User not found in the database

    # --- CHAT MESSAGES HANDLER ---
    # This block is for messages received in group chats.
    else:
        is_ping = False
        msg = event.object['message']['text']
        if not msg:
            return
        msgs = msg.split()
        # if '@club230160029' in msgs[0]:
        #     is_ping = True
        #     msgs.pop(0)
        #     msg = msg[msg.index(']') + 2:]
        # elif '@club230160029' in msg:
        #     is_ping = True

        uid = event.object['message']['peer_id']
        cuid = event.object['message'].get('conversation_message_id')

        if msgs[0].lstrip('/') == 'ping':
            mc = MinecraftServerQuery()
            try:
                players, version = mc.get_dummy_info()
                if players:
                    player_list = '\n📶'.join([''] + players)
                    tts = f'❗ JouTak ☭ {version} ❗\n== Zadry 🤓 {len(players)}/375 =={player_list}'
                else:
                    tts = 'Все антизадры (╥﹏╥)'
            except Exception as e:
                tts = 'Server connection error: ' + str(e)
        else:
            return
        return [{'peer_id': uid, 'message': tts, 'conversation_message_id': cuid}]

    # Default return for processed private messages
    return [{
        'peer_id': uid,
        'message': tts
    }]
