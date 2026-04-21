# -*- coding: utf-8 -*-
import json
import os
import time
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

admin = [297002785, 325899178, 229488682, 304032635]

itmocraft_ip = 'craft.itmo.ru'
joutak_ip = 'mc.joutak.ru'
joutak_link = 'https://joutak.ru'
form_link = 'https://forms.yandex.ru/u/6501f64f43f74f18a8da28de/'
a25_reg_link = 'https://itmo.events/events/116180'
telegram_link = 't.me/itmocraft'
discord_link = 'https://discord.gg/YVj5tckahA'
vk_link = 'https://vk.com/widget_community.php?act=a_subscribe_box&oid=-217494619&state=1|ITMOcraft'

# --- ВАЖНО: как раньше — сообщение для неподписанных ---
info_message = \
    'Привет! Для получения информации о серверах ИТМОкрафта подпишитесь:\n' \
    f'[{vk_link}. Подписаться]\n\n' \
    'После подписки отправь ещё одно сообщение. Только в случае возникновения проблем пиши "АДМИН"'

# --- Это было старым hi_message (у тебя сейчас называлось info_message) ---
hi_message = (
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
    f'{a25_reg_link}'
)

a25_welcome_message = (
    "Привет! \n\n"
    "Сейчас идёт третий сезон Майнокиады по Майнкрафту!\n"
    "Хочешь участвовать — зарегистрируйся по ссылке:\n"
    f"{a25_reg_link}\n\n"
    "После регистрации бот покажет твою команду и данные.\n"
    "Если ты уже зарегистрировался, но бот ничего не показывает — подожди, в нескольких рабочих часов информация точно должна появиться. "
    "Если она не появилась, напиши в ответ: АДМИН"
)

a25_message = '''
Вот твои данные за третий сезон Майнокиады ITMOcraft!

ИСУ:
{isu}

Ник:
{met_a25_nck}

Команда:
{met_a25_cmd}

Капитан:
{met_a25_cap}
{a25_stage_info}
Часы халявы на киберарене: {met_a25_kbr}
Подробнее про компьютерный клуб KRONBARS ARENA, где ты можешь бесплатно поиграть до конца турнира: https://vk.ru/wall-217494619_158

Обязательно проверь все данные, только в случае несоответствий или важных вопросов напиши в ответ "АДМИН"
Присоединяйся и следи за информацией в чате https://t.me/itmocraftchat!

P.S. Сообщение будет дополняться твоими данными по мере участия в играх
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

# --- A25: призыв капитанов поиграть ---
CAPTAIN_CALL_LABEL = 'ПРИЗВАТЬ ПОИГРАТЬ'
CAPTAIN_CALL_COOLDOWN_SECONDS = 120
CAPTAIN_CALL_COOLDOWN_UNTIL: dict[int, float] = {}





def _run_migration_bridge(db_url: str | None = None, users_txt: str | None = None):
    try:
        from source.utils.tools.cli.migrate_from_txt import run_migration
    except ModuleNotFoundError:
        from utils.tools.cli.migrate_from_txt import run_migration
    return run_migration(db_url=db_url, users_txt=users_txt)


def is_migration_enabled() -> bool:
    value = (os.getenv('ENABLE_MIGRATION') or '').strip().lower()
    return value in ('1', 'true', 'yes', 'on')


def is_a25_captain(user: User, uid: int) -> bool:
    # Captain for A25 is detected by comparing stored captain uid (met['a25']['cid']) with the sender uid.
    try:
        a25 = user.met.get('a25') if isinstance(user.met, dict) else None
        if not isinstance(a25, dict):
            return False
        cid = a25.get('cid', 0)
        return int(cid) != 0 and int(cid) == int(uid)
    except Exception:
        return False



def build_a25_stage_info(user: User) -> str:
    """Returns a formatted stage line for A25 participants who passed round 1.

    If round1 is not passed -> empty string.
    If round1 is passed but stage is empty -> shows '[НЕ НАЗНАЧЕН]'.
    """
    try:
        if user is None or not isinstance(user.met, dict):
            return ''
        a25 = user.met.get('a25')
        if not isinstance(a25, dict):
            return ''
        # Show stage info only for those who passed round 1
        if not bool(a25.get('wr1')):
            return ''
        stg = (a25.get('stg') or '').strip()
        if not stg or stg == '-':
            stg = '[НЕ НАЗНАЧЕН]'
        return f"\nТвой турнирный матч (stage): {stg}\n"
    except Exception:
        return ''



def get_a25_captain_uids(users: UserList) -> set[int]:
    # Collects all unique captain VK uids from A25 metadata.
    result: set[int] = set()
    for isu in users.keys():
        u = users.get(isu)
        if not u or not isinstance(u.met, dict):
            continue
        a25 = u.met.get('a25')
        if not isinstance(a25, dict):
            continue
        cid = a25.get('cid', 0)
        try:
            cid_int = int(cid)
        except Exception:
            cid_int = 0
        if cid_int > 0:
            result.add(cid_int)
    return result



def get_a25_current_stage(a25: dict) -> int | None:
    # Returns 1..3 for first not-completed stage, or None if all stages are completed.
    try:
        if not a25.get('wr1', False):
            return 1
        if not a25.get('wr2', False):
            return 2
        if not a25.get('wr3', False):
            return 3
        return None
    except Exception:
        return 1



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

    if any(token in cond for token in tokens[0]):
        for token in tokens[0]:
            if token in cond:
                for c in cond.split(token):
                    check_condition(c, errors)
        if is_first is True:
            return 'ok' if len(errors) == 0 else '\n'.join(errors)
        return

    elif any(token in cond for token in tokens[1]):
        for token in tokens[1]:
            if token in cond:
                c = cond.split(token)
                if len(c) > 2:
                    errors.append(f'A | too many args in "{cond}"')
                if len(c) < 2:
                    errors.append(f'B | not enough args in "{cond}"')
                if c[0] not in tokens[4]:
                    check_condition(c[0], errors)
                if c[1] != 'met':
                    errors.append(f'C | token "{c[1]}" in "{cond}" is unknown')
        if is_first is True:
            return 'ok' if len(errors) == 0 else '\n'.join(errors)
        return

    elif any(token in cond for token in tokens[2]):
        for token in tokens[2]:
            if token in cond:
                c = cond.split(token)
                if len(c) > 2:
                    errors.append('D | too many args in ' + cond)
                if len(c) < 2:
                    errors.append('E | not enough args in ' + cond)
                check_condition(c[0], errors)
                t = c[0].split('.')
                if t[0] not in tokens[3]:
                    errors.append(f'F | token "{t[0]}" in "{cond}" is unknown')
                if len(t) == 1 and c[0] in tokens[2] and not User.text2info_check[tokens[2].index(c[0])](c[1]):
                    errors.append(f'G | token "{c[1]}" in "{cond}" has wrong type')
                elif len(t) == 3 and t[0] == 'met' and t[1] in tokens[4] and t[2] in tokens[5][tokens[4].index(t[1])]:
                    if not User.text2info_check[5][t[1]][t[2]](c[1]):
                        errors.append(f'H | token "{c[1]}" in "{cond}" has wrong type')
        if is_first is True:
            return 'ok' if len(errors) == 0 else '\n'.join(errors)
        return

    elif '.' in cond:
        c = cond.split('.')
        if c[0] == 'met':
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

    elif cond not in tokens[3]:
        errors.append(f'O | token "{cond}" is unknown')
    else:
        if is_first is True:
            return 'P | no matches with any token' if len(errors) == 0 else '\n'.join(errors)
        return


def eval_condition(user: tuple, cond: str) -> bool:
    """
      Evaluates a complex boolean condition string against a user's information.
      """
    if '|' in cond:
        return any(eval_condition(user, i) for i in cond.split('|'))
    if '&' in cond:
        return all(eval_condition(user, i) for i in cond.split('&'))
    if '->' in cond:
        c = cond.split('->')
        return c[0] in user[5].keys()
    if '!>' in cond:
        c = cond.split('!>')
        return c[0] not in user[5].keys()
    for n, token in enumerate(tokens[2]):
        if token in cond:
            c = cond.split(token)
            i = c[0].split('.')
            index = tokens[3].index(i[0])
            v = user[index]
            f = User.text2info[index]
            if i[0] == 'met':
                if i[1] not in v.keys():
                    return False
                if i[2] not in v[i[1]].keys():
                    return False
                v = v[i[1]][i[2]]
                f = f[i[1]][i[2]]
            predicate = (v.__eq__, v.__ne__, v.__gt__, v.__ge__, v.__lt__, v.__le__)
            return predicate[n](f(c[1]))
    return False


def flat_info(info: User.info2text) -> dict[str]:
    """
    Flattens a structured user info object into a single-level dictionary for easier access.
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
            if key not in info[5][event]:
                continue
            result[f'met_{event}_{key}'] = info[5][event][key]
    return result


def format_message(msg: str, user: User.info2text, **additional) -> str:
    """
    Formats a message by replacing placeholders with user info values.
    """
    flat = flat_info(user.info)
    mapping: dict[str, str] = {}
    for key, value in flat.items():
        fmt = User.flat_i2t.get(key)
        if fmt is None:
            mapping[key] = str(value)
        else:
            mapping[key] = fmt(value)

    class _SafeDict(dict):
        def __missing__(self, k):
            return ""

    return msg.format_map(_SafeDict(mapping | additional))


def sender(self, condition: str, msg: str) -> list[dict]:
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
        if 0 <= uid <= 1:
            continue
        if eval_condition(user.info, condition) is True:
            result.append({'peer_id': uid, 'message': format_message(msg, user)})
    return result


def process_message_event(self, event, vk_helper) -> list[dict] | None:
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
    users: UserList = self.users
    uid = event.message.from_id

    user_get = vk_helper.vk.users.get(user_ids=uid)
    user_get = user_get[0]
    uname = user_get['first_name']
    username = user_get['last_name']

    msg: str = event.message.text
    msg = (event.object['message'].get('text') or '')
    msgs = msg.split()

    payload_raw = event.object['message'].get('payload')
    payload_type = None
    if payload_raw:
        try:
            payload_obj = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
        except Exception:
            payload_obj = None
        if isinstance(payload_obj, dict):
            payload_type = payload_obj.get('type')

    callplay_trigger = (payload_type == 'callplay') or ('призвать поиграть' in msg.lower())

    if not event.from_chat:
        if uid in admin and msgs:
            if msgs[0] == 'stop':
                exit()
            elif msgs[0] == 'reload':
                return [{'peer_id': uid, 'message': 'Success' if self.users.load() else 'Failed'}]
            elif msgs[0] == 'migrate':
                if not is_migration_enabled():
                    return [{
                        'peer_id': uid,
                        'message': 'Миграция отключена. Установи ENABLE_MIGRATION=1 и перезапусти бота.'
                    }]
                users_txt = msg.removeprefix(msgs[0]).strip() or None
                try:
                    stats = _run_migration_bridge(users_txt=users_txt)
                    try:
                        self.users.load()
                    except Exception:
                        pass
                    return [{
                        'peer_id': uid,
                        'message': (
                            'Миграция завершена.\n'
                            f'Файл: {stats["users_txt"]}\n'
                            f'Импортировано: {stats["imported"]}\n'
                            f'Валидных строк в файле: {stats["file_valid"]}\n'
                            f'Строк в DB users: {stats["db_rows"]}'
                        )
                    }]
                except Exception as e:
                    return [{'peer_id': uid, 'message': f'Ошибка миграции:\n{e}'}]
            elif msgs[0] == 'sender':
                try:
                    self.users.load()
                except Exception:
                    pass
                if len(msgs) > 2:
                    result = sender(self, msgs[1], msg.removeprefix(msgs[0]).strip().removeprefix(msgs[1]).strip())
                    count = self.handle_actions(result)
                    tts = f'Готово. Всего разослано {count} сообщений'
                elif len(msgs) == 2:
                    tts = 'Нет сообщения'
                else:
                    tts = 'Нет аргумента'
                return [{
                    'peer_id': uid,
                    'message': tts
                }]
            elif msgs[0] == 'add_users':
                errors = dict[str, str]()
                for i in set(msgs[1:]):
                    try:
                        if int(i) in users.uid_to_isu.keys():
                            raise Exception(f'User {i} is already in database')
                        users.add((-1, int(i), '', '', '', {}))
                    except Exception as e:
                        errors[i] = str(e)
                if errors:
                    tts = '\n'.join(f'Ошибка при добавлении "{key}":\n{errors[key]}\n' for key in errors.keys())
                else:
                    tts = 'Успешный успех!'

                if len(set(msgs)) - len(errors.keys()) - 1 != 0:
                    users.save()
                return [{
                    'peer_id': uid,
                    'message': f'{tts}\n{len(set(msgs)) - len(errors.keys()) - 1} пользователей были успешно добавлены!'
                }]

        if ignored.is_ignored(uid) and 'админ' not in msg.lower() and not callplay_trigger:
            return

        if 'админ' in msg.lower():
            link = f'https://vk.com/gim{self.group_id}?sel={uid}'
            buttons = [{'label': 'прямая ссылка', 'payload': {'type': 'userlink'}, 'link': link}]
            link_keyboard = create_link_keyboard(buttons)
            if ignored.is_ignored(uid):
                self.info(ignored.remove(uid))
                self.info(ignored.save_to_file())
                tts = 'Надеюсь, вопрос снят!'
                atts = f'{uname} {username} больше не вызывает!'
                buttons = [{'label': 'ПОЗВАТЬ АДМИНА', 'payload': {'type': 'callmanager'}, 'color': 'positive'}]
                keyboard = create_standard_keyboard(buttons)
            else:
                self.info(ignored.add(uid))
                self.info(ignored.save_to_file())
                tts = 'Принято, сейчас позову! Напиши свою проблему следующим сообщением. ' \
                      'Когда вопрос будет решён, ещё раз напиши команду или нажми на кнопку.'
                atts = f'{uname} {username} вызывает!'
                buttons = [{'label': 'СПАСИБО АДМИН', 'payload': {'type': 'uncallmanager'}, 'color': 'negative'}]
                keyboard = create_standard_keyboard(buttons)
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

        user = None
        if uid in users.uid_to_isu:
            isu = users.uid_to_isu[uid]
            user = users.get(isu)

        if callplay_trigger:
            if user is None or not isinstance(user.met, dict) or 'a25' not in user.met:
                return [{'peer_id': uid, 'message': 'Эта команда доступна только капитанам команд Майнокиады.'}]

            if not is_a25_captain(user, uid):
                return [{'peer_id': uid, 'message': 'Эта команда доступна только капитанам команд Майнокиады.'}]

            now = time.time()
            until = CAPTAIN_CALL_COOLDOWN_UNTIL.get(int(uid), 0)
            if until > now:
                remaining = int(until - now + 0.999)
                return [{'peer_id': uid, 'message': f'Слишком часто. Подожди {remaining} сек. и попробуй ещё раз.'}]

            a25 = user.met.get('a25') or {}
            team = (a25.get('cmd') or '').strip()
            if not team or team == '-':
                return [{'peer_id': uid, 'message': 'Не вижу название твоей команды в базе. Напиши: АДМИН'}]

            stage = get_a25_current_stage(a25)
            if stage is None:
                return [{'peer_id': uid, 'message': 'Похоже, у вашей команды уже отмечены все режимы. Если это ошибка — напиши: АДМИН'}]

            stage_text = {1: 'первый режим', 2: 'второй режим', 3: 'третий режим'}.get(stage, f'режим {stage}')

            notify_text = (
                f'Капитан команды "{team}" призывает поиграть!\n'
                f'Текущий режим: {stage_text}.\n'
                f'Нужны игроки от вашей команды.'
            )

            captains = sorted(get_a25_captain_uids(users))
            actions = [{'peer_id': int(c), 'message': notify_text} for c in captains if int(c) != int(uid)]

            CAPTAIN_CALL_COOLDOWN_UNTIL[int(uid)] = time.time() + CAPTAIN_CALL_COOLDOWN_SECONDS

            ack = {'peer_id': uid, 'message': f'Принято! Разослал другим капитанам ({len(actions)}).'}
            return [ack, *actions]

        is_member = vk_helper.vk_session.method(
            'groups.isMember',
            {'group_id': self.group_id, 'user_id': uid}
        ) != 0

        if 'user' not in locals() or user is None:
            user = None
            if uid in users.uid_to_isu:
                isu = users.uid_to_isu[uid]
                user = users.get(isu)

        keyboard_out = None
        if user is not None and 'a25' in user.met.keys():
            tts = format_message(a25_message, user, a25_stage_info=build_a25_stage_info(user))
            if is_a25_captain(user, uid):
                buttons = [{'label': CAPTAIN_CALL_LABEL, 'payload': {'type': 'callplay'}, 'color': 'positive'}]
                keyboard_out = create_standard_keyboard(buttons)
        elif not is_member:
            tts = info_message
        else:
            tts = a25_welcome_message

    else:
        is_ping = False
        msg = event.object['message']['text']
        if not msg:
            return
        msgs = msg.split()

        uid = event.object['message']['peer_id']
        cuid = event.object['message'].get('conversation_message_id')

        if msgs and msgs[0].lstrip('/') == 'ping':
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

    action = {
        'peer_id': uid,
        'message': tts
    }
    if 'keyboard_out' in locals() and keyboard_out is not None:
        action['keyboard'] = keyboard_out
    return [action]
