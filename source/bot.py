# -*- coding: utf-8 -*-
import os
import vk_api
from random import randint as rd
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

# def sender(sender_type): #TODO: переписать сендер
#     global subscribers_spartakiada
#     global tens
#     global wins2
#     global wins3
#     global uidvk
#     if sender_type=="spartakiada":
#         for i in range(len(uidvk)):
#             if wins3[i]=="2":
#                 countd=52
#             elif wins3[i]=="1":
#                 countd=14
#             elif wins2[i]=="1":
#                 countd=7
#             elif tens!="0":
#                 countd=1
#             message="Привет! На прошлых выходных ты участвовал в спартакиаде, проведённой клубом любителей игры «Майнкрафт» ITMOcraft. Думаю, самое время познакомиться!\n\nНаш клуб — комьюнити итмошников, которым нравится играть в майнкрафт. Выживание, моды, миниигры: если во что-то можно играть, мы создаём для этого условия. Наша альма-матер — SMP JouTak. Это сервер с шестилетней историей (без вайпов, без приватов, без случайных людей), в итмошном районе которого мы вместе уже построили Кронву, Вязьму и даже Ленсовета, а игроки возводят свои проекты, болтают в войсчате и просто отдыхают. Более того, мы регулярно проводим там ивенты, самое время залететь на сервер👻\nТочно! Тебе же ещё положены бонусы за участие в спартакиаде: "+str(countd)+"д. (+30дней, если у тебя лицензия)\n\nКак это сделать?\n1) Подключайся в дискорд: https://discord.gg/YVj5tckahA\n2) Заполняй анкету, чтобы мы с тобой связались: https://forms.yandex.ru/u/6501f64f43f74f18a8da28de/\n3) Следи за новостями в телеграм канале: t.me/itmocraft! Помогая нашему продвижению, ты делаешь наши ивенты масштабнее, а сервера круче!\nP.S. Плашку в ису \"член клуба ITMOcraft\" тоже можно получить после заполнения этой анкеты, по желанию. Если есть вопросы, пиши!"
#             try:
#                 #lsend(uidvk[i],message)
#                 if str(uidvk[i]) not in subscribers_spartakiada:
#                     subscribers_spartakiada.append(str(uidvk[i]))
#                     with open ("subscribers/spartakiada.txt","w") as f:
#                         for i in range(len(subscribers_spartakiada)):
#                             f.write(str(int(subscribers_spartakiada[i]))+"\n")
#             except: pass
                

admin=[297002785, 275052029]

isu=[];nickname=[];password=[];uidvk=[];idvk=[];tens=[];wins1=[];wins2=[];wins3=[]
ignore=[529015396, 403426536, 454638783, 475294527, 178196074, 214648360]
groupid = 217494619
subscribers_spartakiada=[]

# with open("passwords.txt",'r') as f:
#     for x in f.readlines():
#         x=x.split()
#         if x==[]: break
#         isu.append(x[0])
#         nickname.append(x[1])
#         password.append(x[2])
#         uidvk.append(x[3])
#         tens.append(x[4])
#         wins1.append(x[5])
#         wins2.append(x[6])
#         wins3.append(x[7])
# with open ("subscribers/spartakiada.txt","r") as f:
#     for x in f.readlines():
#         subscribers_spartakiada.append(x)
koeff=550
i=0
"""
for x in uidvk[koeff:]:
    i+=1
    finder=x.rfind("/")
    if finder==-1:
        finder=x.find("@")
    finder+=1
    idreq=x[finder:]
    try: 
        if idreq.isdigit(): 
            idreq="id"+idreq
        idvk.append(vk.utils.resolveScreenName(screen_name=idreq)['object_id'])
    except: idvk.append("-1")
with open("passwords.txt", 'w+') as f:
    for i in range(len(uidvk)-koeff):
        if str(uidvk[i+koeff])!=str(idvk[i]):
            #print(uidvk[i+koeff],idvk[i])
            uidvk[i+koeff]=str(idvk[i])
            print("обновлено:",isu[i+koeff], nickname[i+koeff], password[i+koeff], uidvk[i+koeff])
        
    for i in range(len(uidvk)):
        f.write(isu[i] +" " +nickname[i] +" "+ password[i] + " "+str(uidvk[i])+"\n")
"""
def process_message_event(event, vk_helper):
    pl = event.object.get('payload')
    #user_list = UserList() #TODO: userlist
    tts=""
    sender = int(pl['sender'])
    if pl: pass
    else: return
    return [{
        "peer_id": sender,
        "message": tts,
    }]

def process_message_new(event, vk_helper, ignored):
    tts=""
    #user_list = UserList()
    #user_list.load_from_file()
    uid=event.message.from_id
    peer_id = 2000000000 + uid

    user_get = vk_helper.vk.users.get(user_ids=uid)
    user_get = user_get[0]
    uname = user_get['first_name']
    usurname = user_get['last_name']

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
            if not "админ" in msg:
                return
        if "админ" in msg:
            link = f"https://vk.com/gim{groupid}?sel={uid}"
            buttons = [{"label": "прямая ссылка", "payload": {"type": "userlink"}, "link": link}]
            link_keyboard = vk_helper.create_link_keyboard(buttons)
            if ignored.is_ignored(uid):
                ignored.remove(uid)
                ignored.save_to_file()
                tts = "Надеюсь, вопрос снят!"
                Сtts = f"{uname} {usurname} больше не вызывает!"
                buttons = [{"label": "ПОЗВАТЬ АДМИНА", "payload": {"type": "callmanager"}, "color": "positive"}]
                keyboard = vk_helper.create_standart_keyboard(buttons)

            else:
                ignored.add(uid)
                ignored.save_to_file()
                tts = "Принято, сейчас позову! Напиши свою проблему следующим сообщением. " \
                      "Когда вопрос будет решён, ещё раз напиши команду или нажми на кнопку."
                Сtts = f"{uname} {usurname} вызывает!"
                buttons = [{"label": "СПАСИБО АДМИН", "payload": {"type": "uncallmanager"}, "color": "negative"}]
                keyboard = vk_helper.create_standart_keyboard(buttons)
            return [
                {
                    "peer_id": uid,
                    "message": tts,
                    "keyboard": keyboard,
                    "attachment": None
                },
                {
                    "peer_id": admin[0],
                    "message": Сtts,
                    "keyboard": link_keyboard,
                    "attachment": None
                },
                {
                    "peer_id": admin[1],
                    "message": Сtts,
                    "keyboard": link_keyboard,
                    "attachment": None
                }
            ]


    if uid in admin:
        if msgs[0]=="stop":
            exit()
        elif msgs[0]=="sender":
            #sender(msgs[1])
            tts="готово"
    if vk_helper.vk_session.method('groups.isMember', {'group_id': groupid, 'user_id': uid})==0:
        tts="Привет! Для получение информации о серверах ИТМОкрафта подпишитесь:\n[https://vk.com/widget_community.php?act=a_subscribe_box&oid=-217494619&state=1|ITMOcraft. Подписаться]\n\nПосле подписки отправь ещё одно сообщение. Только в случае возникновения проблем пиши \"АДМИН\""
    else:
        tts="Привет! Добро пожаловать в бота клуба любителей игры «Майнкрафт» ITMOcraft. Думаю, самое время познакомиться!\n\nНаш клуб — комьюнити итмошников, которым нравится играть в майнкрафт. Выживание, моды, миниигры: если во что-то можно играть, мы создаём для этого условия. Недавно мы получили от университета ещё большие мощности, поэтому с этой спартакиады мини-игры будут играться на постоянной основе! IP: craft.joutak.ru. Наша альма-матер — SMP JouTak. Это сервер с шестилетней историей (без вайпов, без приватов, без случайных людей), в итмошном районе которого мы вместе уже построили Кронву, Вязьму и даже Ленсовета, а игроки возводят свои проекты, болтают в войсчате и просто отдыхают. Более того, мы регулярно проводим там ивенты, самое время залететь на сервер👻 (+30дней, если у тебя лицензия)\n\nКак это сделать?\n1) Почитай информацию о том, что мы делаем, на нашем сайте: https://joutak.ru\n2) Заполняй анкету, чтобы мы с тобой связались: https://forms.yandex.ru/u/6501f64f43f74f18a8da28de/\n3) Следи за новостями в нашем телеграм канале: t.me/itmocraft. Помогая нашему продвижению, ты делаешь ивенты масштабнее, а сервера круче!\nP.S. Плашку в ису \"член клуба ITMOcraft\" тоже можно получить после заполнения этой анкеты, по желанию. Если есть вопросы, пиши АДМИН!"
        return [{
            "peer_id": uid,
            "message": tts
        }]
    if str(uid) not in subscribers_spartakiada:
        subscribers_spartakiada.append(str(uid))
        with open ("subscribers/spartakiada.txt","w") as f:
            for i in range(len(subscribers_spartakiada)):
                f.write(str(int(subscribers_spartakiada[i]))+"\n")
