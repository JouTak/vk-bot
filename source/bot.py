# -*- coding: utf-8 -*-
import os.path
from datetime import datetime
from utils.VKHelper import *

spartakiada_subs_path = './subscribers/spartakiada{}.txt'
users_path = './users.txt'

admin = [297002785, 275052029, 325899178, 229488682]

TIMESTAMP = 0
VK_UID = TIMESTAMP + 1
NICKNAME = VK_UID + 1
GROUP_ID = NICKNAME + 1
FIO = GROUP_ID + 1
FIRST_TIME = FIO + 1

WIN_ROUND_1 = FIRST_TIME + 1
HAS_10_BALLS = WIN_ROUND_1 + 1
RECORD_ROUND_1 = HAS_10_BALLS + 1

WIN_ROUND_2 = RECORD_ROUND_1 + 1
RECORD_ROUND_2 = WIN_ROUND_2 + 1

FINAL_PLACE = RECORD_ROUND_2 + 1
RECORD_ROUND_3 = FINAL_PLACE + 1

# UL: isu tsp uid nck grp fio fst wr1 h10 rr1 wr2 rr2 fnl rr3
# DB: tsp isu uid nck grp fio fst wr1 h10 rr1 wr2 rr2 fnl rr3

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
Да.

Рекорд раундов в блокпати:
{}

Поставят ли 10 баллов:
{}

Переходишь ли в следующий этап:
{}
{}{}
Обязательно проверь все данные, только в случае несоответствий или важных вопросов напиши в ответ "АДМИН"
Читай о нас подробнее на сайте https://joutak.ru/minigames и других разделах
'''.strip()

second_part = '''
Рекорд во втором этапе:
{}

Проходишь ли ты в финал:
{}

'''

third_part = '''
Рекорд в третьем этапе:
{}

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


warnings = []


def warn(*s: str) -> None:
    # print('Warning:', *s)
    warnings.append('Warning: ' + ' '.join(s))


def str2ts(s: str) -> int:
    return int(datetime.strptime(s, '%m/%d/%Y %H:%M:%S').timestamp())


def ts2str(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).strftime('%m/%d/%Y %H:%M:%S')


class UserList:
    s2b = lambda s: s == '1'
    b2s = lambda b: '1' if b else '0'
    load2db = (str2ts, int, int, str, str, str, s2b, s2b, s2b, int, s2b, int, int, int)
    db_types = (str2ts, int, str, str, str, s2b, s2b, s2b, int, s2b, int, int, int)
    db2save = (ts2str, str, str, str, str, str, b2s, b2s, b2s, str, b2s, str, str, str)

    def __init__(self, path: str, vk_helper) -> None:
        # UL: isu tsp uid nck grp fio fst wr1 h10 rr1 wr2 rr2 fnl rr3
        # DB: tsp isu uid nck grp fio fst wr1 h10 rr1 wr2 rr2 fnl rr3
        self.db = dict[int: tuple[int, int, str, str, str, bool, bool, bool, int, bool, int, int, int]]()
        self.uid_to_isu = dict[int, int]()
        self.path = path
        self.vk_helper = vk_helper
        if self.load() is False:
            raise OSError('Something went wrong while loading DB')

    # Обрабатывает базу данных, заодно проверяя её правильность. Если что-то не так, то исправляет
    def load(self) -> bool:
        if is_file_accessible(self.path) is False:
            return False
        changes = False
        incorrect_uids = dict()
        incorrect_isu = 100000
        self.db.clear()
        with open(self.path, 'r', encoding='UTF-8') as file:
            for n, line in enumerate(file):
                s: list[str] = line.strip().split('\t')
                # строка пустая
                if not s:
                    warn(f'empty {n}-th line in DB')
                    continue
                # isu id не из цифр
                if not all(d.isdigit() for d in s[1]):  # isu
                    warn(f'isu id is NaN in {n}-th line in DB: {s[1]}')
                    s[1] = str(incorrect_isu)
                    incorrect_isu += 1
                if s[2] == '0':  # vk_uid
                    warn(f'vk id is NaN (isu = {s[1]}) in {n}-th line in DB:', s[2])
                # vk_uid не определён, потом определим
                elif not all(d.isdigit() for d in s[2]):  # vk_uid
                    incorrect_uids[int(s[1])] = s[2]
                    s[2] = '0'
                    changes = True
                if len(s[5].split()) != 3:  # fio
                    warn(f'something wrong with fio (isu = {s[1]}) in {n}-th line in DB:', s[5])
                    # but okay, it's his or her problem
                if len(s) < 8:
                    s.extend(list('000'))
                if len(s) < 11:
                    s.extend(list('00'))
                if len(s) < 13:
                    s.extend(list('00'))
                    changes = True
                # UL: isu tsp uid nck grp fio fst wr1 h10 rr1 wr2 rr2 fnl rr3
                # DB: tsp isu uid nck grp fio fst wr1 h10 rr1 wr2 rr2 fnl rr3
                s = [f(i) for f, i in zip(self.load2db, s)]
                self.db[s[1]] = s[0], *s[2:]
        # достаём все vk_uid через vk_link
        incorrect_uids = sorted(incorrect_uids.items())
        for i in range(0, len(incorrect_uids), 25):
            part = incorrect_uids[i:min(i + 25, len(incorrect_uids))]
            links = []
            for isu, uid in part:
                start = uid.rfind('/') + 1
                if start == -1:
                    start = uid.find('@') + 1
                if start == -1:
                    start = 0
                links.append(uid[start:])
            response = self.vk_helper.links_to_uids(links)
            for pair, uid in zip(part, response):
                user = list(self.db[pair[0]])
                user[VK_UID] = int(uid)
                self.db[pair[0]] = tuple(user)
        # делаем штуку для быстрого доступа к пользователю через uid
        for isu in self.db.keys():
            user = self.db[isu]
            if user[VK_UID] != 0:
                self.uid_to_isu[user[VK_UID]] = isu
        if changes is True:
            return self.save()
        return True

    def save(self) -> bool:
        if is_file_accessible(self.path) is False:
            return False
        to_save = []
        for isu in self.db.keys():
            v = self.db[isu]
            v = [f(i) for f, i in zip(self.db2save, [v[0], isu] + list(v)[1:])]
            to_save.append((v[0], '\t'.join(v)))
        to_save.sort()
        with open(users_path, 'w', encoding='UTF-8') as file:
            file.write('\n'.join(i[1] for i in to_save))
        return True

    def get(self, isu: int) -> tuple[int, int, str, str, str, bool, bool, bool, int, bool, int, int, int] | None:
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
    ('tsp', 'uid', 'nck', 'grp', 'fio', 'fst', 'wr1', 'h10', 'rr1', 'wr2', 'rr2', 'fnl', 'rr3'),
    ('s24', 's25', 'adm')
)


def check_condition(cond: str) -> bool:
    for token in tokens[0]:
        if token in cond:
            return all(check_condition(i) for i in cond.split(token))
    for token in tokens[1]:
        if token in cond:
            c = cond.split(token)
            return len(c) == 2 and c[0] in tokens[3] and c[1] in tokens[4]
    for token in tokens[2]:
        if token in cond:
            c = cond.split(token)
            return len(c) == 2 and c[0] in tokens[3]
    return False


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
    for token in tokens[2]:
        if token in cond:
            c = cond.split(token)
            index = tokens[3].index(c[0])
            v = user[index]
            predicate = (v.__eq__, v.__ne__, v.__gt__, v.__ge__, v.__lt__, v.__le__)
            return predicate[index](UserList.db_types[index](c[1]))
    if '!=' in cond:
        c = cond.split('!=')
        return str(user[tokens[3].index(c[0])]) != c[1]
    return False


def sender(self, condition: str, msg: str) -> list[dict]:
    if check_condition(condition) is False:
        return [{'peer_id': uid, 'message': 'Condition issue'} for uid in admin]
    users: UserList = self.users
    result = []
    for isu in users.keys():
        user = users.get(isu)
        uid = user[VK_UID]
        if uid == '0':
            continue
        if eval_condition(user, condition) is True:
            result.append({'peer_id': uid, 'message': msg})
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
            return [{'peer_id': uid, 'message': 'Success' if (self.users.load() is True) else 'Failed'}]
        elif msgs[0] == 'sender':
            if len(msgs) > 2:
                result = sender(self, msgs[1], ' '.join(msgs[2:]).strip())
                self.handle_actions(result)
                tts = f'Готово. Всего разослано {len(result)} сообщений'
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
        if uid in users.uid_to_isu:
            isu = users.uid_to_isu[uid]
            user = users.get(isu)
            tts = welcome_message.format(
                isu, user[NICKNAME],
                ['Нет', 'Да'][user[WIN_ROUND_1]], ['Нет', 'Да'][user[HAS_10_BALLS]], user[RECORD_ROUND_1],
                second_part.format(user[RECORD_ROUND_2], ['Нет', 'Да'][user[WIN_ROUND_2]]) if user[WIN_ROUND_1] else '',
                third_part.format(user[RECORD_ROUND_3], user[FINAL_PLACE]) if user[WIN_ROUND_2] else '')
        else:
            tts = 'Кажется, у нас нет твоих данных. Позови админа, если это не должно быть так'
    return [{
        'peer_id': uid,
        'message': tts
    }]
