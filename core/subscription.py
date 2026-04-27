"""
远行商人订阅管理器
"""

import os
import json
import copy
import asyncio
from typing import Dict, Any, Optional, List
from astrbot.api import logger


class AsyncDataManager:
    """通用异步 JSON 数据管理器"""

    def __init__(self, data_dir: str, filename: str, default_data: Any):
        self.data_dir = data_dir
        self.path = os.path.join(data_dir, filename)
        self.default_data = default_data
        self.lock = asyncio.Lock()
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        self.data = self._load()

    def _load(self) -> Any:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[RocomMerchant] 加载 {self.path} 失败: {e}")
        return copy.deepcopy(self.default_data)

    async def _save(self):
        try:
            temp_path = self.path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.path)
        except Exception as e:
            logger.error(f"[RocomMerchant] 保存 {self.path} 失败: {e}")


class SubscriptionManager(AsyncDataManager):
    """群订阅管理器"""

    def __init__(self, data_dir: str):
        super().__init__(data_dir, "subscriptions.json", {})

    async def get_group_subscriptions(self, session_id: str) -> Optional[Dict[str, Any]]:
        async with self.lock:
            return copy.deepcopy(self.data.get(str(session_id)))

    async def set_group_subscription(self, session_id: str, enabled: bool) -> None:
        async with self.lock:
            key = str(session_id)
            if key not in self.data:
                self.data[key] = {"enabled": enabled, "user_items": {}}
            else:
                self.data[key]["enabled"] = enabled
            await self._save()

    async def get_all_enabled_groups(self) -> Dict[str, Dict[str, Any]]:
        async with self.lock:
            return {
                k: copy.deepcopy(v)
                for k, v in self.data.items()
                if v.get("enabled")
            }

    async def add_user_item(self, session_id: str, user_id: str, item_name: str) -> bool:
        async with self.lock:
            key = str(session_id)
            if key not in self.data:
                self.data[key] = {"enabled": False, "user_items": {}}
            if "user_items" not in self.data[key]:
                self.data[key]["user_items"] = {}
            uid = str(user_id)
            if uid not in self.data[key]["user_items"]:
                self.data[key]["user_items"][uid] = []
            if item_name not in self.data[key]["user_items"][uid]:
                self.data[key]["user_items"][uid].append(item_name)
                await self._save()
                return True
            return False

    async def remove_user_item(self, session_id: str, user_id: str, item_name: str) -> bool:
        async with self.lock:
            key = str(session_id)
            if key not in self.data:
                return False
            uid = str(user_id)
            user_items = self.data[key].get("user_items", {}).get(uid, [])
            if item_name in user_items:
                user_items.remove(item_name)
                await self._save()
                return True
            return False

    async def get_user_items(self, session_id: str, user_id: str) -> List[str]:
        async with self.lock:
            key = str(session_id)
            uid = str(user_id)
            return copy.deepcopy(
                self.data.get(key, {}).get("user_items", {}).get(uid, [])
            )

    async def clear_user_items(self, session_id: str, user_id: str) -> bool:
        async with self.lock:
            key = str(session_id)
            uid = str(user_id)
            if key in self.data and uid in self.data[key].get("user_items", {}):
                self.data[key]["user_items"][uid] = []
                await self._save()
                return True
            return False
