"""
功能模块基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime

from astrbot.api.event import AstrMessageEvent


@dataclass
class CommandInfo:
    name: str
    handler: Callable[[AstrMessageEvent, Any], Awaitable[Any]]
    description: str = ""
    aliases: List[str] = field(default_factory=list)


@dataclass
class ScheduleInfo:
    times: List[str]
    handler: Callable[[], Awaitable[None]]
    description: str = ""


class BaseModule(ABC):
    name: str = "base"
    description: str = "基础模块"
    version: str = "1.0.0"
    
    def __init__(self, context, data_dir: str, config: dict = None):
        self.context = context
        self.data_dir = data_dir
        self.config = config or {}
        self._commands: List[CommandInfo] = []
        self._schedules: List[ScheduleInfo] = []
    
    @abstractmethod
    async def on_load(self):
        pass
    
    async def on_unload(self):
        pass
    
    def register_command(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        aliases: List[str] = None
    ):
        self._commands.append(CommandInfo(
            name=name,
            handler=handler,
            description=description,
            aliases=aliases or []
        ))
    
    def register_schedule(
        self,
        times: List[str],
        handler: Callable,
        description: str = ""
    ):
        self._schedules.append(ScheduleInfo(
            times=times,
            handler=handler,
            description=description
        ))
    
    def get_commands(self) -> List[CommandInfo]:
        return self._commands
    
    def get_schedules(self) -> List[ScheduleInfo]:
        return self._schedules
