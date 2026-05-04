"""
工具函数
"""

import httpx
from typing import Optional, Dict, Any
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent


async def check_admin(event: AstrMessageEvent) -> bool:
    if event.is_private_chat():
        return True
    if event.is_admin():
        return True
    
    sender_id = str(event.get_sender_id())
    role = str(getattr(event, "role", "") or "").lower()
    
    try:
        group = await event.get_group()
        if group:
            owner_candidates = [
                getattr(group, "group_owner", None),
                getattr(group, "owner_id", None),
                getattr(group, "group_owner_id", None),
            ]
            if any(str(owner) == sender_id for owner in owner_candidates if owner):
                return True
            admins = [str(x) for x in getattr(group, "group_admins", [])]
            if sender_id in admins:
                return True
            if role in {"admin", "owner"}:
                return True
    except Exception:
        if role in {"admin", "owner"}:
            return True
    
    return False


class HttpClient:
    def __init__(self, timeout: float = 10.0):
        self._client: Optional[httpx.AsyncClient] = None
        self._timeout = timeout
    
    async def get(self, url: str, params: Dict = None, **kwargs) -> Optional[Dict[str, Any]]:
        for attempt in range(3):
            try:
                if self._client is None or self._client.is_closed:
                    self._client = httpx.AsyncClient(timeout=self._timeout)
                
                resp = await self._client.get(url, params=params, **kwargs)
                if resp.status_code != 200:
                    logger.warning(f"[HttpClient] 状态码: {resp.status_code}")
                    continue
                return resp.json()
            except Exception as e:
                logger.error(f"[HttpClient] 请求失败: {e}, 尝试 {attempt + 1}/3")
        return None
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
