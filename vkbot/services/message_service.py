from __future__ import annotations

from vkbot.domain.user import User
from vkbot.domain.rules import is_real_isu, is_valid_uid
from vkbot.infrastructure.db.event_registry import EventDef, get_event


class MessageService:
    """
    Форматирование сообщений с conditional rendering.
    Заменяет все format_y26_message, format_e26_message и т.д.
    """

    def render_event_info(self, user: User, event_key: str) -> str:
        """
        Форматирует данные юзера по ивенту.
        Возвращает готовое сообщение или пустую строку если данных нет.
        """
        event_def = get_event(event_key)
        if event_def is None:
            return ""

        event_data = user.get_event_data(event_key)
        if not event_data:
            return ""

        # Для каждого ивента — свой шаблон
        template_fn = getattr(self, f"_format_{event_key}", None)
        if template_fn:
            return template_fn(user, event_data)

        # Generic fallback: показываем все непустые поля
        return self._format_generic(user, event_def, event_data)

    def _format_generic(self, user: User, event_def: EventDef, data: dict) -> str:
        """Универсальное форматирование для ивентов без кастомного шаблона."""
        parts = [f"Данные по событию «{event_def.title}»:\n"]

        for field_def in event_def.fields:
            value = data.get(field_def.name)
            if not self._should_show(field_def.name, value):
                continue

            label = field_def.label or field_def.name
            display = self._display_value(value, field_def.type)
            parts.append(f"{label}: {display}")

        return "\n".join(parts)

    # ----------------------------------------------------------
    # Кастомные шаблоны для конкретных ивентов
    # ----------------------------------------------------------

    def _format_y26(self, user: User, data: dict) -> str:
        parts = ["Привет! Вот твои данные по выезду в Ягодное:"]

        nck = data.get("nck", "")
        nmb = data.get("nmb", "")
        way = data.get("way", "")
        bed = data.get("bed", False)
        liv = data.get("liv", "")
        chk = data.get("chk", False)

        if nck and nck != "-":
            parts.append(f"\nТвой ник: {nck}")

        if nmb and nmb != "-":
            parts.append(f"\nТвой номер телефона:\n{nmb}")

        if way and way != "-":
            parts.append(f"\nКак добираешься до Ягодного:\n{way}")
            parts.append("Важно: если ты решил поехать самостоятельно, вызови админа!")

        parts.append(f"\nБерёшь ли ты постельное бельё: {self._b2t(bed)}")

        if liv and liv != "-" and liv.lower() != "пока пусто":
            parts.append(f"\nГде ты живёшь:\n{liv}")

        parts.append(f"\nПолучена ли оплата: {self._b2t(chk)}")
        parts.append("\nЧто-то не так? Вызывай админа!")

        return "\n".join(parts)

    def _format_e26(self, user: User, data: dict) -> str:
        fio = data.get("fio", "")
        nck = data.get("nck", "")
        clk = data.get("clk", "")
        sum_score = data.get("sum", 0)
        plc = data.get("plc", 0)

        name = fio.split()[0] if fio else "участник"
        parts = [f"Привет, {name}!", "ЕГЭ по майнкрафту — инфа ниже:"]

        if fio:
            parts.append(f"Твоё ФИО: {fio}")
        if nck:
            parts.append(f"Твой ник: {nck}")

        if not clk:
            parts.append("")
            parts.append("По нашей информации, тебя не было :(")
            return "\n".join(parts)

        parts.append(f"Время сдачи: {clk}")

        for i in range(1, 21):
            key = f"z{i:02d}"
            val = data.get(key, 0)
            parts.append(f"Задание {i}: {val}")

        parts.append(f"Итого баллов (вторичных): {sum_score}")

        if plc and plc > 0:
            parts.append(f"Твоё место: {plc}")
        else:
            parts.append("К сожалению, ты не занял призовое место")

        return "\n".join(parts)

    def _format_a25(self, user: User, data: dict) -> str:
        parts = ["Вот твои данные за Майнокиаду!"]

        nck = data.get("nck", "")
        cmd = data.get("cmd", "")
        cap = data.get("cap", "")
        kbr = data.get("kbr", "")
        stg = data.get("stg", "")
        wr1 = data.get("wr1", False)

        if nck:
            parts.append(f"\nНик: {nck}")
        if cmd:
            parts.append(f"\nКоманда: {cmd}")
        if cap:
            parts.append(f"\nКапитан: {cap}")

        if wr1:
            stage_display = stg if stg and stg != "-" else "[НЕ НАЗНАЧЕН]"
            parts.append(f"\nТвой турнирный матч (stage): {stage_display}")

        if kbr and kbr != "-":
            parts.append(f"\nЧасы на киберарене: {kbr}")

        parts.append("\nОбязательно проверь данные. Если что-то не так — напиши АДМИН")
        return "\n".join(parts)

    # ----------------------------------------------------------
    # Welcome message
    # ----------------------------------------------------------

    def build_welcome_text(self) -> str:
        return (
            "Привет! Мы клуб любителей Майнкрафта ITMOcraft 🎮\n\n"
            "Нажми на кнопки ниже, чтобы узнать информацию о текущих событиях.\n"
            "Если есть вопросы — напиши АДМИН."
        )

    def build_subscribe_message(self) -> str:
        return (
            "Привет! Для получения информации подпишись на группу:\n"
            "https://vk.com/itmocraft\n"
            "После подписки отправь ещё одно сообщение."
        )

    # ----------------------------------------------------------
    # Хелперы
    # ----------------------------------------------------------

    @staticmethod
    def _b2t(value) -> str:
        if isinstance(value, bool):
            return "Да" if value else "Нет"
        if isinstance(value, str):
            return "Да" if value.lower() in ("1", "true", "yes", "да") else "Нет"
        return "Да" if value else "Нет"

    @staticmethod
    def _should_show(field_name: str, value) -> bool:
        """Определяет, показывать ли поле."""
        if field_name == "isu":
            return isinstance(value, int) and is_real_isu(value)
        if field_name == "uid":
            return isinstance(value, int) and is_valid_uid(value)
        if isinstance(value, str):
            return bool(value.strip()) and value.strip() != "-"
        if isinstance(value, bool):
            return True  # bool всегда показываем
        if isinstance(value, int):
            return True  # int всегда показываем
        return value is not None

    @staticmethod
    def _display_value(value, field_type: str) -> str:
        if isinstance(value, bool):
            return "Да" if value else "Нет"
        return str(value)
