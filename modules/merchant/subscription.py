"""
远行商人订阅管理
"""

import copy
from typing import Dict, Any, Optional, List
from core.data_manager import DataManager


class MerchantSubscriptionManager(DataManager):
    def __init__(self, data_dir: str):
        super().__init__(data_dir, "merchant_subscriptions.json", {})
    
    async def get_group(self, session_id: str) -> Optional[Dict[str, Any]]:
        return await self.get(str(session_id))
    
    async def set_enabled(self, session_id: str, enabled: bool):
        key = str(session_id)
        data = await self.get(key) or {"enabled": False, "user_items": {}}
        data["enabled"] = enabled
        await self.set(key, data)
    
    async def get_all_enabled(self) -> Dict[str, Dict[str, Any]]:
        all_data = await self.get()
        return {k: copy.deepcopy(v) for k, v in all_data.items() if v.get("enabled")}
    
    async def add_user_item(self, session_id: str, user_id: str, item_name: str) -> bool:
        key = str(session_id)
        data = await self.get(key) or {"enabled": False, "user_items": {}}
        
        if "user_items" not in data:
            data["user_items"] = {}
        
        uid = str(user_id)
        if uid not in data["user_items"]:
            data["user_items"][uid] = []
        
        if item_name not in data["user_items"][uid]:
            data["user_items"][uid].append(item_name)
            await self.set(key, data)
            return True
        return False
    
    async def remove_user_item(self, session_id: str, user_id: str, item_name: str) -> bool:
        key = str(session_id)
        data = await self.get(key)
        if not data:
            return False
        
        uid = str(user_id)
        user_items = data.get("user_items", {}).get(uid, [])
        if item_name in user_items:
            user_items.remove(item_name)
            await self.set(key, data)
            return True
        return False
    
    async def get_user_items(self, session_id: str, user_id: str) -> List[str]:
        data = await self.get(str(session_id))
        return copy.deepcopy(data.get("user_items", {}).get(str(user_id), []))
    
    async def clear_user_items(self, session_id: str, user_id: str) -> bool:
        key = str(session_id)
        data = await self.get(key)
        if not data:
            return False
        
        uid = str(user_id)
        if uid in data.get("user_items", {}):
            data["user_items"][uid] = []
            await self.set(key, data)
            return True
        return False
