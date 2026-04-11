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
- **Import users.txt -> DB** — import legacy `source/subscribers/users.txt` into DB (+ creates/updates Fix panel)
- **Reset DB** — drop bot tables (double confirm)
- **Fix panel** — review/fix flagged rows (`users_raw_lines`) + apply to mark row as fixed
- **DB stats** — compact summary + top fix reasons

### Import (users.txt -> DB)
```bash
python -m source.utils.tools.cli.migrate_from_txt
```

Rules:
- Rows are upserted into normalized tables (`users` + event tables).
- Rows that need attention are additionally stored in `users_raw_lines` and appear in Fix panel (examples: uid=0/1, unusual grp, invalid nck, invalid met_json).
- `verify_import` checks that DB state matches the classification rules.

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
- Met fields: `met.<event>.<key>` (events like `a24`, `s25`, `y25`, `a25`)

Example:
```text
sender met.y25.ugo==2 Привет! Ты едешь в Ягодное.
```

Note:
- Users with `uid` 0/1 are skipped by sender (legacy semantics).

## Repo hygiene / secrets
- `.env` is gitignored.
- `source/subscribers/` is gitignored (local legacy data).
