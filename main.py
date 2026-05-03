"""
洛克王国助手插件
"""

import asyncio
from typing import List, Type

from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register, StarTools

from .core.base import BaseModule
from .core.scheduler import Scheduler
from .modules.merchant.module import MerchantModule
from .modules.home.module import HomeModule


ENABLED_MODULES: List[Type[BaseModule]] = [
    MerchantModule,
    HomeModule,
]


@register(
    "astrbot_plugin_rocom_assistant",
    "domye",
    "洛克王国助手",
    "2.0.0",
    "https://github.com/domye/astrbot_plugin_rocom_assistant"
)
class RocomAssistantPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.scheduler = Scheduler()
        self.modules: List[BaseModule] = []
        self._command_handlers: dict = {}
        
        data_dir = str(StarTools.get_data_dir())
        
        for module_cls in ENABLED_MODULES:
            try:
                module_config = self.config.get(module_cls.name, {})
                module_config["api_key"] = self.config.get("api_key", "")
                module = module_cls(context, data_dir, module_config)
                self.modules.append(module)
                logger.info(f"[RocomAssistant] 加载模块: {module.name}")
            except Exception as e:
                logger.error(f"[RocomAssistant] 加载模块失败 {module_cls.name}: {e}")
        
        asyncio.create_task(self._init_modules())
    
    async def _init_modules(self):
        await asyncio.sleep(0.1)
        
        for module in self.modules:
            try:
                await module.on_load()
                
                for cmd in module.get_commands():
                    self._command_handlers[cmd.name] = cmd.handler
                    logger.debug(f"[RocomAssistant] 注册命令: {cmd.name}")
                
                for schedule in module.get_schedules():
                    self.scheduler.register(module.name, schedule.times, schedule.handler)
            
            except Exception as e:
                logger.error(f"[RocomAssistant] 初始化模块失败 {module.name}: {e}")
        
        self.scheduler.start()
        logger.info(f"[RocomAssistant] 插件初始化完成，已加载 {len(self.modules)} 个模块")
    
    async def terminate(self):
        await self.scheduler.stop()
        
        for module in self.modules:
            try:
                await module.on_unload()
            except Exception as e:
                logger.error(f"[RocomAssistant] 卸载模块失败 {module.name}: {e}")
        
        logger.info("[RocomAssistant] 插件已终止")
    
    @filter.command("商人")
    async def cmd_merchant(self, event: AstrMessageEvent):
        handler = self._command_handlers.get("商人")
        if handler:
            async for result in handler(event):
                yield result
    
    @filter.command("商人订阅开启")
    async def cmd_sub_open(self, event: AstrMessageEvent):
        handler = self._command_handlers.get("商人订阅开启")
        if handler:
            async for result in handler(event):
                yield result
    
    @filter.command("商人订阅关闭")
    async def cmd_sub_close(self, event: AstrMessageEvent):
        handler = self._command_handlers.get("商人订阅关闭")
        if handler:
            async for result in handler(event):
                yield result
    
    @filter.command("商人订阅添加")
    async def cmd_sub_add(self, event: AstrMessageEvent, item_name: str = ""):
        handler = self._command_handlers.get("商人订阅添加")
        if handler:
            async for result in handler(event, item_name):
                yield result
    
    @filter.command("商人订阅删除")
    async def cmd_sub_remove(self, event: AstrMessageEvent, item_name: str = ""):
        handler = self._command_handlers.get("商人订阅删除")
        if handler:
            async for result in handler(event, item_name):
                yield result
    
    @filter.command("商人订阅列表")
    async def cmd_sub_list(self, event: AstrMessageEvent):
        handler = self._command_handlers.get("商人订阅列表")
        if handler:
            async for result in handler(event):
                yield result
    
    @filter.command("商人订阅清空")
    async def cmd_sub_clear(self, event: AstrMessageEvent):
        handler = self._command_handlers.get("商人订阅清空")
        if handler:
            async for result in handler(event):
                yield result
    
    @filter.command("家园订阅")
    async def cmd_home_sub(self, event: AstrMessageEvent, uid: str = ""):
        handler = self._command_handlers.get("家园订阅")
        if handler:
            async for result in handler(event, uid):
                yield result
    
    @filter.command("家园取消")
    async def cmd_home_unsub(self, event: AstrMessageEvent):
        handler = self._command_handlers.get("家园取消")
        if handler:
            async for result in handler(event):
                yield result
    
    @filter.command("家园状态")
    async def cmd_home_status(self, event: AstrMessageEvent):
        handler = self._command_handlers.get("家园状态")
        if handler:
            async for result in handler(event):
                yield result
