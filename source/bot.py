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
LOSE_ROUND_1 = WIN_ROUND_1 + 1
RECORD_ROUND_1 = LOSE_ROUND_1 + 1
# isu: (timestamp, vk_uid, link, nick, group, fio, first_time)

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

Переходишь ли в следующий этап:
{}

Поставят ли 10 баллов:
{}

Рекорд раундов в блокпати:
{}

Обязательно проверь все данные, только в случае несоответствий или важных вопросов напиши в ответ "АДМИН"
Читай о нас подробнее на сайте https://joutak.ru/minigames и других разделах
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
        self.db = dict[int: tuple[str, str, str, str, str, str, str, bool, bool, int]]()
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
        incorrect_uids = set()
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
                    incorrect_uids.add(int(s[1]))
                    changes = True
                if len(s[5].split()) != 3:  # fio
                    warn(f'something wrong with fio (isu = {s[1]}) in {n}-th line in DB:', s[5])
                    # but okay, it's his or her problem
                if len(s) < 9:
                    s.extend(list('000'))
                    changes = True
                # DB   | timestamp isu vk_uid nick    group   fio first_time
                # Dict | isu: (timestamp, vk_uid, nick, group, fio, first_time)
                self.db[int(s[1])] = s[0], s[2], s[3], s[4], s[5], s[6], s[7] == '1', s[8] == '1', int(s[9])
        # достаём все vk_uid через vk_link
        incorrect_uids = sorted(incorrect_uids)
        for i in range(0, len(incorrect_uids), 25):
            part = incorrect_uids[i:min(i + 25, len(incorrect_uids))]
            links = []
            for isu in part:
                start = self.db[isu][VK_UID].rfind('/') + 1
                if start == -1:
                    start = self.db[isu][VK_UID].find('@') + 1
                if start == -1:
                    start = 0
                links.append(self.db[isu][VK_UID][start:])
            response = self.vk_helper.links_to_uids(links)
            for isu, uid in zip(part, response):
                user = list(self.db[isu])
                user[VK_UID] = str(uid)
                self.db[isu] = tuple(user)
        # делаем штуку для быстрого доступа к пользователю через uid
        for isu in self.db.keys():
            user = self.db[isu]
            if user[VK_UID] != '0':
                self.uid_to_isu[int(user[VK_UID])] = isu
        if changes is True:
            return self.save()
        return True

    def save(self) -> bool:
        if is_file_accessible(self.path) is False:
            return False
        to_save = []
        for key in self.db.keys():
            v = self.db[key]
            to_save.append((str2ts(v[0]), '\t'.join((v[0], str(key), *v[1:-3], '01'[v[-3]], '01'[v[-2]], str(v[-1])))))
        to_save.sort()
        with open(users_path, 'w', encoding='UTF-8') as file:
            file.write('\n'.join(i[1] for i in to_save))
        return True

    def get(self, isu: int) -> tuple[str, str, str, str, str, str, str] | None:
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


def sender(self, sender_type: str) -> list[dict]:
    users: UserList = self.users
    vk_helper = self.VK
    result = []
    # TODO: Не знаю, как назвать, сам реши
    if sender_type == 'in24notin25':
        users = self.users
        copy = spartakiada24_subs.copy()
        for isu in users.keys():
            if int(users.get(isu)[VK_UID]) in copy:
                copy.remove(int(users.get(isu)[VK_UID]))
        result.extend([{'peer_id': uid, 'message': 'in24notin25 sending...'} for uid in admin])
        result.extend([{'peer_id': uid, 'message': 'Рассылка пошла'} for uid in admin])
        for uid in copy:
            result.append({'peer_id': uid, 'message': 'Привет! Ты участвовал в нашей осенней спартакиаде по майнкрафту. По моим данным ты ещё не зарегистрировался на весенню спартакиаду! Новые, крутые режимы ждут тебя: BlockParty, AceRace, Survival Games.\nРегистрация почти завершена, не упусти возможности снова получить 10 баллов за майнкрафт — вся информация на https://joutak.ru/minigames. P.S. если считаешь, что произошла ошибка и ты зарегистрирован в 2025 году, напиши АДМИН'})
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
                if int(user[VK_UID]) in spartakiada25_subs:
                    continue
                spartakiada25_subs.add(int(user[VK_UID]))
                with open('./subscribers/spartakiada24.txt', 'a', encoding='UTF-8') as file:
                    file.write(user[VK_UID] + '\n')
            except OSError as e:
                warn(f'Warning: can not write id {user[VK_UID]} in spartakiada DB because of: {e}')
    elif sender_type == 'to0record1':
        result.extend([{'peer_id': uid, 'message': 'to0record1 sending...'} for uid in admin])
        result.extend([{'peer_id': uid, 'message': 'Рассылка пошла'} for uid in admin])
        for isu in users.keys():
            user = users.get(isu)
            uid = user[VK_UID]
            record = user[LOSE_ROUND_1]
            if uid == '0':
                continue
            if record is True:
                continue
            result.append({'peer_id': uid, 'message': 'Добрый вечер! Я знаю, что ты регистрировался на спартакиаду, но всё ещё не отыграл две попытки. Варианта два:\n1: ты забыл поучаствовать, в таком случае беги скорее за майн и отыгрывай свои две попытки. Сделать это у тебя есть буквально меньше получаса. \n2: Данные в бот ещё не подгрузились, в таком случае зайди в майн, заскринь то, что тебя не пускает по причинам конца попыток или победы или напиши, во сколько примерно была катка, позови админа и в течение суток мы досоотнесём данные. (Убедись, что админы заметили твоё сообщение)'})  # TODO: заполни чё надо
    print(*result, sep='\n')
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

    user_get = vk_helper.vk.users.get(user_ids=uid)
    user_get = user_get[0]
    uname = user_get['first_name']
    username = user_get['last_name']

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
            link_keyboard = create_link_keyboard(buttons)
            if ignored.is_ignored(uid):
                ignored.remove(uid)
                ignored.save_to_file()
                tts = 'Надеюсь, вопрос снят!'
                Ctts = f'{uname} {username} больше не вызывает!'
                buttons = [{'label': 'ПОЗВАТЬ АДМИНА', 'payload': {'type': 'callmanager'}, 'color': 'positive'}]
                keyboard = create_standart_keyboard(buttons)

            else:
                ignored.add(uid)
                ignored.save_to_file()
                tts = 'Принято, сейчас позову! Напиши свою проблему следующим сообщением. ' \
                      'Когда вопрос будет решён, ещё раз напиши команду или нажми на кнопку.'
                Ctts = f'{uname} {username} вызывает!'
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
                        'message': Ctts,
                        'keyboard': link_keyboard,
                        'attachment': None
                    } for uid in admin
                ]
            ]

    if uid in admin:
        if msgs[0] == 'stop':
            exit()
        elif msgs[0] == 'reload':
            if self.users.load() is True:
                return [{'peer_id': uid, 'message': 'Success'}]
            else:
                return [{'peer_id': uid, 'message': 'Failed'}]
        elif msgs[0] == 'sender':
            if len(msgs) > 1:
                self.handle_actions(sender(self, msgs[1]))
                tts = 'Готово'
            else:
                tts = 'Нет аргумента'
            return [{
                'peer_id': uid,
                'message': tts
            }]
    if vk_helper.vk_session.method('groups.isMember', {'group_id': groupid, 'user_id': uid}) == 0:
        tts = info_message
    else:
        if uid in users.uid_to_isu:
            isu = users.uid_to_isu[uid]
            user = users.get(isu)
            tts = welcome_message.format(
                isu, user[NICKNAME],
                ['Нет', 'Да'][user[WIN_ROUND_1]], ['Нет', 'Да'][user[LOSE_ROUND_1]], user[RECORD_ROUND_1])
        else:
            tts = 'Кажется, у нас нет твоих данных. Позови админа'
    return [{
        'peer_id': uid,
        'message': tts
    }]
    # if uid not in spartakiada25_subs:
    #     spartakiada25_subs.add(uid)
    #     with open(spartakiada_subs_path.format(25), 'a') as file:
    #         file.write(str(uid) + '\n ')
    #         tts = 'Привет, добро пожаловать в бота клуба ITMOcraft! Сейчас у нас проходит спартакиада, но, кажется, ' \
    #               'у нас нет твоих данных. Если считаешь, что произошла ошибка — позови админа командой АДМИН. ' \
    #               'Если хочешь зарегистрироваться — скорее делай это на сайте https://joutak.ru/minigames'
    #     return [{
    #         'peer_id': uid,
    #         'message': tts
    #     }]
    # if uid not in spartakiada24_subs:
    #     spartakiada24_subs.add(uid)
    #     with open(spartakiada_subs_path.format(25), 'a') as file:
    #         file.write(str(uid) + '\n')
