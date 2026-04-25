# ITMOcraftBOT (VK Bot)
VK bot for vk.com/itmocraft. Users are stored in **MySQL/MariaDB** (SQLAlchemy), not in a plain text file.

## Requirements
- Python 3.10+
- MySQL/MariaDB
- Real terminal (TTY) for interactive console tools

## Install
```bash
pip install -r source/requirements.txt
```

## Configuration
Create `.env` (gitignored) or export env vars:
```env
BOT_TOKEN=...
GROUP_ID=...
STORAGE_BACKEND=db
DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1:3306/vk_bot?charset=utf8mb4
```

## Run bot
```bash
python -m source.main
```

## Maintenance console
```bash
python -m source.utils.tools.console
```

What’s inside:
- **Users DB** — find/add/update/delete users
- **Import users.txt -> DB** — parse legacy file and merge it into DB (+ creates/updates Fix panel)
- **Reset DB** — drop bot tables (double confirm)
- **Fix panel** — review/fix flagged rows (`users_raw_lines`) + apply to mark row as fixed
- **DB stats** — compact summary + top fix reasons

### Import (users.txt -> DB)
```bash
python -m source.utils.tools.cli.migrate_from_txt
```

With explicit paths:
```bash
python -m source.utils.tools.cli.migrate_from_txt \
  --db-url 'mysql+pymysql://user:pass@127.0.0.1:3306/vk_bot?charset=utf8mb4' \
  --users-txt source/subscribers/users.txt
```

Rules:
- Rows are merged into normalized tables (`users` + event tables).
- Existing event data is not deleted just because the incoming `users.txt` row does not contain that event key.
- Known current event keys use typed tables: `a24`, `s25`, `y25`, `a25`.
- Legacy/future event keys that do not have a typed table, for example `s24` or `y24`, are stored as-is in `user_events` and returned back in `met` under the same key.
- If a DB user already has `a25`, legacy import keeps the DB base fields (`uid`, `fio`, `grp`, `nck`) as newer data unless the incoming row itself contains `a25`.
- Rows that need attention are additionally stored in `users_raw_lines` and appear in Fix panel (examples: uid=0/1, unusual grp, invalid nck, invalid met_json).
- `verify_import` checks that DB state matches the classification rules.

### Import in Docker
Find the bot service name:
```bash
docker compose ps
```

If the bot container is already running:
```bash
docker compose cp ./users.txt <bot-service>:/app/source/subscribers/users.txt

docker compose exec <bot-service> python -m source.utils.tools.cli.migrate_from_txt \
  --users-txt /app/source/subscribers/users.txt
```

If the container does not already have DB env variables:
```bash
docker compose exec \
  -e STORAGE_BACKEND=db \
  -e DATABASE_URL='mysql+pymysql://user:pass@mariadb:3306/vk_bot?charset=utf8mb4' \
  <bot-service> \
  python -m source.utils.tools.cli.migrate_from_txt \
  --users-txt /app/source/subscribers/users.txt
```

If the bot container is not running:
```bash
docker compose run --rm \
  -v "$PWD/users.txt:/app/source/subscribers/users.txt:ro" \
  <bot-service> \
  python -m source.utils.tools.cli.migrate_from_txt \
  --users-txt /app/source/subscribers/users.txt
```

Before importing production data, make a DB dump:
```bash
docker compose exec <db-service> mysqldump -u <db-user> -p <db-name> > vk_bot_before_legacy_merge.sql
```

### Fix panel
Picker:
```bash
python -m source.utils.tools.cli.raw_pick
```

Editor:
```bash
python -m source.utils.tools.cli.raw_edit <raw_id>
```

A row disappears from Fix panel only after it becomes valid for current rules and is marked as `status=ok`.

### Verify import
```bash
python -m source.utils.tools.cli.verify_import
```

## Sender (admin broadcast)
Sender is an admin command handled by the bot (see `source/bot.py`).

Syntax:
```text
sender <condition> <message>
```

Operators:
- `&` — AND
- `|` — OR
- `->` — key exists
- `!>` — key does NOT exist
- `==`, `!=`, `>>`, `>=`, `<<`, `<=` — comparisons

Fields:
- Base: `isu`, `uid`, `fio`, `grp`, `nck`
- Met fields: `met.<event>.<key>` (events like `s24`, `a24`, `s25`, `y25`, `a25`)

Example:
```text
sender met.y25.ugo==2 Привет! Ты едешь в Ягодное.
```

Note:
- Users with `uid` 0/1 are skipped by sender (legacy semantics).

## Repo hygiene / secrets
- `.env` is gitignored.
- `source/subscribers/` is gitignored (local legacy data).
