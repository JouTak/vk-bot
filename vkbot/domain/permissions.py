from __future__ import annotations


class PermissionChecker:
    def __init__(self, admin_ids: set[int]):
        self._admin_ids = admin_ids

    def is_admin(self, uid: int) -> bool:
        return uid in self._admin_ids
