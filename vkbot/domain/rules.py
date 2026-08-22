def is_real_isu(isu: int) -> bool:
    return 100000 <= isu <= 999999


def is_special_isu(isu: int) -> bool:
    return 0 <= isu < 100000


def is_valid_uid(uid: int) -> bool:
    return uid > 1
