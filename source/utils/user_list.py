from utils.json_worker import *
from datetime import datetime
import re

users_path = './subscribers/users.txt'
warnings = []


def warn(*s: str) -> None:
    warnings.append('Warning: ' + ' '.join(s))
    # print('Warning:', *s)


def s2t(s: str) -> int:
    # Convert date string to UNIX timestamp
    return int(datetime.strptime(s, '%m/%d/%Y %H:%M:%S').timestamp())


def t2s(timestamp: int) -> str:
    # Convert UNIX timestamp to formatted date string
    return datetime.fromtimestamp(timestamp).strftime('%m/%d/%Y %H:%M:%S')


class User:
    # User info structure as a tuple with fields:
    # isu, uid, fio, grp, nck, met: {
    # a24: {tsp, nck, lr1, wr1, wr2, nyt, fnl},
    # s25: {tsp, nck, wr1, rr1, wr2, rr2, fnl},
    # y25: {tsp, nck, nmb, bed, way, car, liv, ugo}}
    # a25: {fio, sts, uid, nck, cmd, cid, wr1, wr2, wr3, brs}
    info_type = tuple[int, int, str, str, str, dict[str: dict[str: str | int | bool]]]
    s2b = lambda s: s == '1'  # ('0', '1') -> (False, True)
    load2info = (int, int, str, str, str, json.loads)

    # Conversion functions for parsing text fields to proper typed user info
    text2info = (int, int, str, str, str, {
        'a24': {'tsp': int, 'nck': str, 'lr1': s2b, 'wr1': s2b, 'wr2': s2b, 'nyt': s2b, 'fnl': s2b},
        's25': {'tsp': int, 'nck': str, 'wr1': s2b, 'rr1': str, 'wr2': s2b, 'rr2': str, 'fnl': str},
        'y25': {'tsp': int, 'nck': str, 'nmb': str, 'bed': s2b, 'way': int, 'car': str, 'liv': str, 'ugo': int},
        'a25': {'fio': str, 'sts': s2b, 'uid': int, 'nck': str, 'cmd': str, 'cid': int, 'cap': str, 'kbr': str,
                'wr1': s2b, 'stg2': str, 'wr2': s2b, 'wr3': s2b, 'brs': s2b}})

    # Checks for parsing validity: text to int and text to bool validators (checkers) (t2ic = Text to Int Checker)
    t2ic = str.isdigit
    t2bc = ['0', '1'].__contains__
    # Validators (checkers) for correctness of conversion from text to info fields
    text2info_check = (t2ic, t2ic, bool, bool, bool, {
        'a24': {'tsp': t2ic, 'nck': bool, 'lr1': t2bc, 'wr1': t2bc, 'wr2': t2bc, 'nyt': t2bc, 'fnl': t2bc},
        's25': {'tsp': t2ic, 'nck': bool, 'wr1': t2bc, 'rr1': t2ic, 'wr2': t2bc, 'rr2': t2ic, 'fnl': t2ic},
        'y25': {'tsp': t2ic, 'nck': bool, 'nmb': bool, 'bed': t2bc, 'way': t2ic, 'car': bool, 'liv': bool, 'ugo': t2ic},
        'a25': {'fio': bool, 'sts': t2bc, 'uid': t2ic, 'nck': bool, 'cmd': bool, 'cid': t2ic, 'cap': bool, 'kbr': bool,
                'wr1': t2bc, 'stg2': bool, 'wr2': t2bc, 'wr3': t2bc, 'brs': t2bc}})

    # bool to text
    b2t = lambda b: 'Да' if b else 'Нет'
    # Translates 'way' integer codes to string descriptions
    w2t = ('На бесплатном трансфере от ГК', 'Своим ходом (электричка)', 'Своим ходом (на машине)').__getitem__
    # String display helper: converts falsy to '[НЕТ ДАННЫХ]' (opt = optional)
    opt = lambda x: x if (x and x != '-') else '[НЕТ ДАННЫХ]'
    # Cyberarena hours: empty -> 'не отыграны', otherwise show text as-is
    kbr2t = lambda x: x if (x and x != '-') else 'не отыграны'
    # Converts 'ugo' status integer codes to textual descriptions
    u2t = ('Нет.', 'Да, ты прошёл отбор, ждём оплату!', 'Оплата дошла до нас, ты едешь!').__getitem__
    # Functions to convert user info fields to text representations, including nested metadata
    info2text = (str, str, str, str, str, {
        'a24': {'tsp': t2s, 'nck': opt, 'lr1': b2t, 'wr1': b2t, 'wr2': b2t, 'nyt': b2t, 'fnl': b2t},
        's25': {'tsp': t2s, 'nck': opt, 'wr1': b2t, 'rr1': opt, 'wr2': b2t, 'rr2': opt, 'fnl': opt},
        'y25': {'tsp': t2s, 'nck': opt, 'nmb': opt, 'bed': b2t, 'way': w2t, 'car': opt, 'liv': opt, 'ugo': u2t},
        'a25': {'fio': opt, 'sts': b2t, 'uid': opt, 'nck': opt, 'cmd': opt, 'cid': opt, 'cap': opt, 'kbr': kbr2t,
                'wr1': b2t, 'stg2': opt, 'wr2': b2t, 'wr3': b2t, 'brs': b2t}})

    # (False, True) -> ('0', '1')
    b2s = lambda b: '1' if b else '0'
    # Functions used to serialize user info for saving, including JSON dump for metadata
    db2save = (str, str, str, str, str, lambda x: json.dumps(x, ensure_ascii=False))

    # List of main user info keys consistent with info tuple indexes
    keys = ('isu', 'uid', 'fio', 'grp', 'nck', 'met')
    # Placeholder for flat mapping of info keys to text, initialized elsewhere
    flat_i2t: dict[str]

    def __init__(self, info: tuple[int, int, str, str, str, dict[str: dict[str: str | int | bool]]]) -> None:
        self.info = info

    def __getitem__(self, key: str) -> int | str | dict | None:
        # Allows indexing by key name to access corresponding info tuple element
        return self.info[User.keys.index(key)] if key in User.keys else None

    def __getattribute__(self, key: str) -> int | str | dict | None:
        # Overrides attribute access to return info elements by key name, except for 'info' attribute itself
        return super().__getattribute__(key) if key == 'info' else \
            (self.info[User.keys.index(key)] if key in User.keys else None)


class UserList:
    """
   Manages a collection of User objects loaded from a file.

   The database stores user info with fields:
   isu, uid, fio, grp, nck, and nested metadata dictionaries like a24, s25, etc.

   Attributes:
       db (dict[int, User]): Maps isu (unique user id) to User objects.
       uid_to_isu (dict[int, int]): Maps vk uid to isu for fast access.
       errors (list[tuple[str]]): List of malformed or problematic data rows.
       path (str): File path for the user database.
       vk_helper: Helper object for interacting with VK API.
       max_special_isu (int): Counter for assigning special ISU IDs.
       used_specials_isus (set[int]): Set of special ISU IDs already assigned.
    """

    def __init__(self, path: str, vk_helper) -> None:
        """
        Initialize UserList, attempt to load the database from file.
        DB: isu, uid, fio, grp, nck, {a24: {...}, s25: {...}, ...}

        Raises:
            OSError: If loading fails, indicating problems with the DB file.
        """
        self.db = dict[int: User]()
        self.uid_to_isu = dict[int: int]()  # uid: isu
        self.errors = list[tuple[str]]()
        self.path = path
        self.vk_helper = vk_helper
        self.max_special_isu = 0
        self.used_specials_isus = set()
        if self.load() is False:
            raise OSError('Something went wrong while loading DB')

    def load(self) -> bool:
        """
        Load and process the user database file, correcting inconsistencies.

        Performs validation on each line, fixes invalid IDs, resolves VK UIDs via API,
        removes deprecated metadata fields, and rebuilds lookup dictionaries.

        Returns:
            bool: True on successful load and save (if needed), False on file access failure.
        """
        inject_a25(self.vk_helper)

        if is_file_accessible(self.path) is False:
            return False
        self.db.clear()

        changes = False
        incorrect_uids = list[tuple[str]]()
        incorrect_isus = list[tuple[str]]()

        def parse_line(n: int, s: tuple[str, ...]) -> tuple | None:
            """
            Validate and parse a line of user data.

            Returns:
                tuple: Parsed and typed user info if valid.
                None: If line is invalid or to be skipped.
            """
            nonlocal changes
            result = [0, 0, '', '', '', {}]
            if not s or len(s) != 6:
                warn(f'empty {n}-th line in DB')
            if not s[0] or not all(d.isdigit() for d in s[0]):
                warn(f'isu id is NaN in {n}-th line in DB: {s[0]}')
                incorrect_isus.append(s)
                changes = True
            else:
                result[0] = int(s[0])
            if not 100000 <= result[0] <= 999999:
                self.used_specials_isus.add(result[0])
            if not all(d.isdigit() for d in s[1]):
                warn(f'vk id is NaN (isu = {s[0]}) in {n}-th line in DB:', s[1])
                incorrect_uids.append(s)
                result[1] = -1
                changes = True
            else:
                result[1] = int(s[1])
            # Skip rows with invalid UIDs (0 or 1)
            if 0 <= result[1] <= 1:
                self.errors.append(s)
                if s in incorrect_isus:
                    incorrect_isus.remove(s)
                if s in incorrect_uids:
                    incorrect_uids.remove(s)
                return None
            if len(s[2].split()) != 3:  # Check correct fio format
                # warn(f'something wrong with fio (isu = {s[0]}) in {n}-th line in DB:', s[2])
                pass
            result[2] = s[2]
            result[3] = s[3]
            result[4] = s[4]
            if is_json(s[5]) is False:
                warn(f'something wrong with meta info (isu = {s[0]}) in {n}-th line in DB:', s[5])
                self.errors.append(s)
                if s in incorrect_isus:
                    incorrect_isus.remove(s)
                if s in incorrect_uids:
                    incorrect_uids.remove(s)
                return None
            else:
                result[5] = json.loads(s[5])
            return tuple(result)

        # Read and parse each line of the DB file
        with open(self.path, 'r', encoding='UTF-8') as file:
            for n, line in enumerate(file):
                user_info = parse_line(n, line.split('\t'))
                if user_info is not None:
                    self.db[user_info[0]] = User(user_info)

        # Fix issues with incorrect ISU IDs by assigning new special ISU IDs
        for i in range(len(incorrect_isus)):
            corrected = list(incorrect_isus[i])
            corrected[0] = str(self.get_new_special_isu())
            incorrect_isus[i] = tuple(corrected)

        # Resolve incorrect VK UIDs by querying VK API in batches of 25
        for i in range(0, len(incorrect_uids), 25):
            part = [j[1] for j in incorrect_uids[i:i + 25]]
            response: list[str] = self.vk_helper.links_to_uids(part)
            for j, uid in zip(range(i, i + 25), response):
                user = list(incorrect_uids[j])
                user[1] = str(uid)
                incorrect_uids[j] = tuple(user)

        # Filter out obviously invalid VK UIDs
        for i in incorrect_uids:
            if i[1] == '0' or i[1] == '1':
                self.errors.append(i)
        incorrect_uids = [i for i in incorrect_uids if i[1] != '0' and i[1] != '1']

        # Merge records with both incorrect ISU and VK UID by matching other details
        for i in incorrect_isus:
            for j in incorrect_uids:
                if tuple(i[2:]) == tuple(j[2:]):
                    user_info = parse_line(0, (i[0], j[1], i[2], i[3], i[4], i[5]))
                    self.db[i[0]] = User(user_info)
        incorrect_isus = [i for i in incorrect_isus if not any(tuple(i[2:]) == tuple(j[2:]) for j in incorrect_uids)]
        incorrect_uids = [i for i in incorrect_uids if not any(tuple(i[2:]) == tuple(j[2:]) for j in incorrect_isus)]

        # Add remaining corrected entries separately
        for s in incorrect_isus:
            user_info = parse_line(0, s)
            self.db[user_info[0]] = User(user_info)
        for s in incorrect_uids:
            user_info = parse_line(0, s)
            self.db[user_info[0]] = User(user_info)

        # Fast lookup map from VK UID to ISU ID, skipping invalid UIDs
        for isu in self.db.keys():
            user = self.db[isu]
            if not (0 <= user.uid <= 1):
                self.uid_to_isu[user.uid] = isu

        # TODO: Remove deprecated metadata keys soon
        for isu in self.db.keys():
            user = self.db[isu]
            if 'y24' in user.met.keys():
                user.met['a24'] = user.met['y24'].copy()
                del user.met['y24']
            if 'y25' in user.met.keys():
                y25 = user.met['y25']
                for key in ('sts', 'why', 'jtk', 'gms', 'lgc', 'wsh'):
                    if key in y25.keys():
                        changes = True
                        del y25[key]
        # ------------------

        if changes is True:
            return self.save()
        return True

    def save(self) -> bool:
        """
        Persist the current database state to file.

        Returns:
            bool: True if the file was successfully written, False if file access failed.
        """
        if is_file_accessible(self.path) is False:
            return False
        to_save = []
        for isu in self.db.keys():
            to_save.append('\t'.join(f(i) for f, i in zip(User.db2save, self.db[isu].info)))
        to_save.extend(map('\t'.join, self.errors))
        to_save.sort(key=lambda x: int(x.split('\t')[0]) if x.split('\t')[0].isdigit() else -1)
        with open(users_path, 'w', encoding='UTF-8') as file:
            file.write('\n'.join([i for i in to_save if i and i[0] != '0']))
        return True

    def get(self, isu: int) -> User | None:
        """
        Retrieve a User by their ISU ID.

        Args:
            isu (int): The ISU identifier of the user.

        Returns:
            User | None: The User object if found, else None.
        """
        return self.db[isu] if isu in self.db.keys() else None

    def add(self, info: tuple[int, int, str, str, str, dict[str: dict[str: str | int | bool]]]) -> User:
        """
        Add a new User to the database.

        If the ISU ID is -1, assigns a new special ISU ID automatically.

        Args:
            info (tuple): User information tuple.

        Returns:
            User: The newly added User object.
        """
        if info[0] == -1:
            info = tuple([self.get_new_special_isu()] + list(info[1:]))
        self.db[info[0]] = User(info)
        if not (0 <= info[1] <= 1):
            self.uid_to_isu[info[1]] = info[0]
        return self.db[info[0]]

    def get_new_special_isu(self) -> int:
        """
        Generate a new unique special ISU ID not already used.

        Returns:
            int: A new special ISU ID.
        """
        while self.max_special_isu in self.used_specials_isus:
            self.max_special_isu += 1
        self.used_specials_isus.add(self.max_special_isu)
        return self.max_special_isu

    def keys(self):
        """
        Get all ISU keys in the database.

        Returns:
            KeysView[int]: A view of all ISU keys.
        """
        return self.db.keys()


def inject_a25(vk_helper):
    """Injects A25 data from ./subscribers/a25.txt into ./subscribers/users.txt.

    TSV header (tabs):
        ису	фио	наш	вк	ник	команда	кэп команды	Киберарена	раунд1?	stage	раунд2?	раунд3?	[баллы?]

    Compatibility:
    - "баллы?" column is optional.
    - Older a25.txt without "Киберарена" is also supported.

    Field rules:
    - "Киберарена": free text; empty means "не отыграны" (display is handled by kbr2t).
    - "кэп команды":
        * if value is a marker (captain/капитан/кэп/кеп) -> this row is the captain for its team;
        * else if it looks like a VK reference (link/screen-name/id123) -> explicit captain reference.

    If a25.txt is missing or empty, injection is skipped (bot keeps running).
    """
    import os
    import json

    a25_path = './subscribers/a25.txt'
    users_path = './subscribers/users.txt'

    if not os.path.exists(a25_path):
        warn(f"A25 inject skipped: file not found: {a25_path}")
        return

    with open(a25_path, 'r', encoding='UTF-8') as f:
        raw = f.read().replace('\r\n', '\n').replace('\r', '\n')

    raw_lines = [ln for ln in raw.split('\n') if ln.strip()]
    if not raw_lines:
        warn('A25 inject skipped: a25.txt is empty')
        return
    # Detect header and map columns (supports optional "Киберарена", "баллы?" and stage for 2nd round)
    header_cols = [c.strip() for c in raw_lines[0].split('	')]
    header_lower = [c.lower() for c in header_cols] if header_cols else []
    has_header = bool(header_cols and header_cols[0].lower() == 'ису')

    def find_col_contains(*needles: str):
        if not has_header:
            return None
        for i, name in enumerate(header_lower):
            for needle in needles:
                if needle and needle in name:
                    return i
        return None

    idx_fio = find_col_contains('фио')
    idx_sts = find_col_contains('наш')
    idx_vk = find_col_contains('вк')
    idx_nick = find_col_contains('ник')
    idx_team = find_col_contains('команда')
    idx_cap = find_col_contains('кэп', 'кеп', 'капитан')
    idx_kbr = find_col_contains('киберарена')
    idx_r1 = find_col_contains('раунд1')
    idx_stage2 = find_col_contains('stage', 'стейдж', 'этап')  # stored as a25.stg2
    idx_r2 = find_col_contains('раунд2')
    idx_r3 = find_col_contains('раунд3')
    idx_brs = find_col_contains('баллы')

    expects_kbr = idx_kbr is not None

    def parse_yes(value: str) -> bool:
        x = (value or '').strip().lower()
        return x in ('да', 'yes', 'true', '1', '+')

    def parse_is_internal(value: str) -> bool:
        """Returns True for internal participants, False for external."""
        x = (value or '').strip().lower()
        if not x:
            return True
        if x in ('внешний человек', 'внешний', 'external'):
            return False
        if '@' in x:
            return True
        return True

    def parse_isu_value(value: str):
        """Returns int ISU for positive numeric value, else None."""
        s = (value or '').strip()
        if not s or not s.lstrip('-').isdigit():
            return None
        try:
            v = int(s)
        except Exception:
            return None
        return v if v > 0 else None

    def clean_vk_link(s: str) -> str:
        s = (s or '').strip()
        if not s:
            return ''
        s = s.replace('https://vk.com/', '').replace('http://vk.com/', '')
        s = s.replace('https://vk.ru/', '').replace('http://vk.ru/', '')
        s = s.replace('https://m.vk.com/', '').replace('http://m.vk.com/', '')
        s = s.replace('https://m.vk.ru/', '').replace('http://m.vk.ru/', '')
        s = s.lstrip('@')
        return s.strip()

    def is_vk_ref(s: str) -> bool:
        s = (s or '').strip()
        if not s:
            return False
        ls = s.lower()
        if 'vk.com' in ls or 'vk.ru' in ls:
            return True
        if ls.startswith('id') and ls[2:].isdigit():
            return True
        # screen-name-like: letters/digits/underscore, at least 2 chars
        if re.match(r'^[a-zA-Z0-9_.]{2,}$', s):
            return True
        return False

    def is_captain_marker(s: str) -> bool:
        x = (s or '').strip().lower()
        return x in ('captain', 'капитан', 'кэп', 'кеп')

    def clean_captain_ref(s: str) -> str:
        s = (s or '').strip()
        if not s:
            return ''
        if is_captain_marker(s):
            return ''
        if not is_vk_ref(s):
            return ''
        return clean_vk_link(s)
    # Parse rows, normalize into 13 columns (tabs):
    # [isu, fio, sts_raw, vk_link, nick, team, cap_raw, kbr_raw, r1, stg2, r2, r3, brs]
    rows: list[list[str]] = []

    def get_col(cols: list[str], idx):
        return cols[idx].strip() if (idx is not None and idx < len(cols)) else ''

    for line in raw_lines:
        cols = [c.strip() for c in line.split('	')]

        # skip header
        if cols and cols[0].lower() == 'ису':
            continue

        if has_header:
            # Header-based parsing (tolerant to optional/moved columns)
            isu_s = get_col(cols, 0)
            fio = get_col(cols, idx_fio)
            sts_raw = get_col(cols, idx_sts)
            vk_link = get_col(cols, idx_vk)
            nick = get_col(cols, idx_nick)
            team = get_col(cols, idx_team)
            cap_raw = get_col(cols, idx_cap)
            kbr_raw = get_col(cols, idx_kbr)
            r1 = get_col(cols, idx_r1)
            stg2 = get_col(cols, idx_stage2)
            r2 = get_col(cols, idx_r2)
            r3 = get_col(cols, idx_r3)
            brs = get_col(cols, idx_brs)

            # Minimum sanity: need at least vk link or nick or team
            if not (vk_link or nick or team or isu_s):
                continue

            rows.append([isu_s, fio, sts_raw, vk_link, nick, team, cap_raw, kbr_raw, r1, stg2, r2, r3, brs])
            continue

        # Fallback positional parsing (legacy files without header)
        # Expected legacy formats:
        # - With kbr: [isu,fio,sts,vk,nick,team,cap,kbr,r1,r2,r3,(brs?)]
        # - Without kbr: [isu,fio,sts,vk,nick,team,cap,r1,r2,r3,(brs?)]

        legacy_has_kbr = False
        if len(cols) >= 12:
            legacy_has_kbr = True
        elif len(cols) >= 11:
            c7 = (cols[7] or '').strip().lower() if len(cols) > 7 else ''
            if c7 and c7 not in ('да', 'нет', 'yes', 'no', 'true', 'false', '0', '1', '+', '-'):
                legacy_has_kbr = True

        if legacy_has_kbr:
            if len(cols) < 11:
                warn('A25 inject: skipping row with missing columns:', line)
                continue
            if len(cols) == 11:
                cols.append('')  # brs
            cols = cols[:12]
            while len(cols) < 12:
                cols.append('')
            isu_s, fio, sts_raw, vk_link, nick, team, cap_raw, kbr_raw, r1, r2, r3, brs = cols
            rows.append([isu_s, fio, sts_raw, vk_link, nick, team, cap_raw, kbr_raw, r1, '', r2, r3, brs])
            continue

        if len(cols) < 10:
            warn('A25 inject: skipping row with missing columns:', line)
            continue
        if len(cols) == 10:
            cols.append('')  # brs
        cols = cols[:11]
        while len(cols) < 11:
            cols.append('')
        isu_s, fio, sts_raw, vk_link, nick, team, cap_raw, r1, r2, r3, brs = cols
        rows.append([isu_s, fio, sts_raw, vk_link, nick, team, cap_raw, '', r1, '', r2, r3, brs])

    if not rows:
        warn('A25 inject skipped: no valid rows')
        return

    # Read existing users.txt
    all_users: list[list[str]] = []
    if os.path.exists(users_path):
        with open(users_path, 'r', encoding='UTF-8') as f:
            content = f.read().replace('\r\n', '\n').replace('\r', '\n').strip()
            if content:
                all_users = [i.split('	') for i in content.split('\n') if i]

    # Ensure each row has at least 6 columns: isu, uid, fio, grp, nck, met
    for i in range(len(all_users)):
        while len(all_users[i]) < 6:
            all_users[i].append('-')

    # Build indexes
    isu_to_index: dict[int, int] = {}
    uid_to_index: dict[int, int] = {}
    for idx, row in enumerate(all_users):
        try:
            isu = int(row[0]) if str(row[0]).lstrip('-').isdigit() else None
        except Exception:
            isu = None
        try:
            uid = int(row[1]) if str(row[1]).isdigit() else None
        except Exception:
            uid = None
        if isu is not None:
            isu_to_index[isu] = idx
        if uid is not None and uid not in (0, 1):
            uid_to_index[uid] = idx

    # Resolve VK uids and captain uids (preserve order, skip empty refs)
    vk_links = [clean_vk_link(r[3]) for r in rows]
    cap_links = [clean_captain_ref(r[6]) for r in rows]

    def resolve_links(links: list[str]) -> list[int]:
        out = [0] * len(links)
        idxs = [i for i, lnk in enumerate(links) if lnk]
        if not idxs:
            return out
        resolved = vk_helper.links_to_uids([links[i] for i in idxs])
        for i, val in zip(idxs, resolved):
            try:
                out[i] = int(val) if str(val).isdigit() else 0
            except Exception:
                out[i] = 0
        return out

    resolved_uids = resolve_links(vk_links)
    resolved_cids = resolve_links(cap_links)

    # Build mappings for team captain
    uid_to_nick: dict[int, str] = {}
    team_to_cid: dict[str, int] = {}
    team_to_cap: dict[str, str] = {}

    for cols, uid in zip(rows, resolved_uids):
        team = (cols[5] or '').strip()
        nick = (cols[4] or '').strip()
        cap_raw = (cols[6] or '').strip()
        if uid not in (0, 1) and nick:
            uid_to_nick[uid] = nick
        if team and is_captain_marker(cap_raw) and uid not in (0, 1):
            team_to_cid[team] = uid
            team_to_cap[team] = nick

    # Fallback captains by explicit links (only for teams without marker)
    for cols, cid in zip(rows, resolved_cids):
        team = (cols[5] or '').strip()
        if not team or team in team_to_cid:
            continue
        if cid not in (0, 1):
            team_to_cid[team] = cid
            team_to_cap[team] = uid_to_nick.get(cid, '')

    # Inject
    for cols, uid, cid in zip(rows, resolved_uids, resolved_cids):
        isu_s, fio, sts_raw, vk_link, nick, team, cap_raw, kbr_raw, r1, stg2_raw, r2, r3, brs = cols

        isu_int = parse_isu_value(isu_s)
        uid_int = uid

        # Decide captain uid: prefer team mapping, then explicit per-row link
        team_key = (team or '').strip()
        cid_int = 0
        if team_key and team_key in team_to_cid:
            cid_int = team_to_cid[team_key]
        elif cid not in (0, 1):
            cid_int = cid

        # Decide captain nick
        cap_text = ''
        if team_key and team_key in team_to_cap and team_to_cap[team_key]:
            cap_text = team_to_cap[team_key]
        elif cid_int not in (0, 1):
            cap_text = uid_to_nick.get(cid_int, '')

        # If this row itself is captain-marker, show self nick even if mapping not built
        if not cap_text and is_captain_marker(cap_raw):
            cap_text = (nick or '').strip()

        info = {
            'fio': str(fio),
            'sts': parse_is_internal(sts_raw),
            'uid': int(uid_int),
            'nck': str(nick),
            'cmd': str(team),
            'cid': int(cid_int),
            'cap': str(cap_text),
            'kbr': str(kbr_raw).strip(),
            'wr1': parse_yes(r1),
            'stg2': str(stg2_raw).strip(),
            'wr2': parse_yes(r2),
            'wr3': parse_yes(r3),
            'brs': parse_yes(brs),
        }

        target_index = None
        if isu_int is not None and isu_int in isu_to_index:
            target_index = isu_to_index[isu_int]
        elif uid_int not in (0, 1) and uid_int in uid_to_index:
            target_index = uid_to_index[uid_int]

        if target_index is not None:
            u = all_users[target_index]
            if isu_int is not None:
                u[0] = str(isu_int)
            if uid_int not in (0, 1):
                u[1] = str(uid_int)
            if fio:
                u[2] = fio
            if nick:
                u[4] = nick

            try:
                met = json.loads(u[5]) if u[5] and u[5] != '-' else {}
                if not isinstance(met, dict):
                    met = {}
            except Exception:
                met = {}

            met['a25'] = info
            u[5] = json.dumps(met, ensure_ascii=False)
        else:
            # Append new record: assign special ISU if missing
            if isu_int is None:
                special = 1000000
                used = set()
                for row in all_users:
                    try:
                        used.add(int(row[0]))
                    except Exception:
                        pass
                while special in used:
                    special += 1
                isu_int = special

            new_user = [
                str(isu_int),
                str(uid_int),
                fio or '-',
                '-',
                nick or '-',
                json.dumps({'a25': info}, ensure_ascii=False)
            ]
            all_users.append(new_user)
            idx = len(all_users) - 1
            isu_to_index[int(isu_int)] = idx
            if uid_int not in (0, 1):
                uid_to_index[int(uid_int)] = idx

    with open(users_path, 'w', encoding='UTF-8') as f:
        f.write('\n'.join('\t'.join(map(str, i)) for i in all_users if i and i[0] != '0'))
