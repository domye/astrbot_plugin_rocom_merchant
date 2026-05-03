"""
家园API接口
"""

import aiohttp
from typing import Dict, Any, Optional
from astrbot.api import logger

API_BASE = "https://wegame.shallow.ink"


class HomeApi:
    def __init__(self, api_key: str = ""):
        self._session: Optional[aiohttp.ClientSession] = None
        self._api_key = api_key
    
    def set_api_key(self, api_key: str):
        self._api_key = api_key
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_home_info(self, uid: str) -> Optional[Dict[str, Any]]:
        try:
            session = await self._get_session()
            url = f"{API_BASE}/api/v1/games/rocom/ingame/home/info"
            params = {"uid": uid, "wait_ms": 5000}
            headers = {}
            if self._api_key:
                headers["X-API-Key"] = self._api_key
            
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("code") == 0:
                        return data.get("data")
                logger.warning(f"[HomeApi] 获取家园信息失败: status={resp.status}")
                return None
        except Exception as e:
            logger.error(f"[HomeApi] 请求异常: {e}")
            return None
    
    def extract_plants(self, data: Dict[str, Any]) -> list:
        plants = []
        try:
            home_info = data.get("home_info", {})
            brief = home_info.get("friend_cell_home_brief_info", {})
            plant_info = brief.get("home_plant_info", {})
            land_list = plant_info.get("home_plant_land_list", [])
            
            for land in land_list:
                land_index = land.get("land_index", 0)
                for plant in land.get("home_plant_list", []):
                    plant["land_index"] = land_index
                    plants.append(plant)
        except Exception as e:
            logger.error(f"[HomeApi] 解析植物数据失败: {e}")
        
        return plants
    
    def extract_pets(self, data: Dict[str, Any]) -> list:
        pets = []
        try:
            home_info = data.get("home_info", {})
            brief = home_info.get("friend_cell_home_brief_info", {})
            home_pets = brief.get("home_pets", [])
            for pet in home_pets:
                pet_info = pet.get("home_pet_info", {})
                display_info = pet.get("display_info", {})
                pets.append({
                    "pet_gid": pet_info.get("pet_gid"),
                    "pet_cfg_id": pet_info.get("pet_cfg_id"),
                    "name": display_info.get("name") or pet_info.get("name", ""),
                    "level": display_info.get("level", 0),
                    "have_egg": pet.get("have_egg", False)
                })
        except Exception as e:
            logger.error(f"[HomeApi] 解析宠物数据失败: {e}")
        
        return pets
