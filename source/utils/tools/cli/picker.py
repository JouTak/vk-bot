from __future__ import annotations
"""
Shared minimal arrow-key picker (Windows, no external deps).

Designed to be reused by:
- raw_pick (fix panel)
- db_controller find results (user picker)

Keys (Windows):
- Up/Down: move selection
- Left/Right: page (-/+ page_size)
- Enter: choose
- q / Esc: quit (returns None)
- Ctrl+C: quit (raises KeyboardInterrupt)

Non-Windows platforms are intentionally not supported to keep this dependency-free.
"""

from dataclasses import dataclass
import os
import sys
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class PickerItem(Generic[T]):
    value: T
    # Either provide `line` (plain string) OR `cols` (table row). If both are provided, `cols` wins.
    line: str = ""
    cols: list[str] | None = None


def is_tty() -> bool:
    return bool(sys.stdin and sys.stdin.isatty())


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _getch_windows() -> str:
    # Arrows are returned as a two-step sequence: '\x00' or '\xe0' + code.
    # We return the raw 2-char sequence for arrows, or 1-char for regular keys.
    # Ctrl+C is handled by checking the keyboard buffer first, because msvcrt.getwch()
    # does not always translate Ctrl+C into KeyboardInterrupt.
    import msvcrt  # type: ignore

    while True:
        if not msvcrt.kbhit():
            continue
        ch = msvcrt.getwch()
        if ch == "\x03":  # Ctrl+C
            raise KeyboardInterrupt
        if ch in ("\x00", "\xe0"):
            ch2 = msvcrt.getwch()
            return ch + ch2
        return ch


def read_key() -> str:
    if os.name != "nt":
        raise SystemExit("picker: Windows only (no extra dependencies)")
    return _getch_windows()


def clamp(v: int, lo: int, hi: int) -> int:
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def pick(
    title: str,
    items: list[PickerItem[T]],
    *,
    page_size: int = 20,
    initial_index: int = 0,
    footer: str | None = None,
    header: str | None = None,
    header_center: bool = False,
    header_cols: list[str] | None = None,
) -> T | None:
    """
    Interactive arrow-key picker.

    Args:
        title: header title.
        items: items to pick from.
        page_size: number of rows visible.
        initial_index: starting selected index.
        footer: optional extra footer line.

    Returns:
        chosen value or None if cancelled.
    """
    if not is_tty():
        raise SystemExit("picker requires an interactive terminal (stdin is not a TTY)")

    if not items:
        clear_screen()
        print(title)
        print("-" * len(title))
        print("No items.")
        return None

    selected = clamp(initial_index, 0, len(items) - 1)

    def page_start() -> int:
        return (selected // page_size) * page_size

    def page_end(start: int) -> int:
        return min(len(items), start + page_size)

    def draw() -> None:
        clear_screen()
        print(title)
        print("-" * len(title))
        print("Up/Down move | Left/Right page | Enter choose | q quit")
        print("")
        start = page_start()
        end = page_end(start)

        # Width for absolute index column (1-based global)
        w_idx = max(2, len(str(end)))

        # Detect "table mode" for current page: if any item has cols (and header_cols provided),
        # we render as aligned columns with auto-fit widths for THIS page.
        start = page_start()
        end = page_end(start)
        window = items[start:end]

        use_table = bool(header_cols) and any(it.cols is not None for it in window)

        def crop(s: str, w: int) -> str:
            if len(s) <= w:
                return s
            if w <= 3:
                return s[:w]
            return s[: w - 3] + "..."

        if use_table:
            cols_n = len(header_cols or [])
            rows: list[list[str]] = []
            for it in window:
                row = (it.cols or [])
                # normalize row length
                row = [str(x) for x in row]
                if len(row) < cols_n:
                    row = row + [""] * (cols_n - len(row))
                elif len(row) > cols_n:
                    row = row[:cols_n]
                rows.append(row)

            # auto-fit widths from header + values (per page)
            widths = [len(str(h or "")) for h in header_cols]  # type: ignore[arg-type]
            for r in rows:
                for i, v in enumerate(r):
                    widths[i] = max(widths[i], len(v))

            # hard cap to keep UI sane
            widths = [min(w, 40) for w in widths]

            # render header (centered per column)
            header_cells = [str(h or "").upper().center(widths[i]) for i, h in enumerate(header_cols or [])]
            header_line = " ".join(header_cells).rstrip()

            # optional header string above table (centered across table width)
            table_w = len(header_line)
            if header:
                if header_center:
                    print(" " * (w_idx + 4) + header.center(table_w).rstrip())
                else:
                    print(" " * (w_idx + 4) + header.rstrip())

            print(" " * (w_idx + 4) + header_line)
            print(" " * (w_idx + 4) + "-" * table_w)

            for idx in range(start, end):
                it = items[idx]
                prefix = ">" if idx == selected else " "
                abs_no = idx + 1
                row = rows[idx - start]
                cells = [crop(row[i], widths[i]).ljust(widths[i]) for i in range(cols_n)]
                line = " ".join(cells).rstrip()
                print(f"{prefix} {abs_no:>{w_idx}}) {line}")
        else:
            # Optional header row (plain text).
            # If header_center=True: center header string inside the same width as list lines.
            if header:
                if header_center:
                    # approximate content width: longest visible line length
                    content_w = 0
                    for j in range(start, end):
                        content_w = max(content_w, len(items[j].line))
                    if content_w <= 0:
                        content_w = len(header)
                    print(" " * (w_idx + 4) + header.center(content_w).rstrip())
                else:
                    print(" " * (w_idx + 4) + header.rstrip())

            for idx in range(start, end):
                it = items[idx]
                prefix = ">" if idx == selected else " "
                abs_no = idx + 1
                print(f"{prefix} {abs_no:>{w_idx}}) {it.line}")

        print("")
        page_no = (start // page_size) + 1
        pages = (len(items) + page_size - 1) // page_size
        print(f"{selected + 1}/{len(items)} | page {page_no}/{pages}")
        if footer:
            print(footer)

    while True:
        # Clamp inside list
        selected = clamp(selected, 0, len(items) - 1)

        # Clamp inside current page (page is strict: no moving outside page with Up/Down)
        start = page_start()
        end = page_end(start)
        selected = clamp(selected, start, end - 1)

        draw()
        key = read_key()

        # quit
        if key in ("q", "Q"):
            return None

        # Enter: can be '\r' or '\n' depending on terminal
        if key in ("\r", "\n"):
            return items[selected].value

        # Up/Down: move only within current page
        if key in ("\x00H", "\xe0H"):  # Up
            if selected > start:
                selected -= 1
            continue
        if key in ("\x00P", "\xe0P"):  # Down
            if selected < end - 1:
                selected += 1
            continue

        # Left/Right: page switch. Keep relative position within page if possible.
        rel = selected - start

        if key in ("\x00K", "\xe0K"):  # Left
            if start == 0:
                continue
            new_start = max(0, start - page_size)
            new_end = page_end(new_start)
            selected = new_start + min(rel, (new_end - new_start) - 1)
            continue

        if key in ("\x00M", "\xe0M"):  # Right
            if end >= len(items):
                continue
            new_start = start + page_size
            new_end = page_end(new_start)
            selected = new_start + min(rel, (new_end - new_start) - 1)
            continue
