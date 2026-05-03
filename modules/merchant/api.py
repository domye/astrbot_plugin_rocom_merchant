"""
远行商人 API
"""

from typing import Dict, Any, Optional
from datetime import datetime
from core.utils import HttpClient


API_URL = "https://roco.dayun.cool/api/merchant"


class MerchantApi:
    def __init__(self):
        self.client = HttpClient()
    
    async def fetch_data(self) -> Optional[Dict[str, Any]]:
        data = await self.client.get(
            f"{API_URL}",
            params={"t": str(int(datetime.now().timestamp()))}
        )
        if data and data.get("success"):
            return data
        return None
    
    async def close(self):
        await self.client.close()
