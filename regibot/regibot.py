import vk_api
from random import randint as rd
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def lsend(id,text):
    print("sended")
    vk_session.method('messages.send', {'user_id': id, 'message': text, 'random_id': 0})

with open ("token.txt",'r') as f:
    token=f.readline()
admin=297002785
vk_session=vk_api.VkApi(token=token)
vk = vk_session.get_api()
groupid=217494619
longpoll=VkBotLongPoll(vk_session, groupid)
isu=[];nickname=[];password=[];uidvk=[];idvk=[]
ignore=[]

with open("passwords.txt",'r') as f:
    for x in f.readlines():
        x=x.split()
        if x==[]: break
        isu.append(x[0])
        nickname.append(x[1])
        password.append(x[2])
        uidvk.append(x[3])
       
koeff=540
i=0
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
                
                if idp==admin and msgs[0]=="stop":
                    exit()
                if "админ" in msg:
                    tts="Принято, сейчас позову!"
                    lsend(admin,"vk.com/id"+str(idp) + " вызывает")
                    if idp in ignore:
                        ignore.pop(idp)
                    else: ignore.append(idp)
                if idp in ignore:
                    continue
                else:
                    #print(vk.method.groups.isMember(groupid, idp))
                    if vk_session.method('groups.isMember', {'group_id': groupid, 'user_id': idp})==0:
                        tts="Для проверки своего ИСУ, ника, а также получения пароля с айпи подпишитесь:\n[https://vk.com/widget_community.php?act=a_subscribe_box&oid=-217494619&state=1|ITMOcraft. Подписаться]\n\nв случае возникновения проблем пиши \"АДМИН\""
                    else:
                        try:
                            ix=uidvk.index(str(idp))
                            #print(msgs, idp, ix)
                            l_isu=isu[ix]
                            l_nickname=nickname[ix]
                            l_password=password[ix]
                            tts="Добро пожаловать на спартакиаду ИТМО по майнкрафту! Записывай данные для входа на сервер:\n\nip:\n135.181.241.201:10105\n\nИСУ:\n"+l_isu+"\n\nНик:\n"+l_nickname+"\n\nПароль:\n"+l_password+"\n\nОбязательно проверь все данные, в случае несоответствий напиши в ответ \"АДМИН\""
                        except:
                            tts="Не могу найти твою страницу VK в списке. Возможно, ты не регистрировался на спартакиаду, но если ты просто ввёл неправильный вк при регистрации, позови админа командой \"АДМИН\""
                lsend(idp,tts)
    except Exception as exc:
        print("error lol:\n"+str(exc))
            