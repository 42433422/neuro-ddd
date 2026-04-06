"""神经反射弧 - 模拟生物神经系统的快速响应机制

设计理念：
模拟生物反射弧的四级结构：
1. 感受器(Receptor): 检测异常信号
2. 传入神经元(Afferent): 快速路由决策
3. 中间神经元(Interneuron): 协调处理
4. 传出神经元(Efferent): 执行纠正动作

目标响应时间：< 1ms
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple

from ..core.signal import NeuroSignal
from ..core.types import (
    ProcessingMode, ProcessingResult,
    ErrorContext, ErrorSeverity, SignalPriority
)

logger = logging.getLogger(__name__)


@dataclass
class ReflexAction:
    """反射动作定义"""
    action_id: str
    name: str
    trigger_conditions: List[Callable]
    handler: Callable
    priority: int = 0
    is_blocking: bool = False
    max_executions: int = -1
    cooldown_ms: float = 0
    execution_count: int = 0
    last_execution: float = 0


@dataclass
class ReflexResult:
    """反射结果"""
    reflex_id: str
    triggered: bool
    action_taken: Optional[str]
    result_data: Any = None
    execution_time_us: float = 0
    blocked_further: bool = False


class ReflexArc:
    """神经反射弧
    
    特性：
    - 超快速响应（目标 < 1ms）
    - 预定义的反射规则
    - 可扩展的动作注册
    - 反射链组合
    """

    def __init__(
        self,
        name: str = "default",
        enabled: bool = True,
        max_reflex_chain_length: int = 10
    ):
        self.name = name
        self.enabled = enabled
        self.max_chain_length = max_reflex_chain_length

        self._receptors: List[Callable[[NeuroSignal], bool]] = []
        self._reflex_actions: List[ReflexAction] = []
        self._interneurons: List[Callable[[NeuroSignal, ReflexAction], bool]] = []

        self._execution_log: List[Dict] = []
        self._metrics = {
            "signals_scanned": 0,
            "reflexes_triggered": 0,
            "reflexes_blocked": 0,
            "avg_response_time_us": 0.0,
            "total_actions_executed": 0,
        }

    def register_receptor(self, receptor_fn: Callable[[NeuroSignal], bool]):
        """注册感受器 - 用于检测需要触发反射的信号"""
        self._receptors.append(receptor_fn)

    def register_action(
        self,
        name: str,
        trigger: Callable,
        handler: Callable,
        priority: int = 0,
        blocking: bool = False,
        max_executions: int = -1,
        cooldown_ms: float = 0
    ) -> str:
        """注册反射动作"""
        import uuid
        action = ReflexAction(
            action_id=uuid.uuid4().hex[:8],
            name=name,
            trigger_conditions=[trigger] if not isinstance(trigger, list) else trigger,
            handler=handler,
            priority=priority,
            is_blocking=blocking,
            max_executions=max_executions,
            cooldown_ms=cooldown_ms,
        )
        self._reflex_actions.append(action)
        self._reflex_actions.sort(key=lambda a: a.priority, reverse=True)
        return action.action_id

    def register_interneuron(self, interneuron_fn: Callable):
        """注册中间神经元 - 用于协调和过滤反射动作"""
        self._interneurons.append(interneuron_fn)

    async def process_signal(self, signal: NeuroSignal) -> ReflexResult:
        """处理信号，触发可能的反射"""
        start = time.perf_counter()
        self._metrics["signals_scanned"] += 1

        if not self.enabled:
            return ReflexResult(
                reflex_id="disabled",
                triggered=False,
                action_taken=None,
                execution_time_us=0,
            )

        needs_reflex = False
        for receptor in self._receptors:
            try:
                result = receptor(signal)
                if asyncio.iscoroutinefunction(receptor):
                    result = await result
                if result:
                    needs_reflex = True
                    break
            except Exception as e:
                logger.debug("Receptor error: %s", e)

        if not needs_reflex:
            elapsed = (time.perf_counter() - start) * 1_000_000
            return ReflexResult(
                reflex_id="none",
                triggered=False,
                action_taken=None,
                execution_time_us=elapsed,
            )

        triggered_actions = []
        blocked = False

        for action in self._reflex_actions:
            if len(triggered_actions) >= self.max_chain_length:
                break
            if blocked:
                break

            should_trigger = await self._check_triggers(signal, action)
            if not should_trigger:
                continue

            should_execute = await self._check_interneurons(signal, action)
            if not should_execute:
                continue

            if not self._can_execute(action):
                continue

            result = await self._execute_action(signal, action)
            triggered_actions.append((action, result))

            if action.is_blocking and result.triggered:
                blocked = True
                self._metrics["reflexes_blocked"] += 1

        elapsed = (time.perf_counter() - start) * 1_000_000
        self._update_metrics(elapsed, len(triggered_actions))

        log_entry = {
            "signal_id": signal.signal_id[:8],
            "signal_type": signal.signal_type,
            "actions_triggered": [a.name for a, _ in triggered_actions],
            "blocked": blocked,
            "response_time_us": round(elapsed, 2),
            "timestamp": time.time(),
        }
        self._execution_log.append(log_entry)

        return ReflexResult(
            reflex_id=self.name,
            triggered=len(triggered_actions) > 0,
            action_taken=", ".join(a.name for a, _ in triggered_actions) or None,
            execution_time_us=elapsed,
            blocked_further=blocked,
        )

    async def _check_triggers(
        self,
        signal: NeuroSignal,
        action: ReflexAction
    ) -> bool:
        """检查动作的所有触发条件"""
        for condition in action.trigger_conditions:
            try:
                result = condition(signal)
                if asyncio.iscoroutinefunction(condition):
                    result = await result
                if not result:
                    return False
            except Exception as e:
                logger.debug("Trigger check error [%s]: %s", action.name, e)
                return False
        return True

    async def _check_interneurons(
        self,
        signal: NeuroSignal,
        action: ReflexAction
    ) -> bool:
        """检查中间神经元是否允许执行"""
        for inter in self._interneurons:
            try:
                allowed = inter(signal, action)
                if asyncio.iscoroutinefunction(inter):
                    allowed = await allowed
                if not allowed:
                    return False
            except Exception as e:
                logger.debug("Interneuron error: %s", e)
        return True

    def _can_execute(self, action: ReflexAction) -> bool:
        """检查动作是否可以执行"""
        now = time.time() * 1000
        
        if action.max_executions > 0 and action.execution_count >= action.max_executions:
            return False
        
        if action.cooldown_ms > 0:
            elapsed = now - action.last_execution
            if elapsed < action.cooldown_ms:
                return False
        
        return True

    async def _execute_action(
        self,
        signal: NeuroSignal,
        action: ReflexAction
    ) -> Tuple[ReflexAction, ReflexResult]:
        """执行单个反射动作"""
        start = time.perf_counter()
        
        try:
            result = action.handler(signal)
            if asyncio.iscoroutinefunction(action.handler):
                result = await result
            
            action.execution_count += 1
            action.last_execution = time.time() * 1000
            self._metrics["total_actions_executed"] += 1

            elapsed = (time.perf_counter() - start) * 1_000_000
            
            return (action, ReflexResult(
                reflex_id=action.action_id,
                triggered=True,
                action_taken=action.name,
                result_data=result,
                execution_time_us=elapsed,
                blocked_further=action.is_blocking,
            ))

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1_000_000
            logger.error("Reflex action '%s' error: %s", action.name, e)
            
            return (action, ReflexResult(
                reflex_id=action.action_id,
                triggered=False,
                action_taken=None,
                execution_time_us=elapsed,
            ))

    def _update_metrics(self, response_time_us: int, actions_count: int):
        """更新指标"""
        if actions_count > 0:
            self._metrics["reflexes_triggered"] += 1
        
        alpha = 0.3
        old_avg = self._metrics["avg_response_time_us"]
        self._metrics["avg_response_time_us"] = (
            alpha * response_time_us + (1 - alpha) * old_avg
        )

    def get_execution_log(self, limit: int = 50) -> List[Dict]:
        """获取执行日志"""
        return list(self._execution_log)[-limit:]

    def get_metrics(self) -> Dict:
        """获取指标"""
        m = dict(self._metrics)
        m["registered_receptors"] = len(self._receptors)
        m["registered_actions"] = len(self._reflex_actions)
        m["registered_interneurons"] = len(self._interneurons)
        m["enabled"] = self.enabled
        return m

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def remove_action(self, action_id: str):
        """移除指定动作"""
        self._reflex_actions = [
            a for a in self._reflex_actions if a.action_id != action_id
        ]

    def __repr__(self) -> str:
        m = self.get_metrics()
        return (
            f"ReflexArc(name={self.name}, "
            f"enabled={m['enabled']}, "
            f"actions={m['registered_actions']}, "
            f"avg_response={m['avg_response_time_us']:.0f}μs)"
        )
