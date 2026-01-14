from utils.json_worker import *
from datetime import datetime

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
        'a25': {'fio': str, 'sts': s2b, 'uid': int, 'nck': str, 'cmd': str, 'cid': int,
                'wr1': s2b, 'wr2': s2b, 'wr3': s2b, 'brs': s2b}})

    # Checks for parsing validity: text to int and text to bool validators (checkers) (t2ic = Text to Int Checker)
    t2ic = str.isdigit
    t2bc = ['0', '1'].__contains__
    # Validators (checkers) for correctness of conversion from text to info fields
    text2info_check = (t2ic, t2ic, bool, bool, bool, {
        'a24': {'tsp': t2ic, 'nck': bool, 'lr1': t2bc, 'wr1': t2bc, 'wr2': t2bc, 'nyt': t2bc, 'fnl': t2bc},
        's25': {'tsp': t2ic, 'nck': bool, 'wr1': t2bc, 'rr1': t2ic, 'wr2': t2bc, 'rr2': t2ic, 'fnl': t2ic},
        'y25': {'tsp': t2ic, 'nck': bool, 'nmb': bool, 'bed': t2bc, 'way': t2ic, 'car': bool, 'liv': bool, 'ugo': t2ic},
        'a25': {'fio': bool, 'sts': t2bc, 'uid': t2ic, 'nck': bool, 'cmd': bool, 'cid': t2ic,
                'wr1': t2bc, 'wr2': t2bc, 'wr3': t2bc, 'brs': t2bc}})

    # bool to text
    b2t = lambda b: 'Да' if b else 'Нет'
    # Translates 'way' integer codes to string descriptions
    w2t = ('На бесплатном трансфере от ГК', 'Своим ходом (электричка)', 'Своим ходом (на машине)').__getitem__
    # String display helper: converts falsy to '[НЕТ ДАННЫХ]' (opt = optional)
    opt = lambda x: x if (x and x != '-') else '[НЕТ ДАННЫХ]'
    # Converts 'ugo' status integer codes to textual descriptions
    u2t = ('Нет.', 'Да, ты прошёл отбор, ждём оплату!', 'Оплата дошла до нас, ты едешь!').__getitem__
    # Functions to convert user info fields to text representations, including nested metadata
    info2text = (str, str, str, str, str, {
        'a24': {'tsp': t2s, 'nck': opt, 'lr1': b2t, 'wr1': b2t, 'wr2': b2t, 'nyt': b2t, 'fnl': b2t},
        's25': {'tsp': t2s, 'nck': opt, 'wr1': b2t, 'rr1': opt, 'wr2': b2t, 'rr2': opt, 'fnl': opt},
        'y25': {'tsp': t2s, 'nck': opt, 'nmb': opt, 'bed': b2t, 'way': w2t, 'car': opt, 'liv': opt, 'ugo': u2t},
        'a25': {'fio': opt, 'sts': b2t, 'uid': opt, 'nck': opt, 'cmd': opt, 'cid': opt,
                'wr1': b2t, 'wr2': b2t, 'wr3': b2t, 'brs': b2t}})

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
    """
    Injects Autumn Spartakiad 2025 (A25) data from ./subscribers/a25.txt into ./subscribers/users.txt.

    Expected a25.txt format (TSV, header allowed):
        ису    фио    наш    вк    ник    команда    кэп команды    раунд1?    раунд2?    раунд3?    баллы?

    Notes:
    - Header line is skipped automatically.
    - Rows with missing columns are skipped.
    - If a user exists in users.txt (matched by ISU first, then by VK uid), their met['a25'] is replaced/updated.
    - New users are appended to users.txt.
    - If a25.txt is missing, the function logs a warning and does nothing (bot keeps running).
    """
    import os
    import json

    a25_path = './subscribers/a25.txt'
    if not os.path.exists(a25_path):
        warn(f"A25 inject skipped: file not found: {a25_path}")
        return

    raw = ''
    with open(a25_path, 'r', encoding='UTF-8') as f:
        raw = f.read().replace('\r\n', '\n').replace('\r', '\n')

    raw_lines = [ln for ln in raw.split('\n') if ln.strip()]
    if not raw_lines:
        warn("A25 inject skipped: a25.txt is empty")
        return

    # Parse rows (skip header if present)
    rows = []
    for line in raw_lines:
        cols = [c.strip() for c in line.split('\t')]
        if len(cols) < 11:
            warn("A25 inject: skipping row with missing columns:", line)
            continue
        if cols[0].strip().lower() == 'ису':
            continue
        rows.append(cols[:11])

    if not rows:
        return

    def parse_is_internal(value: str) -> bool:
        """
        Returns True for internal participants, False for external.
        In the new table, column "наш" may contain an email (internal) or text like "Внешний человек".
        """
        x = (value or '').strip().lower()
        if not x:
            return True
        if x == 'внешний человек' or x == 'внешний' or x == 'external':
            return False
        # If it looks like email, treat as internal
        if '@' in x:
            return True
        # Default: internal
        return True

    def parse_yes(value: str) -> bool:
        x = (value or '').strip().lower()
        return x in ('да', 'yes', 'true', '1', '+')

    def clean_vk_link(s: str) -> str:
        s = (s or '').strip()
        if not s:
            return s
        s = s.replace('https://vk.com/', '').replace('http://vk.com/', '')
        s = s.replace('https://m.vk.com/', '').replace('http://m.vk.com/', '')
        s = s.lstrip('@')
        return s

    # Read existing users.txt
    users_path = './subscribers/users.txt'
    all_users = []
    if os.path.exists(users_path):
        with open(users_path, 'r', encoding='UTF-8') as f:
            content = f.read().replace('\r\n', '\n').replace('\r', '\n').strip()
            if content:
                all_users = [i.split('\t') for i in content.split('\n') if i]

    # Ensure each row has at least 6 columns: isu, uid, fio, grp, nck, met
    for i in range(len(all_users)):
        while len(all_users[i]) < 6:
            all_users[i].append('-')

    # Build indexes
    isu_to_index = {}
    uid_to_index = {}
    for idx, row in enumerate(all_users):
        try:
            isu = int(row[0]) if row[0].isdigit() else None
        except Exception:
            isu = None
        try:
            uid = int(row[1]) if row[1].isdigit() else None
        except Exception:
            uid = None
        if isu is not None:
            isu_to_index[isu] = idx
        if uid is not None and uid not in (0, 1):
            uid_to_index[uid] = idx

    # Resolve VK uids in batches
    vk_links = [clean_vk_link(r[3]) for r in rows]
    cap_links = [clean_vk_link(r[6]) for r in rows]

    resolved_uids = []
    resolved_cids = []
    for i in range(0, len(vk_links), 25):
        resolved_uids.extend(vk_helper.links_to_uids(vk_links[i:i + 25]))
    for i in range(0, len(cap_links), 25):
        resolved_cids.extend(vk_helper.links_to_uids(cap_links[i:i + 25]))

    # Inject
    for cols, uid, cid in zip(rows, resolved_uids, resolved_cids):
        isu_s, fio, sts_raw, vk_link, nick, team, cap_link, r1, r2, r3, brs = cols

        isu_int = int(isu_s) if isu_s.isdigit() else None
        uid_int = int(uid) if isinstance(uid, int) or (isinstance(uid, str) and str(uid).isdigit()) else 0
        cid_int = int(cid) if isinstance(cid, int) or (isinstance(cid, str) and str(cid).isdigit()) else 0

        info = {
            'fio': str(fio),
            'sts': parse_is_internal(sts_raw),
            'uid': uid_int,
            'nck': str(nick),
            'cmd': str(team),
            'cid': cid_int,
            'wr1': parse_yes(r1),
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
            # Update existing record
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
            # Append new record
            if isu_int is None:
                # Assign special ISU
                special = 1000000
                used = set()
                for row in all_users:
                    if row and row[0].isdigit():
                        used.add(int(row[0]))
                while special in used:
                    special += 1
                isu_int = special

            new_user = [str(isu_int), str(uid_int), fio or '-', '-', nick or '-', json.dumps({'a25': info}, ensure_ascii=False)]
            all_users.append(new_user)
            idx = len(all_users) - 1
            isu_to_index[isu_int] = idx
            if uid_int not in (0, 1):
                uid_to_index[uid_int] = idx

    with open(users_path, 'w', encoding='UTF-8') as f:
        f.write('\n'.join('\t'.join(map(str, i)) for i in all_users if i and i[0] != '0'))

