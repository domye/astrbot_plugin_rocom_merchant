"""
通用异步 JSON 数据管理器
"""

import os
import json
import copy
import asyncio
from typing import Dict, Any, Optional
from astrbot.api import logger


class DataManager:
    """通用异步 JSON 数据管理器"""
    
    def __init__(self, data_dir: str, filename: str, default_data: Any = None):
        self.data_dir = data_dir
        self.path = os.path.join(data_dir, filename)
        self.default_data = default_data if default_data is not None else {}
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
                logger.error(f"[DataManager] 加载 {self.path} 失败: {e}")
        return copy.deepcopy(self.default_data)
    
    async def save(self):
        async with self.lock:
            await self._save()
    
    async def _save(self):
        try:
            temp_path = self.path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.path)
        except Exception as e:
            logger.error(f"[DataManager] 保存 {self.path} 失败: {e}")
    
    async def get(self, key: str = None) -> Any:
        async with self.lock:
            if key is None:
                return copy.deepcopy(self.data)
            return copy.deepcopy(self.data.get(key))
    
    async def set(self, key: str, value: Any):
        async with self.lock:
            self.data[key] = value
            await self._save()
    
    async def update(self, updates: Dict[str, Any]):
        async with self.lock:
            self.data.update(updates)
            await self._save()
    
    async def delete(self, key: str) -> bool:
        async with self.lock:
            if key in self.data:
                del self.data[key]
                await self._save()
                return True
            return False
    
    async def clear(self):
        async with self.lock:
            self.data = copy.deepcopy(self.default_data)
            await self._save()
