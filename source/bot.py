# -*- coding: utf-8 -*-
import re
import json
import os.path
from datetime import datetime
from utils.VKHelper import *

spartakiada_subs_path = './subscribers/spartakiada{}.txt'
users_path = './subscribers/users.txt'

admin = [297002785, 275052029, 325899178, 229488682]

# DB: isu, uid, fio, grp, nck, {s24: {...}, s25: {...}, ...}

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
    f'Если есть вопросы, в том числе по спартакиаде, пиши "АДМИН"!'
)

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
'''.strip()

y25_second_part = '''

Номер машины:
{met_y25_car}
'''.rstrip()

s25_message = '''
Вот твои данные за Спартакиаду по Майнкрафту 2025!

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

s24_message = '''
Вот твои данные за Спартакиаду по Майнкрафту 2024!

Ник:
{met_s24_nck}

Участвуешь ли ты в первом этапе:
Да

Использовал ли ты все попытки:
{met_s24_lr1}

Проходишь ли в следующий этап:
{met_s24_wr1}

Поставят ли 10 баллов:
{met_s24_h10}

{part2}{part3}
Обязательно проверь все данные, только в случае несоответствий или важных вопросов напиши в ответ "АДМИН"
Читай о нас подробнее на сайте https://joutak.ru/minigames и других разделах
'''.strip()

s24_second_part = '''
Проходишь ли ты в финал:
{met_s24_wr2}

Ещё не отыграл в финале:
{met_s24_nyt}
'''

s24_third_part = '''
Победил ли в финале:
{met_s24_fnl}

'''.lstrip()


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


def flat_info2text() -> dict[str]:
    result = {key: value for key, value in zip(User.keys[:-1], User.info2text[:-1])}
    for n, key in enumerate(tokens[3][:-1]):
        result[key] = User.info2text[n]
    for n, event in enumerate(tokens[4]):
        for key in tokens[5][n]:
            result[f'met_{event}_{key}'] = User.info2text[5][event][key]
    result['met_s24_h10'] = User.b2t
    result['met_s25_h10'] = User.b2t
    return result


class User:
    # isu, uid, fio, grp, nck, met: {
    # s24: {tsp, nck, lr1, wr1, wr2, nyt, fnl},
    # s25: {tsp, nck, wr1, rr1, wr2, rr2, fnl},
    # y25: {tsp, nck, nmb, bed, way, car, liv, ugo}}
    info_type = tuple[int, int, str, str, str, dict[str: dict[str: str | int | bool]]]
    s2b = lambda s: s == '1'
    load2info = (int, int, str, str, str, json.loads)

    text2info = (int, int, str, str, str, {
        's24': {'tsp': int, 'nck': str, 'lr1': s2b, 'wr1': s2b, 'wr2': s2b, 'nyt': s2b, 'fnl': s2b},
        's25': {'tsp': int, 'nck': str, 'wr1': s2b, 'rr1': str, 'wr2': s2b, 'rr2': str, 'fnl': str},
        'y25': {'tsp': int, 'nck': str, 'nmb': str, 'bed': s2b, 'way': int, 'car': str, 'liv': str, 'ugo': int}})

    t2ic = str.isdigit  # text to integer check
    t2bc = ['0', '1'].__contains__  # text to bool check
    text2info_check = (t2ic, t2ic, bool, bool, bool, {
        's24': {'tsp': t2ic, 'nck': bool, 'lr1': t2bc, 'wr1': t2bc, 'wr2': t2bc, 'nyt': t2bc, 'fnl': t2bc},
        's25': {'tsp': t2ic, 'nck': bool, 'wr1': t2bc, 'rr1': t2ic, 'wr2': t2bc, 'rr2': t2ic, 'fnl': t2ic},
        'y25': {'tsp': t2ic, 'nck': bool, 'nmb': bool, 'bed': t2bc, 'way': t2ic, 'car': bool, 'liv': bool, 'ugo': t2ic}})

    b2t = lambda b: 'Да' if b else 'Нет'  # bool to text
    way2t = ('На бесплатном трансфере от ГК', 'Своим ходом (электричка)', 'Своим ходом (на машине)').__getitem__
    opt = lambda x: x or '[НЕТ ДАННЫХ]'
    ugo2t = ('Нет.', 'Да, ты прошёл отбор, ждём оплату!', 'Оплата дошла до нас, ты едешь!').__getitem__
    info2text = (str, str, str, str, str, {
        's24': {'tsp': ts2str, 'nck': opt, 'lr1': b2t, 'wr1': b2t, 'wr2': b2t, 'nyt': b2t, 'fnl': b2t},
        's25': {'tsp': ts2str, 'nck': opt, 'wr1': b2t, 'rr1': opt, 'wr2': b2t, 'rr2': opt, 'fnl': opt},
        'y25': {'tsp': ts2str, 'nck': opt, 'nmb': opt, 'bed': b2t, 'way': way2t, 'car': opt, 'liv': opt, 'ugo': ugo2t}})

    b2s = lambda b: '1' if b else '0'  # bool to string
    db2save = (str, str, str, str, str, lambda x: json.dumps(x, ensure_ascii=False))

    keys = ('isu', 'uid', 'fio', 'grp', 'nck', 'met')
    flat_i2t: dict[str]

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
        self.max_special_isu = 0
        self.used_specials_isus = set()
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

        def parse_line(n: int, s: tuple[str, ...]) -> tuple | None:
            nonlocal changes
            result = [0, 0, '', '', '', {}]
            if not s or len(s) != 6:
                warn(f'empty {n}-th line in DB')
            if not all(d.isdigit() for d in s[0]):
                warn(f'isu id is NaN in {n}-th line in DB: {s[0]}')
                incorrect_isus.append(s)
                changes = True
            else:
                result[0] = int(s[0])
            if not 100000 <= result[0] <= 999999:
                self.used_specials_isus.add(result[0])
            if not all(d.isdigit() for d in s[1]):
                warn(f'vk id is NaN (isu = {s[0]}) in {n}-th line in DB:', s[1])
                incorrect_uids.append(s)
                result[1] = -1
                changes = True
            else:
                result[1] = int(s[1])
            if 0 <= result[1] <= 1:
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
                warn(f'something wrong with meta info (isu = {s[0]}) in {n}-th line in DB:', s[5])
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
        for i in range(len(incorrect_isus)):
            corrected = list(incorrect_isus[i])
            corrected[0] = str(self.get_new_special_isu())
            incorrect_isus[i] = tuple(corrected)
        # достаём все vk_uid через vk_link
        for i in range(0, len(incorrect_uids), 25):
            part = [j[1] for j in incorrect_uids[i:i + 25]]
            links = []
            for uid in part:
                start = uid.rfind('/') + 1
                if start == -1:
                    start = uid.find('@') + 1
                if start == -1:
                    start = 0
                links.append(uid[start:])
            response: list[str] = self.vk_helper.links_to_uids(links)
            for j, uid in zip(range(i, i + 25), response):
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
            if not (0 <= user.uid <= 1):
                self.uid_to_isu[user.uid] = isu

        # TODO: REMOVE SOON
        for isu in self.db.keys():
            user = self.db[isu]
            if 'y25' in user.met.keys():
                y25 = user.met['y25']
                for key in ('sts', 'why', 'jtk', 'gms', 'lgc', 'wsh'):
                    if key in y25.keys():
                        changes = True
                        del y25[key]
        # ------------------

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
        to_save.sort(key=lambda x: int(x.split('\t')[0]) if x.split('\t')[0].isdigit() else -1)
        with open(users_path, 'w', encoding='UTF-8') as file:
            file.write('\n'.join(to_save))
        return True

    def get(self, isu: int) -> User | None:
        return self.db[isu] if isu in self.db.keys() else None

    def add(self, info: tuple[int, int, str, str, str, dict[str: dict[str: str | int | bool]]]) -> User:
        if info[0] == -1:
            info = tuple([self.get_new_special_isu()] + list(info[1:]))
        self.db[info[0]] = User(info)
        if not (0 <= info[1] <= 1):
            self.uid_to_isu[info[1]] = info[0]
        return self.db[info[0]]

    def get_new_special_isu(self) -> int:
        while self.max_special_isu in self.used_specials_isus:
            self.max_special_isu += 1
        self.used_specials_isus.add(self.max_special_isu)
        return self.max_special_isu

    def keys(self):
        return self.db.keys()


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
    result = {}
    for n, key in enumerate(tokens[3][:-1]):
        result[key] = info[n]
    for n, event in enumerate(tokens[4]):
        if event not in info[5].keys():
            continue
        elif event == 's24':
            result['met_s24_h10'] = info[5][event]['lr1'] is True
        elif event == 's25':
            result['met_s25_h10'] = info[5][event]['rr1'] != 0
        for key in tokens[5][n]:
            result[f'met_{event}_{key}'] = info[5][event][key]
    return result


def format_message(msg: str, user: User.info2text, **additional) -> str:
    # info = flat_info(user.info)
    # formating = {key: value for key, value in info.items()}
    # for key in formating:
    #     f = User.flat_i2t[key]
    #     print(formating[key])
    #     formating[key] = f(formating[key])
    # return msg.format(**formating, **additional)
    return msg.format(**{key: User.flat_i2t[key](value) for key, value in flat_info(user.info).items()}, **additional)


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
    users: UserList = self.users
    uid = event.message.from_id

    user_get = vk_helper.vk.users.get(user_ids=uid)
    user_get = user_get[0]
    uname = user_get['first_name']
    username = user_get['last_name']

    msg: str = event.message.text

    if not msg:
        return  # do some other logic if needed

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
        elif msgs[0] == 'add_users':
            errors = dict[str: str]()
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

    if event.from_chat:
        return

    if ignored.is_ignored(uid) and 'админ' not in msg.lower():
        return
    if 'админ' in msg.lower():
        link = f'https://vk.com/gim{self.group_id}?sel={uid}'
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

    if vk_helper.vk_session.method('groups.isMember', {'group_id': self.group_id, 'user_id': uid}) == 0:
        tts = info_message
    elif uid in users.uid_to_isu:
        isu = users.uid_to_isu[uid]
        user = users.get(isu)
        if 'y25' in user.met.keys() and user.met['y25']['ugo'] != 0:
            tts = format_message(y25_message, user,
                                 part2=(format_message(y25_second_part, user) if user.met['y25']['way'] == 2 else ''))
        elif 's25' in user.met.keys():
            tts = format_message(s25_message, user,
                                 part2=(format_message(s25_second_part, user) if user.met['s25']['wr1'] else ''),
                                 part3=(format_message(s25_third_part, user) if user.met['s25']['wr2'] else ''))
        elif 's24' in user.met.keys():
            tts = format_message(s24_message, user,
                                 part2=format_message(s24_second_part, user) if user.met['s24']['wr1'] else '',
                                 part3=format_message(s24_third_part, user) if user.met['s24']['wr2'] else '')
        else:
            tts = info_message
    else:
        tts = info_message
    return [{
        'peer_id': uid,
        'message': tts
    }]
