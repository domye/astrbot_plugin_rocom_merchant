"""
洛克王国远行商人查询插件

功能：
1. /商人 - 查询当前远行商人售卖商品
2. 管理员开启群订阅后，每天 08:10, 12:10, 16:10, 20:10 自动推送
3. 用户可设置订阅商品，匹配时@提醒
"""

import asyncio
import httpx
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent, MessageChain
from astrbot.api.star import Context, Star, register, StarTools
from astrbot.core.message.components import Plain, At

from .core.subscription import SubscriptionManager


API_URL = "https://roco.dayun.cool/api/merchant"


@register(
    "astrbot_plugin_rocom_merchant",
    "domye",
    "洛克王国远行商人查询",
    "1.0.0",
    "https://github.com/astrbot/astrbot_plugin_rocom_merchant"
)
class RocomMerchantPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self._client: Optional[httpx.AsyncClient] = None
        
        data_dir = str(StarTools.get_data_dir())
        self.subscription_mgr = SubscriptionManager(data_dir)
        
        self._scheduler_task = None
        self._last_push_round: Dict[str, str] = {}
        
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("[RocomMerchant] 插件初始化完成，定时推送任务已启动")

    async def terminate(self):
        if self._scheduler_task and not self._scheduler_task.done():
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    def _cn_tz(self) -> timezone:
        return timezone(timedelta(hours=8))

    def _get_push_times(self, base: datetime | None = None) -> List[datetime]:
        now = base or datetime.now(self._cn_tz())
        if now.tzinfo is None:
            now = now.replace(tzinfo=self._cn_tz())
        return [
            now.replace(hour=8, minute=10, second=0, microsecond=0),
            now.replace(hour=12, minute=10, second=0, microsecond=0),
            now.replace(hour=16, minute=10, second=0, microsecond=0),
            now.replace(hour=20, minute=10, second=0, microsecond=0),
        ]

    def _next_push_time(self, now: datetime | None = None) -> datetime:
        current = now or datetime.now(self._cn_tz())
        if current.tzinfo is None:
            current = current.replace(tzinfo=self._cn_tz())
        for push_time in self._get_push_times(current):
            if push_time > current:
                return push_time
        next_day = current + timedelta(days=1)
        return self._get_push_times(next_day)[0]

    async def _fetch_merchant_data(self, max_retries: int = 3, retry_delay: float = 1.0) -> Optional[Dict[str, Any]]:
        for attempt in range(max_retries):
            try:
                client = await self._get_client()
                resp = await client.get(f"{API_URL}?t={int(datetime.now().timestamp())}")
                if resp.status_code != 200:
                    logger.warning(f"[RocomMerchant] API 返回状态码: {resp.status_code}, 尝试 {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                    return None
                data = resp.json()
                if data.get("success"):
                    return data
                logger.warning(f"[RocomMerchant] API 返回失败: {data.get('error', '未知')}, 尝试 {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return None
            except Exception as e:
                logger.error(f"[RocomMerchant] 获取商人数据失败: {e}, 尝试 {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return None
        return None

    def _format_items(self, items: List[str]) -> str:
        if not items:
            return "暂无商品"
        return "、".join(items)

    def _get_round_id(self, data: Dict[str, Any]) -> str:
        round_info = data.get("roundInfo", {})
        date = round_info.get("date", datetime.now(self._cn_tz()).strftime("%Y-%m-%d"))
        current = round_info.get("current", "unknown")
        return f"{date}-{current}"

    async def _scheduler_loop(self):
        logger.info("[RocomMerchant] 定时推送循环已启动")
        while True:
            try:
                now = datetime.now(self._cn_tz())
                next_push = self._next_push_time(now)
                sleep_seconds = max(1, (next_push - now).total_seconds())
                logger.debug(
                    f"[RocomMerchant] 下次推送时间: {next_push.strftime('%H:%M')}"
                )
                await asyncio.sleep(sleep_seconds)
                await self._do_scheduled_push()
            except asyncio.CancelledError:
                logger.info("[RocomMerchant] 定时推送循环已取消")
                break
            except Exception as e:
                logger.error(f"[RocomMerchant] 定时推送循环异常: {e}")
                await asyncio.sleep(60)

    async def _do_scheduled_push(self):
        enabled_groups = await self.subscription_mgr.get_all_enabled_groups()
        if not enabled_groups:
            logger.debug("[RocomMerchant] 没有开启订阅的群")
            return

        data = await self._fetch_merchant_data()
        if not data or not data.get("success"):
            logger.warning("[RocomMerchant] 获取商人数据失败，跳过本次推送")
            return

        items = data.get("items", [])
        round_info = data.get("roundInfo", {})
        round_id = self._get_round_id(data)

        for session_id, group_data in enabled_groups.items():
            try:
                user_items_map = group_data.get("user_items", {})
                matched_users: Dict[str, List[str]] = {}
                
                for user_id, subscribed_items in user_items_map.items():
                    matched = [item for item in subscribed_items if item in items]
                    if matched:
                        matched_users[user_id] = matched

                chain = MessageChain()
                chain.message(
                    f"【远行商人】{round_info.get('current', '')}\n"
                    f"当前商品: {self._format_items(items)}"
                )

                if matched_users:
                    chain.message("\n\n订阅提醒:")
                    for user_id, matched_items in matched_users.items():
                        chain.chain.append(At(qq=str(user_id)))
                        chain.message(f" 命中: {self._format_items(matched_items)}")

                await self.context.send_message(session_id, chain)
                logger.info(f"[RocomMerchant] 已推送到 {session_id}")
            except Exception as e:
                logger.error(f"[RocomMerchant] 推送到 {session_id} 失败: {e}")

    @filter.command("商人")
    async def query_merchant(self, event: AstrMessageEvent):
        """查询当前远行商人售卖商品"""
        data = await self._fetch_merchant_data()
        if not data:
            yield event.plain_result("获取商人数据失败，请稍后重试")
            return

        items = data.get("items", [])
        round_info = data.get("roundInfo", {})

        msg = f"【远行商人】{round_info.get('current', '-')}\n"
        msg += f"当前商品: {self._format_items(items)}"

        yield event.plain_result(msg)

    @filter.command("商人订阅 开启")
    async def subscribe_open(self, event: AstrMessageEvent):
        """管理员开启群订阅（每天 08:10, 12:10, 16:10, 20:10 自动推送）"""
        if not await self._is_admin(event):
            yield event.plain_result("仅管理员可执行此操作")
            return

        session_id = event.unified_msg_origin
        await self.subscription_mgr.set_group_subscription(session_id, True)
        yield event.plain_result(
            "已开启远行商人订阅\n"
            "推送时间: 每天 08:10, 12:10, 16:10, 20:10\n"
            "用户可使用 /商人订阅添加 <商品名> 订阅特定商品"
        )

    @filter.command("商人订阅 关闭")
    async def subscribe_close(self, event: AstrMessageEvent):
        """管理员关闭群订阅"""
        if not await self._is_admin(event):
            yield event.plain_result("仅管理员可执行此操作")
            return

        session_id = event.unified_msg_origin
        await self.subscription_mgr.set_group_subscription(session_id, False)
        yield event.plain_result("已关闭远行商人订阅")

    @filter.command("商人订阅添加")
    async def subscribe_add(self, event: AstrMessageEvent, item_name: str = ""):
        """添加商品订阅，当该商品出现时会@提醒"""
        if not item_name:
            yield event.plain_result("请输入商品名称，例如: /商人订阅添加 国王球")
            return

        session_id = event.unified_msg_origin
        user_id = event.get_sender_id()
        
        added = await self.subscription_mgr.add_user_item(session_id, user_id, item_name)
        if added:
            yield event.plain_result(f"已添加订阅: {item_name}")
        else:
            yield event.plain_result(f"你已订阅过该商品: {item_name}")

    @filter.command("商人订阅删除")
    async def subscribe_remove(self, event: AstrMessageEvent, item_name: str = ""):
        """删除商品订阅"""
        if not item_name:
            yield event.plain_result("请输入商品名称，例如: /商人订阅删除 国王球")
            return

        session_id = event.unified_msg_origin
        user_id = event.get_sender_id()
        
        removed = await self.subscription_mgr.remove_user_item(session_id, user_id, item_name)
        if removed:
            yield event.plain_result(f"已删除订阅: {item_name}")
        else:
            yield event.plain_result(f"未找到订阅: {item_name}")

    @filter.command("商人订阅列表")
    async def subscribe_list(self, event: AstrMessageEvent):
        """查看当前群的商品订阅列表"""
        session_id = event.unified_msg_origin
        sub = await self.subscription_mgr.get_group_subscriptions(session_id)
        
        if not sub:
            yield event.plain_result("当前群未开启订阅")
            return

        enabled = "已开启" if sub.get("enabled") else "已关闭"
        user_items = sub.get("user_items", {})
        
        if not user_items:
            yield event.plain_result(f"订阅状态: {enabled}\n暂无用户订阅商品")
            return

        lines = [f"订阅状态: {enabled}\n用户订阅:"]
        for user_id, items in user_items.items():
            lines.append(f"  - 用户{user_id}: {self._format_items(items)}")
        
        yield event.plain_result("\n".join(lines))

    @filter.command("商人订阅清空")
    async def subscribe_clear(self, event: AstrMessageEvent):
        """清空自己的所有商品订阅"""
        session_id = event.unified_msg_origin
        user_id = event.get_sender_id()
        
        cleared = await self.subscription_mgr.clear_user_items(session_id, user_id)
        if cleared:
            yield event.plain_result("已清空你的所有商品订阅")
        else:
            yield event.plain_result("你没有订阅任何商品")

    async def _is_admin(self, event: AstrMessageEvent) -> bool:
        if event.is_admin():
            return True
        if event.is_private_chat():
            return False
        sender_id = str(event.get_sender_id())
        role = str(getattr(event, "role", "") or "").lower()
        try:
            group = await event.get_group()
            if group:
                owner_candidates = [
                    getattr(group, "group_owner", None),
                    getattr(group, "owner_id", None),
                    getattr(group, "group_owner_id", None),
                ]
                if any(str(owner) == sender_id for owner in owner_candidates if owner):
                    return True
                admins = [str(x) for x in getattr(group, "group_admins", [])]
                if sender_id in admins:
                    return True
                if role in {"admin", "owner"}:
                    return True
        except Exception:
            if role in {"admin", "owner"}:
                return True
        return False
