# -*- coding: utf-8 -*-
import vk_api
from random import randint as rd
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def lsend(id,text):
    print("sended")
    vk_session.method('messages.send', {'user_id': id, 'message': text, 'random_id': 0})
def sender(sender_type):
    global subscribers_spartakiada
    global tens
    global wins2
    global wins3
    global uidvk
    if sender_type=="spartakiada":
        for i in range(len(uidvk)):
            if wins3[i]=="2":
                countd=52
            elif wins3[i]=="1":
                countd=14
            elif wins2[i]=="1":
                countd=7
            elif tens!="0":
                countd=1
            message="Привет! На прошлых выходных ты участвовал в спартакиаде, проведённой клубом любителей игры «Майнкрафт» ITMOcraft. Думаю, самое время познакомиться!\n\nНаш клуб — комьюнити итмошников, которым нравится играть в майнкрафт. Выживание, моды, миниигры: если во что-то можно играть, мы создаём для этого условия. Наша альма-матер — SMP JouTak. Это сервер с шестилетней историей (без вайпов, без приватов, без случайных людей), в итмошном районе которого мы вместе уже построили Кронву, Вязьму и даже Ленсовета, а игроки возводят свои проекты, болтают в войсчате и просто отдыхают. Более того, мы регулярно проводим там ивенты, самое время залететь на сервер👻\nТочно! Тебе же ещё положены бонусы за участие в спартакиаде: "+str(countd)+"д. (+30дней, если у тебя лицензия)\n\nКак это сделать?\n1) Подключайся в дискорд: https://discord.gg/YVj5tckahA\n2) Заполняй анкету, чтобы мы с тобой связались: https://forms.yandex.ru/u/6501f64f43f74f18a8da28de/\n3) Следи за новостями в телеграм канале: t.me/itmocraft! Помогая нашему продвижению, ты делаешь наши ивенты масштабнее, а сервера круче!\nP.S. Плашку в ису \"член клуба ITMOcraft\" тоже можно получить после заполнения этой анкеты, по желанию. Если есть вопросы, пиши!"
            try:
                lsend(uidvk[i],message)
                if str(uidvk[i]) not in subscribers_spartakiada:
                    subscribers_spartakiada.append(str(uidvk[i]))
                    with open ("subscribers/spartakiada.txt","w") as f:
                        for i in range(len(subscribers_spartakiada)):
                            f.write(str(int(subscribers_spartakiada[i]))+"\n")
            except: pass
                
with open ("token.txt",'r') as f:
    token=f.readline()
admin=[297002785, 275052029]
vk_session=vk_api.VkApi(token=token)
vk = vk_session.get_api()
groupid=217494619
longpoll=VkBotLongPoll(vk_session, groupid)
isu=[];nickname=[];password=[];uidvk=[];idvk=[];tens=[];wins1=[];wins2=[];wins3=[]
ignore=[529015396, 403426536, 454638783, 475294527, 178196074, 214648360]
subscribers_spartakiada=[]
with open("passwords.txt",'r') as f:
    for x in f.readlines():
        x=x.split()
        if x==[]: break
        isu.append(x[0])
        nickname.append(x[1])
        password.append(x[2])
        uidvk.append(x[3])
        tens.append(x[4])
        wins1.append(x[5])
        wins2.append(x[6])
        wins3.append(x[7])
with open ("subscribers/spartakiada.txt","r") as f:
    for x in f.readlines():
        subscribers_spartakiada.append(x)
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
print("работай")
while True:
    try:
        for event in longpoll.listen():
            if event.type==VkBotEventType.MESSAGE_NEW:
                id=event.message.from_id
                idp=id
                peer_id=2000000000+id
                msg=event.object.message['text'].lower()
                msgs=msg.split()
                
                if idp in admin:
                    if msgs[0]=="stop":
                        exit()
                    elif msgs[0]=="sender":
                        sender(msgs[1])
                        tts="готово"
                if "админ" in msg:
                    if idp in ignore:
                        ignore.remove(idp)
                        tts="Надеюсь, вопрос снят!"
                        for i in range(len(admin)):
                            lsend(admin[i],"vk.com/id"+str(idp) + " не вызывает")
                    else: 
                        ignore.append(idp)
                        tts="Принято, сейчас позову! Напиши свою проблему следующим сообщением"
                        for i in range(len(admin)):
                            lsend(admin[i],"vk.com/id"+str(idp) + " вызывает")
                    lsend(idp,tts)
                if idp in ignore:
                    continue
                else:
                    #print(vk.method.groups.isMember(groupid, idp))
                    if vk_session.method('groups.isMember', {'group_id': groupid, 'user_id': idp})==0:
                        tts="Привет! Для получение информации о серверах ИТМОкрафта подпишитесь:\n[https://vk.com/widget_community.php?act=a_subscribe_box&oid=-217494619&state=1|ITMOcraft. Подписаться]\n\nПосле подписки отправь ещё одно сообщение. Только в случае возникновения проблем пиши \"АДМИН\""
                    else:
                        tts="Привет! Добро пожаловать в бота клуба любителей игры «Майнкрафт» ITMOcraft. Думаю, самое время познакомиться!\n\nНаш клуб — комьюнити итмошников, которым нравится играть в майнкрафт. Выживание, моды, миниигры: если во что-то можно играть, мы создаём для этого условия. Наша альма-матер — SMP JouTak. Это сервер с шестилетней историей (без вайпов, без приватов, без случайных людей), в итмошном районе которого мы вместе уже построили Кронву, Вязьму и даже Ленсовета, а игроки возводят свои проекты, болтают в войсчате и просто отдыхают. Более того, мы регулярно проводим там ивенты, самое время залететь на сервер👻 (+30дней, если у тебя лицензия)\n\nКак это сделать?\n1) Подключайся в дискорд: https://discord.gg/YVj5tckahA\n2) Заполняй анкету, чтобы мы с тобой связались: https://forms.yandex.ru/u/6501f64f43f74f18a8da28de/\n3) Следи за новостями в нашем телеграм канале: t.me/itmocraft\nP.S. Плашку в ису \"член клуба ITMOcraft\" тоже можно получить после заполнения этой анкеты, по желанию. Если есть вопросы, пиши АДМИН!"
                        lsend(idp,tts)
                if str(idp) not in subscribers_spartakiada:
                    subscribers_spartakiada.append(str(idp))
                    with open ("subscribers/spartakiada.txt","w") as f:
                        for i in range(len(subscribers_spartakiada)):
                            f.write(str(int(subscribers_spartakiada[i]))+"\n")               
    except Exception as exc:
        print("error lol:\n"+str(exc))
