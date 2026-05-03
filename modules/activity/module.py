"""
活动日历模块（示例）
"""

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from core.base import BaseModule


class ActivityModule(BaseModule):
    name = "activity"
    description = "活动日历提醒"
    version = "1.0.0"
    
    async def on_load(self):
        self.register_command("活动", self._list, "查看当前活动")
        logger.info("[ActivityModule] 模块加载完成")
    
    async def _list(self, event: AstrMessageEvent, _=None):
        yield event.plain_result("活动日历功能开发中...")
