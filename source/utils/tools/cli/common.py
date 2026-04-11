from __future__ import annotations
"""
Common helpers for interactive CLI tools.

Goal: avoid logic duplication between console/raw_edit/db_controller.

This module is intentionally dependency-light and should be safe to import
from interactive scripts.
"""

import os
from dataclasses import dataclass

import vk_api
from dotenv import load_dotenv

from source.utils.vk_helper import VKHelper


@dataclass(frozen=True)
class VkLookupResult:
    fio: str
    url: str


def get_vk_helper_from_env() -> VKHelper | None:
    """Build VKHelper from BOT_TOKEN/GROUP_ID in env/.env.

    Returns None if vars are missing or VK session cannot be created.
    """
    load_dotenv(override=False)
    token = os.getenv("BOT_TOKEN") or ""
    group_id = os.getenv("GROUP_ID") or ""
    if not token:
        return None
    if not group_id or not str(group_id).isdigit():
        return None
    try:
        vk_session = vk_api.VkApi(token=token)
        return VKHelper(vk_session, int(group_id))
    except Exception:
        return None


def vk_lookup_uid(vk: VKHelper, uid: int) -> VkLookupResult:
    """Lookup VK user by numeric uid.

    Raises:
      - ValueError("vk_user_not_found") if VK returns empty list
      - RuntimeError("vk_unreachable") on network/proxy errors
    """
    try:
        r = vk.vk.users.get(user_ids=uid)
    except Exception as e:
        raise RuntimeError("vk_unreachable") from e

    if not r:
        raise ValueError("vk_user_not_found")

    u = r[0]
    fio = f"{u.get('first_name','').strip()} {u.get('last_name','').strip()}".strip()
    url = f"https://vk.com/id{uid}"
    return VkLookupResult(fio=fio, url=url)