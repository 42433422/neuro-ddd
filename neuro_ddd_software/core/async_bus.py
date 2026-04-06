"""异步神经广播总线 - Neuro-DDD软件层核心通信中枢

特性：
- 完全异步（asyncio）实现
- 优先级队列调度
- 订阅/发布模式
- 背压控制
- 死信队列
- 信号过滤与路由
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .signal import NeuroSignal
from .types import SignalPriority, ProcessingResult

logger = logging.getLogger(__name__)


@dataclass
class BusMetrics:
    """总线运行指标"""
    signals_broadcast: int = 0
    signals_delivered: int = 0
    signals_failed: int = 0
    signals_filtered: int = 0
    dead_letters: int = 0
    avg_delivery_time_ms: float = 0.0
    queue_size: int = 0
    subscribers_count: int = 0


class AsyncNeuroBus:
    """异步神经广播总线
    
    核心职责：
    1. 信号广播：将信号同步/异步分发至所有订阅的领域
    2. 优先级调度：高优先级信号优先处理
    3. 订阅管理：领域可订阅特定类型的信号
    4. 流量控制：背压机制防止信号洪泛
    5. 可观测性：完整的监控指标和日志
    """

    def __init__(
        self,
        max_queue_size: int = 10000,
        enable_dead_letter: bool = True,
        back_pressure_threshold: float = 0.8
    ):
        self._domains: Dict[str, Any] = {}
        self._subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self._signal_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._broadcast_log: List[Dict] = []
        
        self._priority_queues: Dict[SignalPriority, asyncio.Queue] = {
            p: asyncio.Queue(maxsize=max_queue_size // 5)
            for p in SignalPriority
        }
        
        self._dead_letter_queue: Optional[asyncio.Queue] = (
            asyncio.Queue() if enable_dead_letter else None
        )
        
        self._max_queue_size = max_queue_size
        self._back_pressure_threshold = back_pressure_threshold
        self._metrics = BusMetrics()
        self._lock = asyncio.Lock()
        self._running = False

    async def register_domain(self, domain) -> None:
        """注册领域到总线"""
        domain_name = domain.domain_name if hasattr(domain, 'domain_name') else str(domain)
        async with self._lock:
            if domain_name in self._domains:
                raise ValueError(f"Domain '{domain_name}' already registered")
            self._domains[domain_name] = domain
            self._metrics.subscribers_count = len(self._domains)
            logger.info("Domain registered: %s", domain_name)

    async def unregister_domain(self, domain_name: str) -> None:
        """从总线注销领域"""
        async with self._lock:
            if domain_name not in self._domains:
                raise KeyError(f"Domain '{domain_name}' not registered")
            del self._domains[domain_name]
            self._subscriptions.pop(domain_name, None)
            self._metrics.subscribers_count = len(self._domains)
            logger.info("Domain unregistered: %s", domain_name)

    def subscribe(
        self,
        domain_name: str,
        signal_types: List[str],
        handler: Callable
    ) -> None:
        """领域订阅特定类型的信号
        
        Args:
            domain_name: 领域名称
            signal_types: 要订阅的信号类型列表，["*"] 表示全部
            handler: 信号处理回调 (async def handler(signal) -> ProcessingResult)
        """
        for sig_type in signal_types:
            self._subscriptions[domain_name].add(sig_type)
            self._signal_handlers[sig_type].append({
                "domain": domain_name,
                "handler": handler,
            })
        logger.debug(
            "Domain '%s' subscribed to: %s",
            domain_name, signal_types
        )

    def unsubscribe(
        self,
        domain_name: str,
        signal_types: List[str] = None
    ) -> None:
        """取消订阅"""
        if signal_types is None:
            self._subscriptions.pop(domain_name, None)
            for handlers in self._signal_handlers.values():
                self._signal_handlers = [
                    h for h in handlers if h["domain"] != domain_name
                ]
        else:
            for sig_type in signal_types:
                self._subscriptions[domain_name].discard(sig_type)
                self._signal_handlers[sig_type] = [
                    h for h in self._signal_handlers.get(sig_type, [])
                    if h["domain"] != domain_name
                ]

    async def broadcast(
        self,
        signal: NeuroSignal,
        wait_for_results: bool = False,
        timeout: float = 30.0
    ) -> List[ProcessingResult]:
        """广播信号到所有匹配的目标领域
        
        这是核心方法！实现：
        1. TTL检查
        2. 目标域解析
        3. 并行分发
        4. 结果收集
        
        Args:
            signal: 待广播的神经信号
            wait_for_results: 是否等待所有处理完成
            timeout: 超时时间（秒）
            
        Returns:
            处理结果列表
        """
        start_time = time.time()
        self._metrics.signals_broadcast += 1

        if signal.is_expired():
            logger.warning("Signal expired: %s", signal.signal_id)
            await self._send_to_dead_letter(signal, "expired")
            return []

        target_handlers = self._resolve_targets(signal)
        if not target_handlers:
            self._metrics.signals_filtered += 1
            logger.debug("No targets for signal %s (type=%s)", signal.signal_id, signal.signal_type)
            return []

        signal.decrement_ttl()
        results = []

        if wait_for_results:
            tasks = [
                self._deliver_to_handler(signal, handler)
                for handler in target_handlers
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [
                r if isinstance(r, ProcessingResult)
                else ProcessingResult(success=False, error=str(r))
                for r in results
            ]
        else:
            for handler in target_handlers:
                asyncio.create_task(self._deliver_to_handler(signal, handler))
            results = [ProcessingResult(success=True)]

        delivery_time = (time.time() - start_time) * 1000
        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count

        self._metrics.signals_delivered += success_count
        self._metrics.signals_failed += fail_count
        self._update_avg_time(delivery_time)

        log_entry = {
            "signal_id": signal.signal_id,
            "signal_type": signal.signal_type,
            "source": signal.source_domain,
            "target_count": len(target_handlers),
            "success_count": success_count,
            "fail_count": fail_count,
            "delivery_time_ms": round(delivery_time, 3),
            "timestamp": time.time(),
        }
        self._broadcast_log.append(log_entry)

        return results

    async def publish(self, signal: NeuroSignal) -> None:
        """Fire-and-forget 发布模式（不等待结果）"""
        await self.broadcast(signal, wait_for_results=False)

    async def publish_priority(
        self,
        signal: NeuroSignal,
        priority: SignalPriority = None
    ) -> None:
        """通过优先级队列发布信号"""
        effective_priority = priority or signal.priority
        try:
            self._priority_queues[effective_priority].put_nowait(signal)
        except asyncio.QueueFull:
            await self._handle_back_pressure(signal)
            try:
                await asyncio.wait_for(
                    self._priority_queues[effective_priority].put(signal),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                await self._send_to_dead_letter(signal, "queue_full")

    def _resolve_targets(self, signal: NeuroSignal) -> List[Dict]:
        """解析信号的目标处理器"""
        targets = []

        if signal.target_domains:
            for domain_name in signal.target_domains:
                if "*" in self._subscriptions.get(domain_name, set()):
                    for handler_info in self._signal_handlers.get("*", []):
                        if handler_info["domain"] == domain_name:
                            targets.append(handler_info)
                elif signal.signal_type in self._subscriptions.get(domain_name, set()):
                    for handler_info in self._signal_handlers.get(signal.signal_type, []):
                        if handler_info["domain"] == domain_name:
                            targets.append(handler_info)
        else:
            all_matching = self._signal_handlers.get(signal.signal_type, [])
            wildcard_matching = self._signal_handlers.get("*", [])
            targets.extend(all_matching)
            targets.extend(wildcard_matching)

        seen = set()
        unique_targets = []
        for t in targets:
            key = (t["domain"], id(t["handler"]))
            if key not in seen:
                seen.add(key)
                unique_targets.append(t)

        return unique_targets

    async def _deliver_to_handler(
        self,
        signal: NeuroSignal,
        handler_info: Dict
    ) -> ProcessingResult:
        """将信号投递给单个处理器"""
        domain_name = handler_info["domain"]
        handler = handler_info["handler"]
        start = time.time()

        try:
            result = handler(signal)
            if asyncio.iscoroutine(result):
                result = await result
            
            duration = (time.time() - start) * 1000
            signal.add_processing_record(
                domain_name, "delivered",
                "success" if getattr(result, 'success', True) else "failed",
                duration
            )
            return result if isinstance(result, ProcessingResult) else ProcessingResult(
                success=True, result_data=result
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            signal.add_processing_record(domain_name, "error", str(e), duration)
            logger.exception("Error delivering to %s: %s", domain_name, e)
            await signal.fail(e)
            return ProcessingResult(success=False, error=str(e))

    async def _send_to_dead_letter(self, signal: NeuroSignal, reason: str):
        """发送到死信队列"""
        if self._dead_letter_queue is not None:
            await self._dead_letter_queue.put({"signal": signal, "reason": reason})
            self._metrics.dead_letters += 1
            logger.warning("Dead letter: %s (reason=%s)", signal.signal_id, reason)

    async def _handle_back_pressure(self, signal: NeuroSignal):
        """处理背压情况"""
        total_size = sum(q.qsize() for q in self._priority_queues())
        capacity = self._max_queue_size
        usage = total_size / capacity if capacity > 0 else 1.0

        if usage > self._back_pressure_threshold:
            logger.warning(
                "Back pressure triggered: %.1f%% usage (%d/%d)",
                usage * 100, total_size, capacity
            )
            if signal.priority >= SignalPriority.LOW:
                await self._send_to_dead_letter(signal, "back_pressure")

    def _update_avg_time(self, new_time: float):
        """更新平均投递时间（指数移动平均）"""
        alpha = 0.3
        if self._metrics.avg_delivery_time_ms == 0:
            self._metrics.avg_delivery_time_ms = new_time
        else:
            self._metrics.avg_delivery_time_ms = (
                alpha * new_time + (1 - alpha) * self._metrics.avg_delivery_time_ms
            )

    def get_metrics(self) -> BusMetrics:
        """获取总线运行指标"""
        self._metrics.queue_size = sum(q.qsize() for q in self._priority_queues.values())
        return self._metrics

    def get_broadcast_log(self, limit: int = 100) -> List[Dict]:
        """获取广播日志"""
        return self._broadcast_log[-limit:]

    async def get_dead_letters(self) -> List[Dict]:
        """获取死信队列中的信号"""
        if self._dead_letter_queue is None:
            return []
        letters = []
        while not self._dead_letter_queue.empty():
            letters.append(self._dead_letter_queue.get_nowait())
        return letters

    def get_registered_domains(self) -> List[str]:
        """获取已注册的领域列表"""
        return list(self._domains.keys())

    async def shutdown(self, wait_for_pending: bool = True):
        """优雅关闭总线"""
        logger.info("Shutting down AsyncNeuroBus...")
        self._running = False
        if wait_for_pending:
            for q in self._priority_queues.values():
                await q.join()

    async def __aenter__(self):
        self._running = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()

    def __repr__(self) -> str:
        m = self.get_metrics()
        return (
            f"AsyncNeuroBus(domains={m.subscribers_count}, "
            f"broadcast={m.signals_broadcast}, "
            f"delivered={m.signals_delivered}, "
            f"failed={m.signals_failed})"
        )
