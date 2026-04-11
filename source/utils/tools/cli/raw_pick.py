from __future__ import annotations
"""
Minimal arrow-key picker for problematic rows from users_raw_lines (Windows, no deps).

Controls:
  Up/Down - move
  Enter   - open raw_edit for selected row
  q / Esc - quit

Run:
  python -m source.utils.tools.cli.raw_pick
"""

import os
import sys
import sqlalchemy as sa

from source.utils.db.db import init_engine, session_scope
from source.utils.db.models import UsersRawLineModel
from source.utils.tools.cli.picker import PickerItem, pick


def _is_tty() -> bool:
    return bool(sys.stdin and sys.stdin.isatty())




def _load_items(limit: int = 5000) -> tuple[list[str], list[PickerItem[int]], list[str]]:
    init_engine()
    with session_scope() as s:
        rows = (
            s.execute(
                sa.select(
                    UsersRawLineModel.id,
                    UsersRawLineModel.line_no,
                    UsersRawLineModel.isu,
                    UsersRawLineModel.uid,
                    UsersRawLineModel.fio,
                    UsersRawLineModel.grp,
                    UsersRawLineModel.nck,
                    UsersRawLineModel.error,
                )
                .where(UsersRawLineModel.status != "ok")
                .order_by(UsersRawLineModel.line_no, UsersRawLineModel.id)
                .limit(limit)
            )
            .all()
        )

    # Keep the "tabular" feel: align columns and cap long fields.
    def cut(s: str, w: int) -> str:
        s = (s or "").strip()
        if len(s) <= w:
            return s
        if w <= 3:
            return s[:w]
        return s[: w - 3] + "..."

    # Define columns dynamically from DB model (so header follows schema changes).
    # We still keep fixed widths for a stable UI.
    col_names = ["line_no", "isu", "uid", "fio", "grp", "nck", "error"]

    # Widths (tuned for typical console width; still readable if narrower)
    widths = {
        "line_no": 4,
        "isu": 6,
        "uid": 10,
        "fio": 28,
        "grp": 6,
        "nck": 16,
        "error": 18,
    }

    labels = {
        "line_no": "LINE",
        "isu": "ISU",
        "uid": "UID",
        "fio": "FIO",
        "grp": "GRP",
        "nck": "NCK",
        "error": "ERR",
    }

    items: list[PickerItem[int]] = []
    for rid, line_no, isu, uid, fio, grp, nck, err in rows:
        line_no = int(line_no)
        isu_s = "" if isu is None else str(int(isu))
        uid_s = "" if uid is None else str(int(uid))
        fio_s = cut(str(fio or ""), widths["fio"])
        grp_s = cut(str(grp or ""), widths["grp"])
        nck_s = cut(str(nck or ""), widths["nck"])
        err_s = cut(str(err or ""), widths["error"])

        items.append(
            PickerItem(
                value=int(rid),
                cols=[
                    str(line_no),
                    isu_s,
                    uid_s,
                    fio_s,
                    grp_s,
                    nck_s,
                    err_s,
                ],
            )
        )

    def center(text: str, w: int) -> str:
        # Python's center() is fine, but keep it explicit for clarity
        return str(text).center(int(w))

    # Header to be printed by picker: reflect column list (dynamic schema), centered
    header = [center(labels.get(c, c).upper(), widths.get(c, 10)) for c in col_names]
    header_cols = [labels.get(c, c).upper() for c in col_names]
    return header, items, header_cols




def _clamp(v: int, lo: int, hi: int) -> int:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def main() -> None:
    if not _is_tty():
        raise SystemExit("raw_pick requires an interactive terminal (stdin is not a TTY)")

    try:
        while True:
            header, items, header_cols = _load_items()
            rid = pick(
                "Fix panel (raw rows)",
                items,
                page_size=20,
                footer="Enter: edit | Left/Right: page",
                header_cols=header_cols,
            )
            if rid is None:
                return
            os.system(f"{sys.executable} -m source.utils.tools.cli.raw_edit {int(rid)}")
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
