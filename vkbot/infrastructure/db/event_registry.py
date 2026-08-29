from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from vkbot.config import settings
import vkbot.infrastructure.db.templates as templates

# хз, почему такое название у переменной, legacy хрень
SUBSCRIBERS_DIR = settings.base_dir / "vkbot" / "bot" / "subscribers"


@dataclass(frozen=True)
class FieldDef:
    """Описание одного поля ивента."""
    name: str
    type: str  # "int", "str", "bool"
    default: Any = None
    # Для sender/query: как отображать в условии
    label: str = ""  # человекочитаемое имя, например "Берёшь бельё"


@dataclass(frozen=True)
class EventDef:
    """Полная декларация ивента."""
    key: str
    title: str
    fields: tuple[FieldDef, ...]
    inject_url: str | None = None
    inject_file: str | None = None
    active: bool = True
    info_template: str | None = None

    @property
    def table_name(self) -> str:
        return f"user_{self.key}"

    @property
    def field_names(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.fields)

    def get_field(self, name: str) -> FieldDef | None:
        for f in self.fields:
            if f.name == name:
                return f
        return None


# ============================================================
# РЕЕСТР: все ивенты описаны здесь
# ============================================================

EVENT_REGISTRY: dict[str, EventDef] = {}


def register_event(event: EventDef) -> EventDef:
    """Регистрирует ивент в глобальном реестре."""
    EVENT_REGISTRY[event.key] = event
    return event


def get_event(key: str) -> EventDef | None:
    return EVENT_REGISTRY.get(key)


def get_all_events() -> list[EventDef]:
    return list(EVENT_REGISTRY.values())


def get_active_events() -> list[EventDef]:
    return [e for e in EVENT_REGISTRY.values() if e.active]


# ============================================================
# ОПРЕДЕЛЕНИЯ ИВЕНТОВ
# ============================================================

register_event(EventDef(
    key="e26",
    title="ЕГЭ по майнкрафту 26",
    active=False,
    inject_url="https://docs.google.com/spreadsheets/d/11aRURg_RU-WwaMs19xh5yE-_epG8Ea5fW-N8HGKBFZc/export?format=tsv&gid=938113370",
    inject_file=str(SUBSCRIBERS_DIR / "e26.txt"),
    fields=(
        FieldDef("uid", "int", 0, label="VK ID"),
        FieldDef("fio", "str", "", label="ФИО"),
        FieldDef("nck", "str", "", label="Ник"),
        FieldDef("clk", "str", "", label="Время сдачи"),
        FieldDef("sum", "int", 0, label="Баллы (вторичные)"),
        FieldDef("plc", "int", 0, label="Место"),
        # Задания z01..z20
        *(FieldDef(f"z{i:02d}", "int", 0, label=f"Баллы за {i:02d} задание") for i in range(1, 21)),
    ),
    info_template=templates.E26_INFO_TEMPLATE
))

register_event(EventDef(
    key="y26",
    title="Ягодное 2026",
    active=False,
    inject_url="https://docs.google.com/spreadsheets/d/15g_s2MciovUVVrDtj6y-u-I3SHZ5X7u3gLGPfHzTIPg/export?format=tsv&gid=1986446860",
    inject_file=str(SUBSCRIBERS_DIR / "y26.txt"),
    fields=(
        FieldDef("uid", "int", 0, label="VK ID"),
        FieldDef("fio", "str", "", label="ФИО"),
        FieldDef("nck", "str", "", label="Ник"),
        FieldDef("nmb", "str", "", label="Номер телефона"),
        FieldDef("bed", "bool", False, label="Берёшь бельё"),
        FieldDef("liv", "str", "", label="Домик"),
        FieldDef("way", "str", "", label="Как добираешься"),
        FieldDef("chk", "bool", False, label="Оплата получена"),
        FieldDef("cst", "int", 0, label="Стоимость"),
        FieldDef("ugo", "bool", False, label="Одобрен"),
    ),
    info_template=templates.Y26_INFO_TEMPLATE
))

register_event(EventDef(
    key="a25",
    title="Майнокиада осень 25",
    active=False,
    inject_file=str(SUBSCRIBERS_DIR / "a25.txt"),
    fields=(
        FieldDef("fio", "str", "", label="ФИО"),
        FieldDef("sts", "bool", False, label="Из ИТМО"),
        FieldDef("uid", "int", 0, label="VK ID"),
        FieldDef("nck", "str", "", label="Ник"),
        FieldDef("cmd", "str", "", label="Команда"),
        FieldDef("cid", "int", 0, label="VK капитана"),
        FieldDef("cap", "str", "", label="Ник капитана"),
        FieldDef("kbr", "str", "", label="Киберарена"),
        FieldDef("stg", "str", "", label="Stage"),
        FieldDef("wr1", "bool", False, label="Раунд 1 пройден"),
        FieldDef("wr2", "bool", False, label="Раунд 2 пройден"),
        FieldDef("wr3", "bool", False, label="Раунд 3 пройден"),
        FieldDef("brs", "bool", False, label="Баллы"),
    ),
    info_template=templates.A25_INFO_TEMPLATE
))

register_event(EventDef(
    key="y25",
    title="Ягодное 2025",
    inject_file=str(SUBSCRIBERS_DIR / "y25.txt"),
    active=False,
    fields=(
        FieldDef("tsp", "int", 0, label='Timestamp регистрации'),
        FieldDef("nck", "str", "", label="Ник"),
        FieldDef("nmb", "str", "", label="Номер телефона"),
        FieldDef("bed", "bool", False, label="Берёшь бельё"),
        FieldDef("way", "int", 0, label="Как добираешься"),
        FieldDef("car", "str", "", label="Номер машины"),
        FieldDef("liv", "str", "", label="Домик"),
        FieldDef("ugo", "int", 0, label="Одобрен"),
    ),
    info_template=templates.Y25_INFO_TEMPLATE
))

register_event(EventDef(
    key="s25",
    title="Спартакиада весна 25",
    inject_file=str(SUBSCRIBERS_DIR / "s25.txt"),
    active=False,
    fields=(
        FieldDef("tsp", "int", 0, label='Timestamp регистрации'),
        FieldDef("nck", "str", "", label="Ник"),
        FieldDef("wr1", "bool", False, label="Прошёл в AceRace"),
        FieldDef("rr1", "int", 0, label="Рекорд BlockParty"),
        FieldDef("wr2", "bool", False, label="Прошёл в финал"),
        FieldDef("rr2", "int", 0, label="Рекорд AceRace"),
        FieldDef("fnl", "int", 0, label="Место в финале"),
    ),
    info_template=templates.S25_INFO_TEMPLATE,
))

register_event(EventDef(
    key="a24",
    title="Спартакиада осень 24",
    inject_file=str(SUBSCRIBERS_DIR / "a24.txt"),
    active=False,
    fields=(
        FieldDef("tsp", "int", 0, label='Timestamp регистрации'),
        FieldDef("nck", "str", "", label="Ник"),
        FieldDef("lr1", "bool", False, label="Все попытки использованы"),
        FieldDef("wr1", "bool", False, label="Прошёл во 2 этап"),
        FieldDef("wr2", "bool", False, label="Прошёл в финал"),
        FieldDef("nyt", "bool", False, label="Ещё не отыграл финал"),
        FieldDef("fnl", "bool", False, label="Победил в финале"),
    ),
    info_template=templates.A24_INFO_TEMPLATE
))
