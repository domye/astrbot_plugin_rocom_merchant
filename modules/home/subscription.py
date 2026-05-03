"""
家园订阅数据管理
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...core.data_manager import DataManager


class HomeSubscriptionManager:
    def __init__(self, data_dir: str):
        self.data = DataManager(
            data_dir,
            "home_subscriptions.json",
            default_data={"subscriptions": {}}
        )
    
    async def _get_subs(self) -> Dict[str, Any]:
        return await self.data.get("subscriptions") or {}
    
    async def _save_subs(self, subs: Dict[str, Any]):
        await self.data.set("subscriptions", subs)
    
    def _key(self, session_id: str, user_id: str) -> str:
        return f"{session_id}:{user_id}"
    
    async def subscribe(self, session_id: str, user_id: str, uid: str) -> bool:
        key = self._key(session_id, user_id)
        subs = await self._get_subs()
        
        if key in subs and subs[key].get("uid") == uid:
            return False
        
        subs[key] = {
            "uid": uid,
            "session_id": session_id,
            "user_id": user_id,
            "polling": True,
            "timers": {},
            "created_at": datetime.now().isoformat()
        }
        await self._save_subs(subs)
        return True
    
    async def unsubscribe(self, session_id: str, user_id: str) -> bool:
        key = self._key(session_id, user_id)
        subs = await self._get_subs()
        
        if key not in subs:
            return False
        
        del subs[key]
        await self._save_subs(subs)
        return True
    
    async def get_subscription(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        key = self._key(session_id, user_id)
        subs = await self._get_subs()
        return subs.get(key)
    
    async def get_all_polling(self) -> List[Dict[str, Any]]:
        subs = await self._get_subs()
        return [s for s in subs.values() if s.get("polling")]
    
    async def get_all_subscriptions(self) -> List[Dict[str, Any]]:
        subs = await self._get_subs()
        return list(subs.values())
    
    async def set_polling(self, session_id: str, user_id: str, polling: bool):
        key = self._key(session_id, user_id)
        subs = await self._get_subs()
        
        if key in subs:
            subs[key]["polling"] = polling
            await self._save_subs(subs)
    
    async def set_timer(self, session_id: str, user_id: str, plant_id: int, rip_time: int):
        key = self._key(session_id, user_id)
        subs = await self._get_subs()
        
        if key in subs:
            if "timers" not in subs[key]:
                subs[key]["timers"] = {}
            subs[key]["timers"][str(plant_id)] = rip_time
            await self._save_subs(subs)
    
    async def clear_timer(self, session_id: str, user_id: str, plant_id: int):
        key = self._key(session_id, user_id)
        subs = await self._get_subs()
        
        if key in subs and "timers" in subs[key]:
            subs[key]["timers"].pop(str(plant_id), None)
            if not subs[key]["timers"]:
                subs[key]["polling"] = True
            await self._save_subs(subs)
    
    async def get_timers(self, session_id: str, user_id: str) -> Dict[str, int]:
        sub = await self.get_subscription(session_id, user_id)
        return sub.get("timers", {}) if sub else {}
