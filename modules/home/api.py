"""
家园API接口
"""

import aiohttp
from typing import Dict, Any, Optional
from astrbot.api import logger

API_BASE = "https://wegame.shallow.ink"


class HomeApi:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
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
            
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("code") == 0:
                        return data.get("data", {}).get("home_info")
                logger.warning(f"[HomeApi] 获取家园信息失败: status={resp.status}")
                return None
        except Exception as e:
            logger.error(f"[HomeApi] 请求异常: {e}")
            return None
    
    def extract_plants(self, home_info: Dict[str, Any]) -> list:
        plants = []
        try:
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
