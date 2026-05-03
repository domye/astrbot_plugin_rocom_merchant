"""
宠物查询模块（示例）
"""

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from core.base import BaseModule


class PetModule(BaseModule):
    name = "pet"
    description = "宠物图鉴查询"
    version = "1.0.0"
    
    async def on_load(self):
        self.register_command("宠物", self._query, "查询宠物信息")
        logger.info("[PetModule] 模块加载完成")
    
    async def _query(self, event: AstrMessageEvent, pet_name: str = ""):
        if not pet_name:
            yield event.plain_result("请输入宠物名称，例如: /宠物 火花")
            return
        yield event.plain_result(f"宠物 [{pet_name}] 查询功能开发中...")
