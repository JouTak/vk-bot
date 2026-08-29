from __future__ import annotations


class PermissionChecker:
    """Проверяет права администратора по списку VK ID."""

    def __init__(self, admin_ids: set[int]):
        """Сохраняет множество админских VK ID."""
        self._admin_ids = admin_ids

    def is_admin(self, uid: int) -> bool:
        """Возвращает True, если пользователь входит в список админов."""
        return uid in self._admin_ids
