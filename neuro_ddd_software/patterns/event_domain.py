"""事件领域模板 - Neuro-DDD软件层的事件驱动模式

用于实现发布-订阅模式的事件处理，
支持事件广播、过滤、聚合等高级特性。
"""

import asyncio
import logging
from ..core.domain import SoftwareDomain
from ..core.types import DomainRole, ProcessingMode, ProcessingContext, ProcessingResult
from ..core.signal import NeuroSignal

logger = logging.getLogger(__name__)


class EventDomain(SoftwareDomain):
    """事件领域模板
    
    适用场景：
    - 事件发布/订阅
    - 消息队列封装
    - 通知系统
    - 跨领域事件协调
    """

    def __init__(
        self,
        event_channel: str = "default",
        **kwargs
    ):
        super().__init__(
            domain_name=f"event:{event_channel}",
            role=DomainRole.CROSS_CUTTING,
            default_mode=ProcessingMode.DUAL,
            **kwargs
        )
        self.event_channel = event_channel
        self._subscribers: dict = {}  
        self._event_history: list = []
        self._event_filters: list = []

    async def subscribe(
        self,
        event_type: str,
        subscriber_name: str,
        handler,
        filter_fn=None
    ):
        """订阅事件"""
        key = (event_type, subscriber_name)
        self._subscribers[key] = {
            "handler": handler,
            "filter": filter_fn,
        }
        logger.debug("Subscriber '%s' subscribed to '%s'", subscriber_name, event_type)

    async def unsubscribe(self, event_type: str, subscriber_name: str):
        """取消订阅"""
        key = (event_type, subscriber_name)
        self._subscribers.pop(key, None)

    async def publish_event(
        self,
        event_type: str,
        event_data: dict = None,
        target_subscribers: list = None,
        wait_for_handlers: bool = False
    ) -> ProcessingResult:
        """发布事件"""
        signal = NeuroSignal(
            signal_type=f"event:{event_type}",
            source_domain=self.domain_name,
            payload={
                "event_type": event_type,
                "event_data": event_data or {},
                "channel": self.event_channel,
            },
        )

        matching_handlers = []
        for (et, sub), info in self._subscribers.items():
            if et == event_type or et == "*":
                if target_subscribers and sub not in target_subscribers:
                    continue
                if info["filter"]:
                    should_receive = info["filter"](event_data)
                    if asyncio.iscoroutinefunction(info["filter"]):
                        should_receive = await info["filter"](event_data)
                    if not should_receive:
                        continue
                matching_handlers.append((sub, info["handler"]))

        self._event_history.append({
            "type": event_type,
            "channel": self.event_channel,
            "subscribers_notified": len(matching_handlers),
            "timestamp": __import__("time").time(),
        })

        if wait_for_handlers and matching_handlers:
            tasks = [h(event_data) for _, h in matching_handlers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful = sum(1 for r in results if not isinstance(r, Exception))
            return ProcessingResult(
                success=True,
                result_data={
                    "event_type": event_type,
                    "notified": len(matching_handlers),
                    "successful": successful,
                    "results": [r for r in results if not isinstance(r, Exception)],
                },
                signals_generated=[signal],
            )
        else:
            for _, handler in matching_handlers:
                try:
                    result = handler(event_data)
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.create_task(result)
                except Exception as e:
                    logger.error("Event handler error: %s", e)

            return ProcessingResult(
                success=True,
                result_data={
                    "event_type": event_type,
                    "notified": len(matching_handlers),
                    "fire_and_forget": True,
                },
                signals_generated=[signal],
            )

    async def async_process_signal(
        self,
        signal: NeuroSignal,
        context: ProcessingContext
    ) -> ProcessingResult:
        event_type = signal.payload.get("event_type", signal.signal_type.replace("event:", ""))
        event_data = signal.payload.get("event_data", {})
        
        return await self.publish_event(
            event_type=event_type,
            event_data=event_data,
            wait_for_handlers=context.metadata.get("wait_for_handlers", False),
        )

    def get_event_history(self, limit: int = 50) -> list:
        return list(self._event_history)[-limit:]

    def get_subscriber_count(self, event_type: str = None) -> int:
        if event_type:
            return sum(1 for (et, _) in self._subscribers if et == event_type)
        return len(self._subscribers)

    def __repr__(self) -> str:
        return (
            f"EventDomain(channel={self.event_channel}, "
            f"subscribers={len(self._subscribers)}, "
            f"events={len(self._event_history)})"
        )
