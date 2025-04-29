# -*- coding: utf-8 -*-
import os.path
from datetime import datetime
from utils.VKHelper import *

spartakiada_subs_path = './subscribers/spartakiada{}.txt'
users_path = './subscribers/users.txt'

admin = [297002785, 275052029, 325899178, 229488682]

# DB: isu, uid, fio, grp, nck, {s24: {...}, s25: {...}, ...}

groupid = 217494619  # 230160029
joutek_ip = 'craft.joutak.ru'
joutek_link = 'https://joutak.ru'
form_link = 'https://forms.yandex.ru/u/6501f64f43f74f18a8da28de/'
telegram_link = 't.me/itmocraft'
discord_link = 'https://discord.gg/YVj5tckahA'
vk_link = 'https://vk.com/widget_community.php?act=a_subscribe_box&oid=-217494619&state=1|ITMOcraft'

# format message with countd
hi_message = \
    'Привет! На прошлых выходных ты участвовал в спартакиаде, ' \
    'проведённой клубом любителей игры «Майнкрафт» ITMOcraft. Думаю, самое время познакомиться!\n\n' \
    'Наш клуб — комьюнити итмошников, которым нравится играть в майнкрафт. ' \
    'Выживание, моды, мини-игры: если во что-то можно играть, мы создаём для этого условия. ' \
    'Наша альма-матер — SMP JouTak. ' \
    'Это сервер с шестилетней историей (без вайпов, без приватов, без случайных людей), ' \
    'в итмошном районе которого мы вместе уже построили Кронву, Вязьму и даже Ленсовета, ' \
    'а игроки возводят свои проекты, болтают в войсике и просто отдыхают. ' \
    'Более того, мы регулярно проводим там ивенты, самое время залететь на сервер👻\n' \
    'Точно! Тебе же ещё положены бонусы за участие в спартакиаде: {} дней проходки. ' \
    '(+30дней, если у тебя лицензия)\n\n' \
    'Как это сделать?\n' \
    f'1) Подключайся в дискорд: {discord_link}\n' \
    f'2) Заполняй анкету, чтобы мы с тобой связались: {form_link}\n' \
    f'3) Следи за новостями в телеграм канале: {telegram_link}! ' \
    'Помогая нашему продвижению, ты делаешь наши ивенты масштабнее, а сервера круче!\n' \
    'P.S.: Плашку в ису "Член клуба ITMOcraft" тоже можно получить после заполнения этой анкеты, ' \
    'по желанию. Если есть вопросы, пиши!'

info_message = \
    'Привет! Для получения информации о серверах ИТМОкрафта подпишитесь:\n' \
    f'[{vk_link}. Подписаться]\n\n' \
    'После подписки отправь ещё одно сообщение. Только в случае возникновения проблем пиши "АДМИН"'

welcome_message = '''
Добро пожаловать на спартакиаду ИТМО по майнкрафту! Записывай данные для входа на сервер:
IP: craft.itmo.ru

ИСУ:
{}

Ник:
{}

Участвуешь ли ты в первом этапе (BlockParty):
Да

Проходишь ли в следующий этап (AceRace):
{}

Поставят ли 10 баллов:
{}

Рекорд раундов в BlockParty:
{}
{}{}
Обязательно проверь все данные, только в случае несоответствий или важных вопросов напиши в ответ "АДМИН"
Читай о нас подробнее на сайте https://joutak.ru/minigames и других разделах
'''.strip()

second_part = '''
Рекорд в AceRace:
{}

Проходишь ли ты в финал (SurvivalGames):
{}

'''

third_part = '''
Место в финале:
{}

'''.lstrip()


#    'Наш клуб — комьюнити итмошников, которым нравится играть в майнкрафт. ' \
#    'Выживание, моды, мини-игры: если во что-то можно играть, мы создаём для этого условия. ' \
#    'Недавно мы получили от университета ещё большие мощности, ' \
#    f'поэтому с этой спартакиады мини-игры будут играться на постоянной основе! IP: {joutek_ip}. ' \
#    'Наша альма-матер — SMP JouTak. Это сервер с шестилетней историей ' \
#    '(без вайпов, без приватов, без случайных людей), ' \
#    'в итмошном районе которого мы вместе уже построили Кронву, Вязьму и даже Ленсовета, ' \
#    'а игроки возводят свои проекты, болтают в войсчате и просто отдыхают. ' \
#    'Более того, мы регулярно проводим там ивенты, самое время залететь на сервер👻 ' \
#    '(+30дней, если у тебя лицензия)\n\n' \
#    'Как это сделать?\n' \
#    f'1) Почитай информацию о том, что мы делаем, на нашем сайте: {joutek_link}\n' \
#    f'2) Заполняй анкету, чтобы мы с тобой связались: {form_link}\n' \
#    f'3) Следи за новостями в нашем телеграм канале: {telegram_link}. ' \
#    'Помогая нашему продвижению, ты делаешь ивенты масштабнее, а сервера круче!\n' \
#    'P.S.: Плашку в ису "Член клуба ITMOcraft" тоже можно получить после заполнения этой анкеты, по желанию. ' \
#    'Если есть вопросы, пиши "АДМИН"!'


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


warnings = []


def warn(*s: str) -> None:
    # print('Warning:', *s)
    warnings.append('Warning: ' + ' '.join(s))


def str2ts(s: str) -> int:
    return int(datetime.strptime(s, '%m/%d/%Y %H:%M:%S').timestamp())


def ts2str(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).strftime('%m/%d/%Y %H:%M:%S')


class User:
    # isu, uid, fio, grp, nck, {s24: {...}, s25: {...}, ...}
    info_type = tuple[int, int, str, str, str, dict[str: dict[str: str | int | bool]]]
    s2b = lambda s: s == '1'
    load2info = (int, int, str, str, str, json.loads)

    text2info = (int, int, str, str, str,
                 {'s24': {'tsp': int, 'nck': str, 'lr1': s2b, 'wr1': s2b, 'wr2': s2b, 'nyt': s2b, 'fnl': s2b},
                  's25': {'tsp': int, 'nck': str, 'wr1': s2b, 'rr1': str, 'wr2': s2b, 'rr2': str, 'fnl': str}})

    s2ic = str.isdigit
    s2bc = ['0', '1'].__contains__
    text2info_check = (s2ic, s2ic, bool, bool, bool,
                       {'s24': {'tsp': s2ic, 'nck': bool, 'lr1': s2bc, 'wr1': s2bc, 'wr2': s2bc, 'nyt': s2bc,
                                'fnl': s2bc},
                        's25': {'tsp': s2ic, 'nck': bool, 'wr1': s2bc, 'rr1': bool, 'wr2': s2bc, 'rr2': bool,
                                'fnl': bool}})

    b2t = lambda b: 'Да' if b else 'Нет'
    info2text = (str, str, str, str, str,
                 {'s24': {'tsp': ts2str, 'nck': str, 'lr1': b2t, 'wr1': b2t, 'wr2': b2t, 'nyt': b2t, 'fnl': b2t},
                  's25': {'tsp': ts2str, 'nck': str, 'wr1': b2t, 'rr1': str, 'wr2': b2t, 'rr2': str, 'fnl': str}})

    b2s = lambda b: '1' if b else '0'
    db2save = (str, str, str, str, str, json.dumps)

    keys = ('isu', 'uid', 'fio', 'grp', 'nck', 'met')
    s24keys = ('tsp', 'nck', 'lr1', 'wr1', 'wr2', 'nyt', 'fnl')
    s25keys = ('tsp', 'nck', 'wr1', 'rr1', 'wr2', 'rr2', 'fnl')

    def __init__(self, info: tuple[int, int, str, str, str, dict[str: dict[str: str | int | bool]]]) -> None:
        self.info = info

    def __getitem__(self, key: str) -> int | str | dict | None:
        return self.info[User.keys.index(key)] if key in User.keys else None

    def __getattribute__(self, key: str) -> int | str | dict | None:
        return super().__getattribute__(key) if key == 'info' else \
            (self.info[User.keys.index(key)] if key in User.keys else None)


class UserList:
    def __init__(self, path: str, vk_helper) -> None:
        # DB: isu, uid, fio, grp, nck, {s24: {...}, s25: {...}, ...}
        self.db = dict[int: User]()
        self.uid_to_isu = dict[int: int]()  # uid: isu
        self.errors = list[tuple[str]]()
        self.path = path
        self.vk_helper = vk_helper
        if self.load() is False:
            raise OSError('Something went wrong while loading DB')

    # Обрабатывает базу данных, заодно проверяя её правильность. Если что-то не так, то исправляет
    def load(self) -> bool:
        if is_file_accessible(self.path) is False:
            return False
        self.db.clear()

        changes = False
        incorrect_uids = list[tuple[str]]()
        incorrect_isus = list[tuple[str]]()
        used_specials_isus = set()

        def parse_line(n: int, s: tuple[str, ...]) -> tuple | None:
            nonlocal changes
            result = [0, 0, '', '', '', {}]
            if not s or len(s) != 6:
                warn(f'empty {n}-th line in DB')
            if not all(d.isdigit() for d in s[0]):
                warn(f'isu id is NaN in {n}-th line in DB: {s[0]}')
                incorrect_isus.append(line)
                changes = True
            else:
                result[0] = int(s[0])
            if not 100000 <= result[0] <= 999999:
                used_specials_isus.add(result[0])
            if not all(d.isdigit() for d in s[1]):
                warn(f'vk id is NaN (isu = {s[0]}) in {n}-th line in DB:', s[1])
                incorrect_uids.append(line)
                changes = True
            else:
                result[1] = int(s[1])
            if result[1] <= 1:
                self.errors.append(s)
                if s in incorrect_isus:
                    incorrect_isus.remove(s)
                if s in incorrect_uids:
                    incorrect_uids.remove(s)
                return None
            if len(s[2].split()) != 3:  # fio
                warn(f'something wrong with fio (isu = {s[0]}) in {n}-th line in DB:', s[2])
            result[2] = s[2]
            result[3] = s[3]
            result[4] = s[4]
            if is_json(s[5]) is False:
                warn(f'something wrong with meta  info (isu = {s[0]}) in {n}-th line in DB:', s[5])
                self.errors.append(s)
                if s in incorrect_isus:
                    incorrect_isus.remove(s)
                if s in incorrect_uids:
                    incorrect_uids.remove(s)
                return None
            else:
                result[5] = json.loads(s[5])
            return tuple(result)

        with open(self.path, 'r', encoding='UTF-8') as file:
            for n, line in enumerate(file):
                user_info = parse_line(n, line.strip().split('\t'))
                if user_info is not None:
                    self.db[user_info[0]] = User(user_info)
        # выдаём special isu для нетакусь:
        special_isu = 1
        for i in range(len(incorrect_isus)):
            while special_isu in used_specials_isus:
                special_isu += 1
            corrected = list(incorrect_isus[i])
            corrected[0] = str(special_isu)
            incorrect_isus[i] = tuple(corrected)
        # достаём все vk_uid через vk_link
        for i in range(0, len(incorrect_uids), 25):
            part = [incorrect_uids[j][1] for j in range(i, min(i + 25, len(incorrect_uids)))]
            links = []
            for isu, uid in part:
                start = uid.rfind('/') + 1
                if start == -1:
                    start = uid.find('@') + 1
                if start == -1:
                    start = 0
                links.append(uid[start:])
            response: list[str] = self.vk_helper.links_to_uids(links)
            for j, uid in zip(range(i, min(i + 25, len(incorrect_uids))), response):
                user = list(incorrect_uids[j])
                user[1] = str(uid)
                incorrect_uids[j] = tuple(user)
        # с ними уже ничего не поделать...
        for i in incorrect_uids:
            if i[1] == '0' or i[1] == '1':
                self.errors.append(i)
        incorrect_uids = [i for i in incorrect_uids if i[1] != '0' and i[1] != '1']
        # если isu и uid неправильны сразу
        for i in incorrect_isus:
            for j in incorrect_uids:
                if tuple(i[2:]) == tuple(j[2:]):
                    user_info = parse_line(0, (i[0], j[1], i[2], i[3], i[4], i[5]))
                    self.db[i[0]] = User(user_info)
        incorrect_isus = [i for i in incorrect_isus if not any(tuple(i[2:]) == tuple(j[2:]) for j in incorrect_uids)]
        incorrect_uids = [i for i in incorrect_uids if not any(tuple(i[2:]) == tuple(j[2:]) for j in incorrect_isus)]
        # остаток
        for s in incorrect_isus:
            user_info = parse_line(0, s)
            self.db[user_info[0]] = User(user_info)
        for s in incorrect_uids:
            user_info = parse_line(0, s)
            self.db[user_info[0]] = User(user_info)
        # делаем штуку для быстрого доступа к пользователю через uid
        for isu in self.db.keys():
            user = self.db[isu]
            if user.uid != 0:
                self.uid_to_isu[user.uid] = isu
        if changes is True:
            return self.save()
        return True

    def save(self) -> bool:
        if is_file_accessible(self.path) is False:
            return False
        to_save = []
        for isu in self.db.keys():
            to_save.append('\t'.join(f(i) for f, i in zip(User.db2save, self.db[isu].info)))
        to_save.extend(map('\t'.join, self.errors))
        to_save.sort()
        with open(users_path, 'w', encoding='UTF-8') as file:
            file.write('\n'.join(to_save))
        return True

    def get(self, isu: int) -> User | None:
        return self.db[isu] if isu in self.db.keys() else None

    def keys(self):
        return self.db.keys()


def init_spartakiada_subs(year: int) -> set[int]:
    # DB   | timestamp isu vk_uid  vk_link nick    group   fio first_time
    spartakiada_subs = set[int]()
    with open(spartakiada_subs_path.format(year), 'r', encoding='UTF-8') as file:
        for n, uid in enumerate(file):
            if not uid:
                continue
            if not all(d.isdigit() for d in uid.strip()):
                warn(f'something wrong with id in {n}-th line in spartakiada subs DB')
                continue
            spartakiada_subs.add(int(uid.strip()))
    if 0 in spartakiada_subs:
        spartakiada_subs.remove(0)
    if -1 in spartakiada_subs:
        spartakiada_subs.remove(-1)
    return spartakiada_subs


def save_spartakiada_subs(uids: set[int], year: int) -> bool:
    if is_file_accessible(spartakiada_subs_path.format(year)) is False:
        return False
    with open(spartakiada_subs_path.format(year), 'w', encoding='UTF-8') as file:
        file.writelines(map(str, sorted(uids)))
    return True


spartakiada24_subs = init_spartakiada_subs(24)
spartakiada25_subs = init_spartakiada_subs(25)

tokens = (
    ('|', '&'),
    ('->', '!>'),
    ('==', '!=', '>>', '>=', '<<', '<='),
    User.keys,
    ('s24', 's25'),
    (User.s24keys, User.s25keys),
    ('s24', 's25', 'adm')
)


def check_condition(cond: str, errors: list = None) -> str | None:
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
                if not check_condition(c[0], errors):
                    errors.append(f'C | token "{c[0]}" in "{cond}" is unknown')
                if c[1] not in tokens[4]:
                    errors.append(f'D | token "{c[1]}" in "{cond}" is unknown')
        if is_first is True:
            return 'ok' if len(errors) == 0 else '\n'.join(errors)
        return
    elif any(token in cond for token in tokens[2]):
        for token in tokens[2]:
            if token in cond:
                c = cond.split(token)
                if len(c) > 2:
                    errors.append('E | too many args in ' + cond)
                if len(c) < 2:
                    errors.append('F | not enough args in ' + cond)
                check_condition(c[0], errors)
                # if not UserList.db_t_check[tokens[3].index(c[0])](c[1]):
                #     errors.append(f'token "{c[1]}" in "{cond}" has wrong type')
        if is_first is True:
            return 'ok' if len(errors) == 0 else '\n'.join(errors)
        return
    elif '.' in cond:
        c = cond.split('.')
        if c[0] == 'met':
            if len(c) == 2:
                errors.append(f'H | token "{c[1]}" in "{cond}" is unknown')
            elif len(c) == 3:
                if c[1] not in tokens[4]:
                    errors.append(f'I | token "{c[1]}" in "{cond}" is unknown')
                elif c[2] not in tokens[5][tokens[4].index(c[1])]:
                    errors.append(f'J | token "{c[2]}" in "{cond}" is unknown')
            else:
                errors.append('K | too many args in ' + cond)
        if is_first is True:
            return 'L | not enough conditions'
        return
    else:
        if is_first is True:
            return 'M | no matches with any token' if len(errors) == 0 else '\n'.join(errors)
        return


def eval_condition(user: tuple, cond: str) -> bool:
    if '|' in cond:
        return any(eval_condition(user, i) for i in cond.split('|'))
    if '&' in cond:
        return all(eval_condition(user, i) for i in cond.split('&'))
    if '->' in cond:
        c = cond.split('->')
        return user[tokens[3].index(c[0])] in [spartakiada24_subs, spartakiada25_subs, admin][tokens[4].index(c[1])]
    if '!>' in cond:
        c = cond.split('!>')
        return user[tokens[3].index(c[0])] not in [spartakiada24_subs, spartakiada25_subs, admin][tokens[4].index(c[1])]
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
            print((v, n, c[1], token))
            return predicate[n](f(c[1]))
    return False


def flat_info2text(d: dict) -> dict[str]:
    result = {key: value for key, value in zip(User.keys[:-1], User.info2text[:-1])}
    for key in d.keys():
        if isinstance(d[key], dict):
            temp = {'met_' + key + '_' + ikey: value for ikey, value in flat_info2text(d[key]).items()}
            for key in temp:
                result[key] = temp[key]
        else:
            result[key] = d[key]
    return result


def flat_info(info: User.info2text) -> dict[str]:
    result = {}
    for n, key in enumerate(tokens[3][:-1]):
        result[key] = info[n]
    for n, event in enumerate(tokens[4]):
        if event not in info[5].keys():
            continue
        for key in tokens[5][n]:
            result[f'met_{event}_{key}'] = info[5][event][key]
    return result


def format_message(msg: str, user: User.info2text) -> str:
    flat_fs = flat_info2text(User.info2text[5])
    flat_ui = flat_info(user.info)
    print(flat_fs.keys())
    print(flat_ui.keys())
    return msg.format(**{key: flat_fs[key](flat_ui[key]) for key in flat_ui.keys()})


def sender(self, condition: str, msg: str) -> list[dict]:
    check = check_condition(condition)
    if check_condition(condition) != 'ok':
        return [{'peer_id': uid, 'message': 'Condition issue:\n' + check} for uid in admin]
    users: UserList = self.users
    result = []
    for isu in users.keys():
        user = users.get(isu)
        uid = user.uid
        if uid == '0':
            continue
        if eval_condition(user.info, condition) is True:
            result.append({'peer_id': uid, 'message': format_message(msg, user)})
            print(msg)
    return result


# Чёт с кнопкой связано
def process_message_event(self, event, vk_helper) -> list[dict] | None:
    pl = event.object.get('payload')
    # user_list = UserList() # TODO: userlist
    tts = ''
    sender = int(pl['sender'])
    if not pl:
        return
    return [{
        'peer_id': sender,
        'message': tts,
    }]


# Чёт без кнопки
def process_message_new(self, event, vk_helper, ignored) -> list[dict] | None:
    users = self.users
    uid = event.message.from_id

    user_get = vk_helper.vk.users.get(user_ids=uid)
    user_get = user_get[0]
    uname = user_get['first_name']
    username = user_get['last_name']

    msg: str = event.message.text
    msgs = msg.split()
    if uid in admin:
        if msgs[0] == 'stop':
            exit()
        elif msgs[0] == 'reload':
            return [{'peer_id': uid, 'message': 'Success' if self.users.load() else 'Failed'}]
        elif msgs[0] == 'sender':
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

    if event.from_chat:
        return

    if ignored.is_ignored(uid) and 'админ' not in msg.lower():
        return
    if 'админ' in msg.lower():
        link = f'https://vk.com/gim{groupid}?sel={uid}'
        buttons = [{'label': 'прямая ссылка', 'payload': {'type': 'userlink'}, 'link': link}]
        link_keyboard = create_link_keyboard(buttons)
        if ignored.is_ignored(uid):
            ignored.remove(uid)
            ignored.save_to_file()
            tts = 'Надеюсь, вопрос снят!'
            atts = f'{uname} {username} больше не вызывает!'
            buttons = [{'label': 'ПОЗВАТЬ АДМИНА', 'payload': {'type': 'callmanager'}, 'color': 'positive'}]
            keyboard = create_standart_keyboard(buttons)
        else:
            ignored.add(uid)
            ignored.save_to_file()
            tts = 'Принято, сейчас позову! Напиши свою проблему следующим сообщением. ' \
                  'Когда вопрос будет решён, ещё раз напиши команду или нажми на кнопку.'
            atts = f'{uname} {username} вызывает!'
            buttons = [{'label': 'СПАСИБО АДМИН', 'payload': {'type': 'uncallmanager'}, 'color': 'negative'}]
            keyboard = create_standart_keyboard(buttons)
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

    if vk_helper.vk_session.method('groups.isMember', {'group_id': groupid, 'user_id': uid}) == 0:
        tts = info_message
    else:
        return []
    return [{
        'peer_id': uid,
        'message': tts
    }]
