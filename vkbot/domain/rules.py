def is_real_isu(isu: int) -> bool:
    """Возвращает True, если ISU настоящий (100000–999999)."""
    return 100000 <= isu <= 999999


def is_special_isu(isu: int) -> bool:
    """Возвращает True, если ISU служебный (0–99999)."""
    return 0 <= isu < 100000


def is_valid_uid(uid: int) -> bool:
    """Возвращает True, если VK ID валиден."""
    return uid > 1
