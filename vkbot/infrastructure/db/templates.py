"""
Шаблоны информационных сообщений ивентов.

Используются через EventDef.info_template.

Новый синтаксис:
- плейсхолдеры: {key}
- условия: $if (condition) $then "..." $else "..." $end
- ветки $then/$else всегда в кавычках
- перенос строки, стоящий после \\, удаляется
"""

E26_TASK_LINES = "".join(
    '$if (met.e26.clk != "") $then "Задание %d: {met.e26.z%02d}\n" $end'
    % (i, i)
    for i in range(1, 21)
)

E26_INFO_TEMPLATE = (
    '$if (fio != "" & fio != "-") '
    '$then "Привет, {fio}!\n" '
    '$else "Привет, участник!\n" '
    '$end'
    "ЕГЭ по майнкрафту — инфа ниже:\n"
    '$if (fio != "" & fio != "-") $then "Твоё ФИО: {fio}\n" $end'
    '$if (nck != "" & nck != "-") $then "Твой ник: {nck}\n" $end'
    '$if (met.e26.clk != "") $then "Время сдачи: {met.e26.clk}\n" $end'
    '$if (met.e26.clk == "") $then "По нашей информации, тебя не было :(\n" $end'
    + E26_TASK_LINES
    + '$if (met.e26.clk != "") $then "Итого баллов (вторичных): {met.e26.sum}\n" $end'
    '$if (met.e26.clk != "" & met.e26.plc >> 0) $then "Твоё место: {met.e26.plc}\n" $end'
    '$if (met.e26.clk != "" & met.e26.plc == 0) $then "К сожалению, ты не занял призовое место" $end'
)

Y26_INFO_TEMPLATE = (
    "Привет! Вот твои данные по выезду в Ягодное:\n"
    '$if (met.y26.nck != "" & met.y26.nck != "-") $then "Твой ник: {met.y26.nck}\n" $end'
    '$if (met.y26.nmb != "" & met.y26.nmb != "-") $then "Твой номер телефона: {met.y26.nmb}\n" $end'
    '$if (met.y26.way != "" & met.y26.way != "-") '
    '$then "Как добираешься до Ягодного: {met.y26.way}\n'
    'Важно: если ты решил поехать самостоятельно, вызови админа!\n" '
    '$end'
    "Берёшь ли ты постельное бельё: {met.y26.bed}\n"
    '$if (met.y26.liv != "" & met.y26.liv != "-" & met.y26.liv != "пока пусто") '
    '$then "Где ты живёшь: {met.y26.liv}\n" $end'
    '$if (fmt.y26_mates != "") $then "С кем ты живешь в этом домике: {fmt.y26_mates}\n" $end'
    "Получена ли оплата: {met.y26.chk}\n"
    "Что-то не так? Вызывай админа!"
)

Y25_INFO_TEMPLATE = (
    "Вот твои данные по выезду в Ягодное 2025!\n"
    '$if (met.y25.ugo == 0) $then "Едешь ли ты: Нет.\n" $end'
    '$if (met.y25.ugo == 1) $then "Едешь ли ты: Да, ты прошёл отбор, ждём оплату!\n" $end'
    '$if (met.y25.ugo == 2) $then "Едешь ли ты: Оплата дошла до нас, ты едешь!\n" $end'
    '$if (met.y25.ugo != 0 & met.y25.ugo != 1 & met.y25.ugo != 2) $then "Едешь ли ты: {met.y25.ugo}\n" $end'
    '$if (nck != "" & nck != "-") $then "Ник: {nck}\n" $else "Ник: [НЕТ ДАННЫХ]\n" $end'
    '$if (fio != "" & fio != "-") $then "ФИО: {fio}\n" $end'
    '$if (met.y25.nmb != "" & met.y25.nmb != "-") $then "Номер телефона: {met.y25.nmb}\n" $end'
    "Планируешь ли взять бельё в ягодном: {met.y25.bed}\n"
    '$if (met.y25.way == 0) $then "Как планируешь добираться до Ягодного: На бесплатном трансфере от ГК\n" $end'
    '$if (met.y25.way == 1) $then "Как планируешь добираться до Ягодного: Своим ходом (электричка)\n" $end'
    '$if (met.y25.way == 2) $then "Как планируешь добираться до Ягодного: Своим ходом (на машине)\n" $end'
    '$if (met.y25.way != 0 & met.y25.way != 1 & met.y25.way != 2) '
    '$then "Как планируешь добираться до Ягодного: {met.y25.way}\n" $end'
    '$if (met.y25.way == 2 & met.y25.car != "" & met.y25.car != "-") $then "Номер машины: {met.y25.car}\n" $end'
    '$if (met.y25.liv != "" & met.y25.liv != "-") '
    '$then "В каком домике ты живёшь: {met.y25.liv}\n" '
    '$else "В каком домике ты живёшь: [НЕТ ДАННЫХ]\n" $end'
)

A25_INFO_TEMPLATE = (
    "Данные по событию «Майнокиада осень 25»:\n"
    '$if (fio != "" & fio != "-") $then "ФИО: {fio}\n" $end'
    '$if (nck != "" & nck != "-") $then "Ник: {nck}\n" $end'
    '$if (met.a25.cmd != "" & met.a25.cmd != "-") $then "Команда: {met.a25.cmd}\n" $end'
    '$if (met.a25.cap != "" & met.a25.cap != "-") $then "Ник капитана: {met.a25.cap}\n" $end'
    '$if (met.a25.kbr != "" & met.a25.kbr != "-") $then "Киберарена: {met.a25.kbr}\n" $end'
    '$if (met.a25.stg != "" & met.a25.stg != "-") $then "Stage: {met.a25.stg}\n" $end'
    "Из ИТМО: {met.a25.sts}\n"
    "Раунд 1 пройден: {met.a25.wr1}\n"
    "Раунд 2 пройден: {met.a25.wr2}\n"
    "Раунд 3 пройден: {met.a25.wr3}\n"
    "Баллы: {met.a25.brs}"
)

S25_INFO_TEMPLATE = (
    "Вот твои данные за весеннюю Спартакиаду по Майнкрафту 2025!\n"
    '$if (isu >> 99999) $then "ИСУ: {isu}\n" $end'
    '$if (nck != "" & nck != "-") $then "Ник: {nck}\n" $else "Ник: [НЕТ ДАННЫХ]\n" $end'
    "Участвуешь ли ты в первом этапе (BlockParty): Да\n"
    "Проходишь ли в следующий этап (AceRace): {met.s25.wr1}\n"
    '$if (met.s25.rr1 != 0) $then "Поставят ли 10 баллов: Да\n" $else "Поставят ли 10 баллов: Нет\n" $end'
    "Рекорд раундов в BlockParty: {met.s25.rr1}\n"
    '$if (met.s25.wr1 != 0) $then "Рекорд в AceRace: {met.s25.rr2}\n" $end'
    "Проходишь ли ты в финал (SurvivalGames): {met.s25.wr2}\n"
    '$if (met.s25.wr2 != 0) $then "Место в финале: {met.s25.fnl}\n" $end'
    'Обязательно проверь данные, только в случае несоответствий напиши "АДМИН"'
)

A24_INFO_TEMPLATE = (
    "Вот твои данные за осеннюю Спартакиаду по Майнкрафту 2024!\n"
    '$if (nck != "" & nck != "-") '
    '$then "Ник: {nck}\n" '
    '$else "Ник: [НЕТ ДАННЫХ]\n" '
    '$end'
    "Участвуешь ли ты в первом этапе: Да\n"
    "Использовал ли ты все попытки: {met.a24.lr1}\n"
    "Проходишь ли в следующий этап: {met.a24.wr1}\n"
    "Поставят ли 10 баллов: {met.a24.lr1}\n"
    '$if (met.a24.wr1 != 0) '
    '$then "Проходишь ли ты в финал: {met.a24.wr2}\n" '
    '$end'
    "Ещё не отыграл в финале: {met.a24.nyt}\n"
    '$if (met.a24.wr2 != 0) '
    '$then "Победил ли в финале: {met.a24.fnl}\n" '
    '$end'
    'Обязательно проверь данные, только в случае несоответствий напиши "АДМИН"'
)