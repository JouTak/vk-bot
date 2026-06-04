# ITMOcraft VK Bot — Архитектура

VK бот для клуба любителей Майнкрафта ИТМО (vk.com/itmocraft).

## Стек

- **Python 3.10+**
- **vk_api** — VK Bot LongPoll API
- **SQLAlchemy** — ORM (MySQL/MariaDB или файловый fallback)
- **dotenv** — конфигурация через .env

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен VK бота |
| `GROUP_ID` | ID группы VK |
| `STORAGE_BACKEND` | `db` или `file` (по умолчанию `file`) |
| `DATABASE_URL` | MySQL connection string |
| `USERS_TXT_PATH` | Путь к users.txt (для file backend) |
| `IGNORED_TXT_PATH` | Путь к ignored.txt |
| `LOG_PATH` | Путь к лог-файлу |

## Структура файлов

```
source/
├── main.py                    # Точка входа, longpoll цикл, админ-команды
├── bot.py                     # Обработчики сообщений, sender DSL
├── templates/                 # Шаблоны welcome-сообщений
│   ├── current.txt            # Имя активного шаблона
│   ├── default.txt            # Дефолтное сообщение
│   ├── a25.txt                # Майнокиада осень 2025
│   └── y26.txt                # Ягодное 2026
└── utils/
    ├── __init__.py            # initialize() — загрузка env
    ├── vk_helper.py           # VKHelper — обёртка VK API
    ├── templates.py           # Система шаблонов сообщений
    ├── ignored_list.py        # IgnoredList — список "в поддержке"
    ├── query_helper.py        # MinecraftServerQuery (mcipc)
    ├── log.py                 # Логгирование
    ├── json_worker.py
    ├── db/
    │   ├── db.py              # init_engine(), session_scope()
    │   ├── models.py          # SQLAlchemy модели
    │   └── repositories.py    # UserRepository, IgnoredRepository
    ├── storage/
    │   ├── user_store.py      # User, UserList классы
    │   ├── user_list.py       # (legacy, не используется)
    │   └── inject_y26.py      # Инъекция Y26 из Google Sheets
    └── tools/cli/             # CLI утилиты для миграции/отладки
```

## Модель данных

### Основная таблица `users`

| Поле | Тип | Описание |
|------|-----|----------|
| `isu` | INT PK | ИСУ студента (0-99999 для внешних) |
| `uid` | BIGINT | VK user ID (0=нет, 1=не распознан) |
| `fio` | VARCHAR(255) | ФИО |
| `grp` | VARCHAR(64) | Группа (A1234) |
| `nck` | VARCHAR(64) | Ник в Minecraft |

### Таблицы событий

Каждое событие хранится в отдельной типизированной таблице с FK на `users.isu`:

- **`user_a24`** — Осенняя Спартакиада 2024
- **`user_s25`** — Весенняя Спартакиада 2025
- **`user_y25`** — Ягодное 2025
- **`user_a25`** — Майнокиада (осень 2025)
- **`user_y26`** — Ягодное 2026

#### Поля Y26 (user_y26)

| Поле | Тип | Описание |
|------|-----|----------|
| `uid` | BIGINT | VK ID |
| `fio` | VARCHAR | ФИО |
| `nck` | VARCHAR | Ник |
| `nmb` | VARCHAR | Номер телефона |
| `bed` | BOOL | Берёт бельё |
| `liv` | VARCHAR | Домик |
| `way` | VARCHAR | Способ добраться |
| `chk` | BOOL | Оплата получена |
| `cst` | INT | Стоимость |
| `ugo` | BOOL | Одобрен (едет) |

### Класс User

```python
class User:
    info = (isu, uid, fio, grp, nck, met)  # tuple
    met = {"a24": {...}, "y26": {...}}     # dict событий
```

## Админ-команды

Отправляются в ЛС боту от админов (UIDs: 297002785, 325899178, 229488682, 304032635):

| Команда | Описание |
|---------|----------|
| `stop` | Остановить бота |
| `reload` | Перезагрузить users + Y26 inject |
| `db <SQL>` | Выполнить произвольный SQL |
| `migrate [path]` | Миграция из users.txt в БД |
| `query <условие>` | Найти юзеров по условию (без рассылки) |
| `sender <условие> <сообщение>` | Массовая рассылка |
| `add_users <uid1> <uid2>...` | Добавить юзеров по VK ID |
| `message` | Показать текущий шаблон welcome-сообщения |
| `message <name>` | Сменить шаблон (y26, a25, default...) |

## Система шаблонов

Шаблоны welcome-сообщений хранятся в `source/templates/*.txt`.

- `current.txt` — содержит имя активного шаблона (например `y26`)
- Шаблоны поддерживают плейсхолдеры: `{itmocraft_ip}`, `{joutak_link}`, `{form_link}`, `{telegram_link}`, `{discord_link}`, `{a25_reg_link}`

### Использование

```
message           → показывает текущий шаблон и список доступных
message y26       → переключает на templates/y26.txt
message default   → переключает на templates/default.txt
```

## Sender DSL

Язык условий для `query` и `sender`:

### Операторы

| Оператор | Значение |
|----------|----------|
| `\|` | ИЛИ |
| `&` | И |
| `->` | Событие существует |
| `!>` | Событие НЕ существует |
| `==` `!=` | Равно / не равно |
| `>>` `>=` `<<` `<=` | Сравнение |

### Поля

- Базовые: `isu`, `uid`, `fio`, `grp`, `nck`
- Вложенные: `met.<event>.<field>` (например `met.a25.wr1`)

### Примеры

```
# Участники A25 с командой
met.a25.wr1==1&met.a25.cmd!=

# Есть событие Y26
y26->met

# Обычные ИСУ (не внешние)
isu>=100000

# Без Y26 или не одобрен
y26!>met|met.y26.ugo==0
```

## Inject-паттерн (inject_y26)

1. Fetch TSV из Google Sheets (fallback на локальный файл)
2. Parse header для маппинга колонок
3. Resolve VK ссылки через `vk_helper.links_to_uids()`
4. Upsert в БД через `UserRepository`
5. Удаление записей, отсутствующих в таблице

Запускается:
- При старте бота
- По команде `reload`

## Обработка сообщений

### Приватные сообщения (не из чата)

1. **Админ-команды** — если отправитель в списке админов
2. **Ignored режим** — если юзер уже вызвал админа, сообщения пробрасываются
3. **"АДМИН"** — toggle режима поддержки, уведомление админам
4. **Вложения** — предупреждение о необходимости вызвать админа
5. **Y26 участник** — показ данных по выезду (`format_y26_message`)
6. **Подписчик** — welcome сообщение
7. **Не подписчик** — просьба подписаться

### Сообщения из чата

- `/ping` — статус сервера JouTak (mcipc query)

## VKHelper

Ключевые методы:

```python
vk_helper.send_message(peer_id, message, keyboard=None, attachment=None)
vk_helper.send_messages(messages: list[dict])  # batch через execute
vk_helper.links_to_uids(links: list[str]) -> list[int]  # resolve VK ссылок
```

## Обработка ошибок в main.py

```python
while True:
    try:
        bot.run()
    except requests.exceptions.ReadTimeout:
        pass  # Нормально, переподключение
    except (ConnectionError, MaxRetryError, RemoteDisconnected, OSError):
        print(...)  # Логируем, переподключаемся
    except Exception as e:
        bot.error(e)
        # Уведомление админам
```

## Типичные задачи

### Добавить новое событие (например Y27)

1. Создать модель `UserY27Model` в `models.py`
2. Добавить в `KNOWN_EVENT_KEYS` в `repositories.py`
3. Добавить upsert логику в `UserRepository.upsert()`
4. Добавить в `User.text2info` и `User.info2text` в `user_store.py`
5. Создать `inject_y27.py` по аналогии с `inject_y26.py`
6. Добавить вызов в `main.py` при старте и `reload`

### Добавить админ-команду

В `bot.py` → `process_message_new()` → блок `if uid in admin and msgs:`

### Изменить welcome-сообщение

В `bot.py` — переменные `hi_message`, `y26_welcome_message`, `info_message`
