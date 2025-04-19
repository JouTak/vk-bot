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

tsp - timestamp
uid - vk_uid
nck - nickname
grp - group_id
fio - fio
fst - first_time
wr1 - won_round_1
h10 - has_10_balls
rr1 - record_round_1
wr2 - won_round_2
rr2 - record_round_2
fnl - final_place
rr3 - record_round_3


s24 - spartakiada24_subs
s25 - spartakiada25_subs
adm - admin


&, |, ->, !>, ==, !=, >>, >=, <<, <= - logic
tsp, uid, nck, grp, fio, fst, wr1, h10, rr1 - parameters
s24, s25, a - sets


-> and !> only with parameters and sets (uid->s24)
other logic only with parameters and value (nck==enderdissa)
```