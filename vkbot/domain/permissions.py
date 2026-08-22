from __future__ import annotations


class PermissionChecker:
    def __init__(self, admin_ids: set[int]):
        self._admin_ids = admin_ids

    def is_admin(self, uid: int) -> bool:
        return uid in self._admin_ids

    def require_admin(self, uid: int) -> bool:
        """Бросает PermissionError если не админ. Для middleware."""
        if not self.is_admin(uid):
            raise PermissionError(f"User {uid} is not admin")
        return True
