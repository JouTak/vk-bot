from __future__ import annotations

from sqlalchemy import select
from vkbot.domain.user import User
from vkbot.domain.rules import is_real_isu, is_valid_uid
from vkbot.infrastructure.db.event_registry import EventDef, get_event
from vkbot.infrastructure.db.engine import session_scope
from vkbot.infrastructure.db.models import get_event_model


class MessageService:
    """
    Форматирование сообщений с conditional rendering.
    Заменяет все format_y26_message, format_e26_message и т.д.
    """
    WAY2TEXT = ("На бесплатном трансфере от ГК", "Своим ходом (электричка)", "Своим ходом (на машине)")
    UGO2TEXT = ("Нет.", "Да, ты прошёл отбор, ждём оплату!", "Оплата дошла до нас, ты едешь!")

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
            mates = self._get_y26_house_mates(liv, user.isu)
            if mates:
                parts.append(f"\nС кем ты живешь в этом домике:\n{mates}")

        parts.append(f"\nПолучена ли оплата: {self._b2t(chk)}")
        parts.append("\nЧто-то не так? Вызывай админа!")

        return "\n".join(parts)

    def _format_y25(self, user: User, data: dict) -> str:
        parts = ["Вот твои данные по выезду в Ягодное 2025!"]
        parts.append(f"Едешь ли ты: {self._safe_pick(self.UGO2TEXT, data.get('ugo', 0), str(data.get('ugo', '')))}")
        parts.append(f"Ник: {user.nck or data.get('nck') or '[НЕТ ДАННЫХ]'}")
        if user.fio:
            parts.append(f"ФИО: {user.fio}")
        nmb = data.get("nmb", "")
        if nmb and nmb != "-":
            parts.append(f"Номер телефона: {nmb}")
        parts.append(f"Планируешь ли взять бельё в ягодном: {self._b2t(data.get('bed', False))}")
        way = data.get("way", 0)
        parts.append(f"Как планируешь добираться до Ягодного: {self._safe_pick(self.WAY2TEXT, way, str(way))}")
        if int(way or 0) == 2:
            car = data.get("car", "")
            if car and car != "-":
                parts.append(f"Номер машины: {car}")
        liv = data.get("liv", "")
        parts.append(f"В каком домике ты живёшь: {liv or '[НЕТ ДАННЫХ]'}")
        return "\n".join(parts)

    def _format_s25(self, user: User, data: dict) -> str:
        parts = ["Вот твои данные за весеннюю Спартакиаду по Майнкрафту 2025!"]
        parts.append(f"ИСУ: {user.isu}")
        parts.append(f"Ник: {user.nck or data.get('nck') or '[НЕТ ДАННЫХ]'}")
        parts.append("Участвуешь ли ты в первом этапе (BlockParty): Да")
        parts.append(f"Проходишь ли в следующий этап (AceRace): {self._b2t(data.get('wr1', False))}")
        parts.append(f"Поставят ли 10 баллов: {self._b2t(data.get('rr1', 0) != 0)}")
        parts.append(f"Рекорд раундов в BlockParty: {data.get('rr1', 0)}")
        if data.get("wr1"):
            parts.append(f"Рекорд в AceRace: {data.get('rr2', 0)}")
            parts.append(f"Проходишь ли ты в финал (SurvivalGames): {self._b2t(data.get('wr2', False))}")
        if data.get("wr2"):
            parts.append(f"Место в финале: {data.get('fnl', 0)}")
        parts.append('Обязательно проверь данные, только в случае несоответствий напиши "АДМИН"')
        return "\n".join(parts)

    def _format_a24(self, user: User, data: dict) -> str:
        parts = ["Вот твои данные за осеннюю Спартакиаду по Майнкрафту 2024!"]
        parts.append(f"Ник: {user.nck or data.get('nck') or '[НЕТ ДАННЫХ]'}")
        parts.append("Участвуешь ли ты в первом этапе: Да")
        parts.append(f"Использовал ли ты все попытки: {self._b2t(data.get('lr1', False))}")
        parts.append(f"Проходишь ли в следующий этап: {self._b2t(data.get('wr1', False))}")
        parts.append(f"Поставят ли 10 баллов: {self._b2t(data.get('lr1', False))}")
        if data.get("wr1"):
            parts.append(f"Проходишь ли ты в финал: {self._b2t(data.get('wr2', False))}")
            parts.append(f"Ещё не отыграл в финале: {self._b2t(data.get('nyt', False))}")
        if data.get("wr2"):
            parts.append(f"Победил ли в финале: {self._b2t(data.get('fnl', False))}")
        parts.append('Обязательно проверь данные, только в случае несоответствий напиши "АДМИН"')
        return "\n".join(parts)

    # ----------------------------------------------------------
    # Welcome message
    # ----------------------------------------------------------

    def build_welcome_text(self, has_events: bool = True) -> str:
        if has_events:
            return (
                "Привет! Мы клуб любителей Майнкрафта ITMOcraft 🎮\n"
                "Нажми на кнопки ниже, чтобы узнать информацию о событиях.\n"
                "Если есть вопросы — напиши АДМИН."
            )

        return (
            "Привет! Мы клуб любителей Майнкрафта ITMOcraft 🎮\n"
            "Пока у тебя нет событий с доступными данными.\n"
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
    def _get_y26_house_mates(house: str, exclude_isu: int) -> str:
        if not house or house.strip().lower() in ("", "-", "пока пусто"):
            return ""
        model = get_event_model("y26")
        if model is None:
            return ""

        with session_scope() as s:
            rows = s.execute(select(model).where(model.liv != "")).scalars().all()
            # Сразу материализуем все нужные поля ВНУТРИ сессии
            data = [
                (r.isu, (r.liv or "").strip().lower(), (r.nck or "").strip())
                for r in rows
            ]

        # Теперь сессия закрыта, но у нас обычные tuples — безопасно
        house_lower = house.strip().lower()
        mates = sorted(
            nck for isu, liv, nck in data
            if isu != exclude_isu
            and liv == house_lower
            and nck not in ("", "-")
        )
        return ", ".join(mates)

    @staticmethod
    def _safe_pick(mapping: tuple[str, ...], idx, fallback: str = "") -> str:
        try:
            return mapping[int(idx)]
        except (IndexError, ValueError, TypeError):
            return fallback

    @staticmethod
    def _b2t(value) -> str:
        if isinstance(value, bool):
            return "Да" if value else "Нет"
        if isinstance(value, str):
            return "Да" if value.lower() in {"1", "true", "yes", "да"} else "Нет"
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
