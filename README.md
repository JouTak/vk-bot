# ITMOcraftBOT
![Static Badge](https://img.shields.io/badge/JouTak-vk)
![GitHub top language](https://img.shields.io/github/languages/top/JouTak/vk-bot)

VK bot (vk.com/itmocraft)

HOWTO:
1) git clone
2) pip install -r source/requirements.py (installing requirements)
3) python setup.py (asking for token)
4) python main.py (running bot itself)

For admins:
How to use sender?
```
sender [some_logic] <message>

& - and
| - or
-> - in
!> - not in
== - equals
!= - not equals
>> - greater than
>= - greater than or equals
<< - less than
<= - less than or equals

Формат БД:
isu, uid, fio, grp, nck, met: {
s24: {tsp, nck, lr1, wr1, wr2, nyt, fnl},
s25: {tsp, nck, wr1, rr1, wr2, rr2, fnl},
y25: {tsp, nck, nmb, bed, way, car, liv, ugo}}

isu — ИСУ (спец номера от 0 до 99999, если не из ИТМО)
uid — ссылка ВК, если ещё не обработана, иначе VK id (0 если ссылка неверна, 1 если не указано, иначе реальный id)
fio — ФИО
grp — group, группа ('', если не из ИТМО)
nck — nick — ник в Майнкрафте
met — metadata — словарь с метаданными об ивентах

tsp — timestamp — время заполнения формы в формате unix timestamp
wrN — win round N — выиграл ли первый раунд
lrN — lose round N — истратил ли все попытки (одновременно c этим может и выиграть (wr1==1))
rrN — round record N — наилучший результат в раунде
nyt — not yet — ещё не играл в финале
fnl — final — играл ли в финале (s24), либо какое место в нём занял (s25)

sts — status — статус в ИТМО (является индексом из ('Действующий студент', 'Выпускник / отчисляш', 'Сотрудник', 'Не из ИТМО'))
nmb — number — номер телефона
why — мотивация поехать
bed — планирует ли взять бельё
way — способ, каким чел добирается (индекс из ('На бесплатном трансфере от ГК', 'Своим ходом (электричка)', 'Своим ходом (на машине)'))
car — номер машины, если добирается на машине, иначе '-'
liv — с кем чел живёт
ugo — you go — поедет ли чел


|, & — для составных выражений
->, !> — есть ли метаданные у юзера
==, != >>, >=, <<, <= — для сравнения значений полей
. — для обращения к полю юзера / его метаданным
```
