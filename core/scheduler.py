"""
统一定时任务调度器
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Callable, Awaitable, List, Tuple
from astrbot.api import logger


class Scheduler:
    def __init__(self):
        self._tasks: List[Tuple[str, List[str], Callable]] = []
        self._running = False
        self._task: asyncio.Task = None
    
    def _cn_tz(self) -> timezone:
        return timezone(timedelta(hours=8))
    
    def register(self, name: str, times: List[str], handler: Callable[[], Awaitable[None]]):
        self._tasks.append((name, times, handler))
        logger.info(f"[Scheduler] 注册定时任务: {name}, 时间: {times}")
    
    def _parse_time(self, time_str: str, base: datetime) -> datetime:
        hour, minute = map(int, time_str.split(":"))
        return base.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    def _next_time(self, now: datetime, times: List[str]) -> datetime:
        for t in sorted(times):
            pt = self._parse_time(t, now)
            if pt > now:
                return pt
        next_day = now + timedelta(days=1)
        return self._parse_time(sorted(times)[0], next_day)
    
    async def _run_handlers(self, now: datetime):
        for name, times, handler in self._tasks:
            for t in times:
                pt = self._parse_time(t, now)
                if abs((now - pt).total_seconds()) < 60:
                    try:
                        logger.info(f"[Scheduler] 执行定时任务: {name}")
                        await handler()
                    except Exception as e:
                        logger.error(f"[Scheduler] 任务执行失败 {name}: {e}")
    
    async def _loop(self):
        while self._running:
            try:
                now = datetime.now(self._cn_tz())
                if now.tzinfo is None:
                    now = now.replace(tzinfo=self._cn_tz())
                
                all_times = []
                for _, times, _ in self._tasks:
                    all_times.extend(times)
                
                if not all_times:
                    await asyncio.sleep(60)
                    continue
                
                next_run = self._next_time(now, all_times)
                sleep_seconds = max(1, (next_run - now).total_seconds())
                
                await asyncio.sleep(sleep_seconds)
                
                now = datetime.now(self._cn_tz())
                await self._run_handlers(now)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Scheduler] 循环异常: {e}")
                await asyncio.sleep(60)
    
    def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("[Scheduler] 调度器已启动")
    
    async def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[Scheduler] 调度器已停止")
