from __future__ import annotations

import json
import time
import requests
from loguru import logger

import vk_api
from vk_api.utils import get_random_id


class VKClient:
    """Обёртка над VK API. Знает только про отправку и резолвинг."""

    def __init__(self, token: str, group_id: int):
        self.session = vk_api.VkApi(token=token)
        self.api = self.session.get_api()
        self.group_id = group_id

    def is_member(self, uid: int) -> bool:
        try:
            return bool(self.session.method(
                "groups.isMember",
                {"group_id": self.group_id, "user_id": uid},
            ))
        except Exception:
            return True  # не спамим если API недоступен

    def get_user_info(self, uid: int) -> tuple[str, str]:
        """Возвращает (first_name, last_name)."""
        try:
            resp = self.session.method("users.get", {"user_ids": uid})
            if resp:
                return resp[0].get("first_name", ""), resp[0].get("last_name", "")
        except Exception:
            pass
        return "", ""

    def send_messages(self, messages: list[dict]) -> list:
        """Батч-отправка через execute (до 25 за раз).

        Возвращает список в том же порядке, что и messages:
        - успех: то, что вернул VK (message_id)
        - ошибка: {"error": "<текст ошибки>"}
        """
        if not messages:
            return []

        results = []

        for i in range(0, len(messages), 25):
            chunk = messages[i:i + 25]

            for d in chunk:
                d["group_id"] = self.group_id
                d["random_id"] = get_random_id()

            parts = [
                f"API.messages.send({json.dumps(d, ensure_ascii=False)})"
                for d in chunk
            ]
            code = f"return [{','.join(parts)}];"

            try:
                resp, exec_errors = self._execute_raw(code)

                # Сопоставляем execute_errors с позициями False в resp
                err_iter = iter(exec_errors)
                for r in resp:
                    if r is False:
                        e = next(err_iter, None) or {}
                        results.append({
                            "error": e.get("error_msg") or "VK вернул false",
                        })
                    else:
                        results.append(r)

                # Если VK вернул массив короче чанка — помечаем остаток ошибкой
                if len(resp) < len(chunk):
                    results.extend(
                        [{"error": "Нет результата от execute"}]
                        * (len(chunk) - len(resp))
                    )

            except Exception as e:
                logger.error(f"send_messages batch error: {e}")
                results.extend([{"error": str(e)}] * len(chunk))

            if i + 25 < len(messages):
                time.sleep(0.35)

        return results

    def _execute_raw(self, code: str) -> tuple[list, list]:
        """execute с возвратом execute_errors (vk_api.method их не отдаёт)."""
        resp = requests.post(
            "https://api.vk.com/method/execute",
            data={
                "code": code,
                "access_token": self._get_access_token(),
                "v": getattr(self.session, "API_VERSION", "5.131"),
            },
            timeout=30,
        )
        values = resp.json()

        if "error" in values:
            err = values["error"]
            raise RuntimeError(
                f"VK error {err.get('error_code')}: {err.get('error_msg')}"
            )

        return values.get("response") or [], values.get("execute_errors") or []

    def _get_access_token(self) -> str:
        raw = self.session.token
        if isinstance(raw, dict):
            return raw.get("access_token", "")
        return raw or ""

    def resolve_links(self, links: list[str]) -> list[int]:
        """Резолвит VK-ссылки/screen_names в uid. Батчи по 25."""
        out = [0] * len(links)

        def extract_screen_name(link: str) -> str:
            s = str(link).strip()
            if not s:
                return ""
            s = s.split("?", 1)[0].split("#", 1)[0]
            if "/" in s:
                s = s.rsplit("/", 1)[-1]
            if "@" in s:
                s = s.split("@", 1)[-1]
            return s.strip()

        screen_names = [extract_screen_name(l) for l in links]
        idxs = [i for i, name in enumerate(screen_names) if name]

        if not idxs:
            return out

        for start in range(0, len(idxs), 25):
            part_idxs = idxs[start:start + 25]
            part_names = [screen_names[i] for i in part_idxs]

            parts = [
                f'API.utils.resolveScreenName({json.dumps({"screen_name": name})})'
                for name in part_names
            ]
            code = f"return [{','.join(parts)}];"

            try:
                resp = self.session.method("execute", {"code": code})
                for i, r in zip(part_idxs, resp):
                    if isinstance(r, dict) and "object_id" in r:
                        out[i] = int(r["object_id"])
            except Exception as e:
                logger.warning(f"resolve_links batch error: {e}")

            if start + 25 < len(idxs):
                time.sleep(0.35)

        return out
