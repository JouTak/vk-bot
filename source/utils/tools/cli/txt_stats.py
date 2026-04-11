from __future__ import annotations

from collections import Counter


def main() -> None:
    c = Counter()
    with open("source/subscribers/users.txt", "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            p = ln.split("\t")
            if len(p) != 6 or not p[0].isdigit():
                continue
            isu = int(p[0])
            c["total"] += 1
            if isu < 100000:
                c["isu_lt_100000"] += 1
            else:
                c["isu_ge_100000"] += 1

    print(dict(c))


if __name__ == "__main__":
    main()