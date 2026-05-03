"""
家园种植提醒模块
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp

from ...core.base import BaseModule
from .api import HomeApi
from .subscription import HomeSubscriptionManager


class HomeModule(BaseModule):
    name = "home"
    description = "家园种植提醒"
    version = "1.0.0"
    
    POLL_INTERVAL = 600
    
    def __init__(self, context, data_dir: str, config: dict = None):
        super().__init__(context, data_dir, config)
        config = config or {}
        api_key = config.get("api_key", "")
        self.api = HomeApi(api_key)
        self.subscription = HomeSubscriptionManager(data_dir)
        self._poll_task: asyncio.Task = None
        self._running = False
    
    async def on_load(self):
        self.register_command("家园订阅", self._subscribe, "订阅家园种植提醒")
        self.register_command("家园取消", self._unsubscribe, "取消家园订阅")
        self.register_command("家园状态", self._status, "查看订阅状态")
        
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info(f"[HomeModule] 模块加载完成，轮询间隔: {self.POLL_INTERVAL}秒")
    
    async def on_unload(self):
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        await self.api.close()
    
    def _cn_tz(self) -> timezone:
        return timezone(timedelta(hours=8))
    
    def _now_ts(self) -> int:
        return int(datetime.now(self._cn_tz()).timestamp())
    
    async def _subscribe(self, event: AstrMessageEvent, uid: str = ""):
        if not uid:
            yield event.plain_result("请输入UID，例如: /家园订阅 123456")
            return
        
        added = await self.subscription.subscribe(
            event.unified_msg_origin,
            event.get_sender_id(),
            uid
        )
        
        if added:
            yield event.plain_result(f"已订阅家园 {uid}，将在作物成熟时提醒你")
        else:
            yield event.plain_result("你已订阅过该UID")
    
    async def _unsubscribe(self, event: AstrMessageEvent, _=None):
        removed = await self.subscription.unsubscribe(
            event.unified_msg_origin,
            event.get_sender_id()
        )
        yield event.plain_result("已取消家园订阅" if removed else "你未订阅任何家园")
    
    async def _status(self, event: AstrMessageEvent, _=None):
        sub = await self.subscription.get_subscription(
            event.unified_msg_origin,
            event.get_sender_id()
        )
        
        if not sub:
            yield event.plain_result("你未订阅任何家园")
            return
        
        uid = sub.get("uid")
        
        home_info = await self.api.get_home_info(uid)
        if not home_info:
            yield event.plain_result(f"订阅UID: {uid}\n查询家园信息失败")
            return
        
        plants = self.api.extract_plants(home_info)
        now = self._now_ts()
        
        ripe_count = 0
        growing_count = 0
        max_rip_time = None
        
        for plant in plants:
            state = plant.get("plant_state", 0)
            rip_time = plant.get("plant_rip_time", 0)
            
            if state == 1:
                if rip_time <= now:
                    ripe_count += 1
                else:
                    growing_count += 1
                    if max_rip_time is None or rip_time > max_rip_time:
                        max_rip_time = rip_time
        
        lines = [f"订阅UID: {uid}", f"成熟: {ripe_count}株, 生长中: {growing_count}株"]
        
        if growing_count > 0 and max_rip_time:
            remain = max_rip_time - now
            remain_str = self._format_remain(remain)
            lines.append(f"{remain_str}后全部成熟")
        
        yield event.plain_result("\n".join(lines))
    
    def _format_remain(self, seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            return f"{seconds // 60}分钟"
        else:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            return f"{hours}小时{mins}分钟"
    
    async def _poll_loop(self):
        while self._running:
            try:
                await asyncio.sleep(self.POLL_INTERVAL)
                
                polling_subs = await self.subscription.get_all_polling()
                if not polling_subs:
                    continue
                
                for sub in polling_subs:
                    await self._check_home(sub)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[HomeModule] 轮询异常: {e}")
    
    async def _check_home(self, sub: Dict[str, Any]):
        uid = sub.get("uid")
        session_id = sub.get("session_id")
        user_id = sub.get("user_id")
        
        home_info = await self.api.get_home_info(uid)
        if not home_info:
            logger.debug(f"[HomeModule] 获取家园信息失败: uid={uid}")
            return
        
        plants = self.api.extract_plants(home_info)
        now = self._now_ts()
        
        timers = await self.subscription.get_timers(session_id, user_id)
        
        ripe_count = 0
        growing_count = 0
        max_rip_time = None
        max_rip_plant_id = None
        
        for plant in plants:
            plant_id = plant.get("plant_id")
            state = plant.get("plant_state", 0)
            rip_time = plant.get("plant_rip_time", 0)
            
            if state != 1:
                continue
            
            if rip_time <= now:
                ripe_count += 1
            else:
                growing_count += 1
                if max_rip_time is None or rip_time > max_rip_time:
                    max_rip_time = rip_time
                    max_rip_plant_id = plant_id
        
        if ripe_count > 0:
            await self._notify_ripe(session_id, user_id, uid, ripe_count, growing_count)
        
        if growing_count > 0 and max_rip_plant_id and str(max_rip_plant_id) not in timers:
            await self.subscription.set_timer(session_id, user_id, max_rip_plant_id, max_rip_time)
            await self.subscription.set_polling(session_id, user_id, False)
            asyncio.create_task(self._wait_ripe(session_id, user_id, max_rip_plant_id, max_rip_time, uid))
    
    async def _wait_ripe(self, session_id: str, user_id: str, plant_id: int, rip_time: int, uid: str):
        now = self._now_ts()
        wait_seconds = max(0, rip_time - now)
        
        logger.debug(f"[HomeModule] 设置定时提醒: plant_id={plant_id}, 等待{wait_seconds}秒")
        
        try:
            await asyncio.sleep(wait_seconds)
            
            home_info = await self.api.get_home_info(uid)
            if not home_info:
                return
            
            plants = self.api.extract_plants(home_info)
            now = self._now_ts()
            
            ripe_count = 0
            growing_count = 0
            
            for p in plants:
                state = p.get("plant_state", 0)
                if state == 1:
                    rt = p.get("plant_rip_time", 0)
                    if rt <= now:
                        ripe_count += 1
                    else:
                        growing_count += 1
            
            if ripe_count > 0:
                await self._notify_ripe(session_id, user_id, uid, ripe_count, growing_count)
            
            await self.subscription.clear_timer(session_id, user_id, plant_id)
            
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[HomeModule] 定时提醒异常: {e}")
    
    async def _notify_ripe(self, session_id: str, user_id: str, uid: str, ripe_count: int, growing_count: int):
        chain = [
            Comp.At(qq=str(user_id)),
            Comp.Plain(f" 你的家园({uid})作物已成熟!\n成熟: {ripe_count}株, 生长中: {growing_count}株")
        ]
        
        try:
            await self.context.send_message(session_id, chain)
            logger.info(f"[HomeModule] 已发送成熟提醒: user={user_id}, uid={uid}")
        except Exception as e:
            logger.error(f"[HomeModule] 发送提醒失败: {e}")
