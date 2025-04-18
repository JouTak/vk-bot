# -*- coding: utf-8 -*-
import os.path
from datetime import datetime

spartakiada24_subs_path = './subscribers/spartakiada24.txt'
spartakiada25_subs_path = './subscribers/spartakiada25.txt'
users_path = './users.txt'

admin = [297002785, 275052029, 229488682]

TIMESTAMP = 0
VK_UID = TIMESTAMP + 1
VK_LINK = VK_UID + 1
NICKNAME = VK_LINK + 1
GROUP_ID = NICKNAME + 1
FIO = GROUP_ID + 1
FIRST_TIME = FIO + 1
# isu: (timestamp, vk_uid, link, nick, group, fio, first_time)

groupid = 230160029  # 217494619
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
    'Привет! Для получение информации о серверах ИТМОкрафта подпишитесь:\n' \
    f'[{vk_link}. Подписаться]\n\n' \
    'После подписки отправь ещё одно сообщение. Только в случае возникновения проблем пиши "АДМИН"'

welcome_message = '''
Добро пожаловать на спартакиаду ИТМО по майнкрафту! Записывай данные для входа на сервер:

ИСУ:
{}

Ник:
{}

Обязательно проверь все данные, только в случае несоответствий или важных вопросов напиши в ответ "АДМИН"
'''.strip()
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
    def __init__(self, path: str, vk_helper) -> None:
        # isu: (timestamp, vk_uid, vk_link, nick, group, fio, first_time)
        self.db = dict[int: tuple[str, str, str, str, str, str, str]]()
        self.by_uid = dict[int, tuple[int, str, str, str, str, str]]()
        self.path = path
        self.vk_helper = vk_helper
        if self.load() is False:
            raise OSError('Something went wrong while loading DB')

    # Обрабатывает базу данных, заодно проверяя её правильность. Если что-то не так, то исправляет
    def load(self) -> bool:
        if is_file_accessible(self.path) is False:
            return False
        changes = False
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
                # vk_uid не определён, пытаемся определить
                if s[2] == '0':  # vk_uid
                    # достаём его через vk_link
                    start = s[3].rfind('/')  # vk_link
                    if start == -1:
                        start = s[3].find('@')  # vk_link
                    if start == -1:
                        warn(f'vk uid is 0 and error occurred while parsing vk link in {n}-th line in DB: {s[3]}')
                    try:
                        uid = s[3][start + 1:]  # vk_link
                        if all(d.isdigit() for d in uid):
                            uid = 'id' + uid
                        print(f'{n}. Trying to get {s[6]}\'s vk uid with {s[3]}', end=' ')
                        s[3] = str(self.vk_helper.vk.resolveScreenName(screen_name=uid)['object_id'])
                        print('[✓]')
                        changes = True
                    except Exception as e:
                        print('[X]')
                        warn(f'something went wrong while getting vk id (isu = {s[1]}) in {n}-th line in DB: {e}')
                # из цифр ли vk_uid
                elif not all(d.isdigit() for d in s[2]):  # vk_uid
                    warn(f'vk id is NaN (isu = {s[1]}) in {n}-th line in DB:', s[2])
                # весь ли ФОИ заполнен
                if len(s[6].split()) != 3:  # fio
                    warn(f'something wrong with fio (isu = {s[1]}) in {n}-th line in DB:', s[6])
                    # but okay, it's his or her problem
                # DB   | timestamp isu vk_uid  vk_link nick    group   fio first_time
                # Dict | isu: (timestamp, vk_uid, vk_link, nick, group, fio, first_time)
                self.db[int(s[1])] = s[0], s[2], s[3], s[4], s[5], s[6], s[7]
        for isu in self.db.keys():
            user = self.db[isu]
            if user[VK_UID] != '0':
                self.by_uid[VK_UID] = (isu, user[2], user[3], user[4], user[5], user[6])
        if changes is True:
            return self.save()
        return True

    def save(self) -> bool:
        if is_file_accessible(self.path) is False:
            return False
        to_save = []
        for key in self.db.keys():
            v = self.db[key]
            to_save.append((str2ts(v[0]), '\t'.join((v[0], str(key), v[1], v[2], v[3], v[4], v[5], v[6]))))
        to_save.sort()
        with open('./users.txt', 'w', encoding='UTF-8') as file:
            file.write('\n'.join(i[1] for i in to_save))
        return True

    def get(self, isu: int) -> tuple[str, str, str, str, str, str, str] | None:
        return self.db[isu] if isu in self.db.keys() else None

    def keys(self):
        return self.db.keys()


def init_spartakiada24_subs() -> set[int]:
    # DB   | timestamp isu vk_uid  vk_link nick    group   fio first_time
    spartakiada24_subs = set[int]()
    with open(spartakiada24_subs_path, 'r', encoding='UTF-8') as file:
        for n, uid in enumerate(file):
            if not all(d.isdigit() for d in uid):
                warn(f'something wrong with id in {n}-th line in spartakiada subs DB')
                continue
            spartakiada24_subs.add(int(uid))
    return spartakiada24_subs


def save_spartakiada24_subs() -> bool:
    if is_file_accessible(spartakiada24_subs_path) is False:
        return False
    with open(spartakiada24_subs_path, 'w', encoding='UTF-8') as file:
        file.writelines(map(str, sorted(spartakiada24_subs)))
    return True


spartakiada24_subs = init_spartakiada24_subs()


def sender(sender_type: str, users: UserList) -> list[dict]:
    result = []
    # TODO: Не знаю, как назвать, сам реши
    if sender_type == 'in25notin24':
        copy = spartakiada24_subs.copy()
        for isu in users.keys():
            if isu in copy:
                copy.remove(isu)
        for i in copy:
            pass
    elif sender_type == 'spartakiada2025':
        for isu in users.keys():
            user = users.get(isu)
            day_reward = 0
            # TODO: сделайте условие
            # if users[user][?]:
            #     day_reward = ?
            message = hi_message.format(day_reward)
            try:
                # lsend(uidvk[i],message)
                if user[VK_UID] == '0':
                    continue
                if int(user[VK_UID]) in spartakiada24_subs:
                    continue
                spartakiada24_subs.add(int(user[VK_UID]))
                with open('./subscribers/spartakiada24.txt', 'a', encoding='UTF-8') as file:
                    file.write(user[VK_UID] + '\n')
            except OSError as e:
                warn(f'Warning: can not write id {user[VK_UID]} in spartakiada DB because of: {e}')
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
    tts = ''
    users = self.users
    uid = event.message.from_id
    user = users.by_uid[uid]
    peer_id = 2000000000 + uid

    user_get = vk_helper.vk.users.get(user_ids=uid)
    user_get = user_get[0]
    uname = user_get['first_name']
    username = user_get['last_name']

    msgraw = event.message.text
    msg = event.message.text.lower()
    msgs = msg.split()

    if event.from_chat:
        id = event.chat_id
        uid = event.obj['message']['from_id']
        peer_id = 2000000000 + uid
        return
    else:
        if ignored.is_ignored(uid):
            if 'админ' not in msg:
                return
        if 'админ' in msg:
            link = f'https://vk.com/gim{groupid}?sel={uid}'
            buttons = [{'label': 'прямая ссылка', 'payload': {'type': 'userlink'}, 'link': link}]
            link_keyboard = vk_helper.create_link_keyboard(buttons)
            if ignored.is_ignored(uid):
                ignored.remove(uid)
                ignored.save_to_file()
                tts = 'Надеюсь, вопрос снят!'
                Ctts = f'{uname} {username} больше не вызывает!'
                buttons = [{'label': 'ПОЗВАТЬ АДМИНА', 'payload': {'type': 'callmanager'}, 'color': 'positive'}]
                keyboard = vk_helper.create_standart_keyboard(buttons)

            else:
                ignored.add(uid)
                ignored.save_to_file()
                tts = 'Принято, сейчас позову! Напиши свою проблему следующим сообщением. ' \
                      'Когда вопрос будет решён, ещё раз напиши команду или нажми на кнопку.'
                Ctts = f'{uname} {username} вызывает!'
                buttons = [{'label': 'СПАСИБО АДМИН', 'payload': {'type': 'uncallmanager'}, 'color': 'negative'}]
                keyboard = vk_helper.create_standart_keyboard(buttons)
            return [
                {
                    'peer_id': uid,
                    'message': tts,
                    'keyboard': keyboard,
                    'attachment': None
                },
                {
                    'peer_id': admin[0],
                    'message': Ctts,
                    'keyboard': link_keyboard,
                    'attachment': None
                },
                {
                    'peer_id': admin[1],
                    'message': Ctts,
                    'keyboard': link_keyboard,
                    'attachment': None
                },
                {
                    'peer_id': admin[2],
                    'message': Ctts,
                    'keyboard': link_keyboard,
                    'attachment': None
                }
            ]

    if uid in admin:
        if msgs[0] == 'stop':
            exit()
        elif msgs[0] == 'sender':
            sender(msgs[1], vk_helper)
            tts = 'готово'
    if vk_helper.vk_session.method('groups.isMember', {'group_id': groupid, 'user_id': uid}) == 0:
        tts = info_message
    else:
        tts = welcome_message.format(user[0], user[3])
        return [{
            'peer_id': uid,
            'message': tts
        }]
    if uid not in spartakiada24_subs:
        spartakiada24_subs.add(uid)
        with open(spartakiada25_subs_path, 'a') as file:
            file.write(str(uid) + '\n')
