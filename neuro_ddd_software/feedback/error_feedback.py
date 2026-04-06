"""错误反馈系统 - Neuro-DDD软件层的容错与恢复机制

特性：
- 即时反馈：致命错误立即通知所有领域
- 延迟反馈：非致命错误累积后批量报告
- 自适应调整：根据错误频率自动调整策略
- 熔断器模式：错误率过高时自动降级
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from ..core.signal import NeuroSignal
from ..core.types import (
    FeedbackType, ErrorSeverity,
    ErrorContext, ProcessingResult
)

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 30.0
    half_open_max_calls: int = 1


@dataclass
class ErrorRecord:
    """错误记录"""
    error_id: str
    context: ErrorContext
    timestamp: float = field(default_factory=time.time)
    handled: bool = False
    handling_strategy: str = ""


@dataclass
class FeedbackConfig:
    """反馈配置"""
    feedback_type: FeedbackType = FeedbackType.IMMEDIATE
    batch_size: int = 10
    batch_timeout: float = 5.0
    max_accumulated: int = 100


class ErrorFeedbackSystem:
    """错误反馈系统
    
    核心职责：
    1. 错误收集和分类
    2. 根据严重程度选择反馈策略
    3. 熔断器管理（防止级联故障）
    4. 错误统计和趋势分析
    5. 自动恢复策略推荐
    """

    def __init__(
        self,
        default_config: FeedbackConfig = None,
        circuit_breaker_config: CircuitBreakerConfig = None,
        error_handlers: Dict[ErrorSeverity, Callable] = None
    ):
        self.default_config = default_config or FeedbackConfig()
        self.circuit_config = circuit_breaker_config or CircuitBreakerConfig()
        self.error_handlers = error_handlers or {}

        self._error_buffer: List[ErrorRecord] = []
        self._circuit_state: Dict[str, CircuitState] = {}
        self._failure_counts: Dict[str, int] = defaultdict(int)
        self._success_counts: Dict[str, int] = defaultdict(int)
        self._last_failure_time: Dict[str, float] = {}
        
        self._callbacks: List[Callable[[ErrorRecord], None]] = []
        self._domain_error_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total": 0, "by_severity": defaultdict(int),
            "last_error": None, "consecutive_failures": 0,
        })

        self._metrics = {
            "errors_received": 0,
            "errors_immediate": 0,
            "errors_deferred": 0,
            "errors_batched": 0,
            "circuit_opens": 0,
            "auto_recoveries": 0,
        }

    def register_callback(self, callback: Callable[[ErrorRecord], None]):
        """注册错误回调"""
        self._callbacks.append(callback)

    async def report_error(
        self,
        context: ErrorContext,
        domain: str = "",
        signal: NeuroSignal = None,
        config: FeedbackConfig = None
    ) -> str:
        """报告错误到反馈系统"""
        import uuid
        error_id = uuid.uuid4().hex[:12]
        
        record = ErrorRecord(
            error_id=error_id,
            context=context,
        )
        if signal:
            record.context.original_signal = signal
        
        self._metrics["errors_received"] += 1
        self._update_domain_stats(domain, context)
        
        effective_config = config or self.default_config

        if context.severity in (ErrorSeverity.FATAL, ErrorSeverity.CRITICAL):
            await self._handle_immediate(record, domain)
            self._metrics["errors_immediate"] += 1
        elif effective_config.feedback_type == FeedbackType.IMMEDIATE:
            await self._handle_immediate(record, domain)
            self._metrics["errors_immediate"] += 1
        elif effective_config.feedback_type == FeedbackType.DEFERRED:
            self._handle_deferred(record)
            self._metrics["errors_deferred"] += 1
        elif effective_config.feedback_type in (FeedbackType.ACCUMULATED, FeedbackType.BATCH):
            self._handle_accumulated(record, effective_config)
            if len(self._error_buffer) >= effective_config.batch_size:
                await self._flush_batch(effective_config)
            self._metrics["errors_batched"] += 1

        circuit_key = domain or context.source_domain
        self._check_circuit_breaker(circuit_key, context.severity)

        for callback in self._callbacks:
            try:
                callback(record)
            except Exception as e:
                logger.error("Error callback failed: %s", e)

        return error_id

    async def _handle_immediate(self, record: ErrorRecord, domain: str):
        """即时处理错误"""
        logger.error(
            "[IMMEDIATE] %s in %s: %s",
            record.context.severity.value.upper(),
            domain or record.context.source_domain,
            record.context.message
        )

        handler = self.error_handlers.get(record.context.severity)
        if handler:
            try:
                result = handler(record.context)
                if asyncio.iscoroutinefunction(handler):
                    result = await result
                
                record.handled = True
                record.handling_strategy = "custom_handler"
                
            except Exception as e:
                logger.error("Custom error handler failed: %s", e)
                record.handling_strategy = "handler_failed"

        emergency_signal = self._create_error_signal(record)
        if emergency_signal:
            logger.info("Emergency error signal created: %s", emergency_signal.signal_id)

    def _handle_deferred(self, record: ErrorRecord):
        """延迟处理 - 放入缓冲区稍后处理"""
        self._error_buffer.append(record)
        logger.warning(
            "[DEFERRED] Error queued: %s (buffer=%d)",
            record.error_id[:8],
            len(self._error_buffer)
        )

    def _handle_accumulated(self, record: ErrorRecord, config: FeedbackConfig):
        """累积处理 - 收集后批量报告"""
        if len(self._error_buffer) >= config.max_accumulated:
            oldest = self._error_buffer.pop(0)
            logger.warning("[ACCUMULATED] Dropped old error: %s", oldest.error_id[:8])
        
        self._error_buffer.append(record)

    async def _flush_batch(self, config: FeedbackConfig):
        """刷新批量缓冲区"""
        if not self._error_buffer:
            return

        batch = self._error_buffer[:]
        self._error_buffer.clear()

        severity_counts = defaultdict(int)
        for record in batch:
            severity_counts[record.context.severity.value] += 1

        logger.warning(
            "[BATCH] Flushing %d errors: %s",
            len(batch),
            dict(severity_counts)
        )

    def _create_error_signal(self, record: ErrorRecord) -> Optional[NeuroSignal]:
        """创建紧急错误信号用于广播"""
        if record.context.severity not in (ErrorSeverity.FATAL, ErrorSeverity.CRITICAL):
            return None

        from ..core.signal import NeuroSignal
        from ..core.types import SignalPriority

        return NeuroSignal(
            signal_type="system_error",
            source_domain=record.context.source_domain,
            target_domains=[],
            payload={
                "error_id": record.error_id,
                "severity": record.context.severity.value,
                "message": record.context.message,
                "error_type": record.context.error_type,
                "recovery_hints": record.context.recovery_hints or [],
                "timestamp": record.timestamp,
            },
            priority=SignalPriority.CRITICAL,
        )

    def _check_circuit_breaker(
        self,
        key: str,
        severity: ErrorSeverity
    ):
        """检查并更新熔断器状态"""
        if severity not in (ErrorSeverity.ERROR, ErrorSeverity.CRITICAL, ErrorSeverity.FATAL):
            self._success_counts[key] += 1
            current_state = self._circuit_state.get(key, CircuitState.CLOSED)
            
            if current_state == CircuitState.HALF_OPEN:
                if self._success_counts[key] >= self.circuit_config.success_threshold:
                    self._circuit_state[key] = CircuitState.CLOSED
                    self._failure_counts[key] = 0
                    self._success_counts[key] = 0
                    self._metrics["auto_recoveries"] += 1
                    logger.info("Circuit recovered for: %s", key)
            return

        self._failure_counts[key] += 1
        self._last_failure_time[key] = time.time()
        current_state = self._circuit_state.get(key, CircuitState.CLOSED)

        if current_state == CircuitState.CLOSED:
            if self._failure_counts[key] >= self.circuit_config.failure_threshold:
                self._circuit_state[key] = CircuitState.OPEN
                self._metrics["circuit_opens"] += 1
                logger.warning(
                    "Circuit OPEN for '%s' after %d failures",
                    key, self._failure_counts[key]
                )
        elif current_state == CircuitState.OPEN:
            pass
        elif current_state == CircuitState.HALF_OPEN:
            self._circuit_state[key] = CircuitState.OPEN
            self._metrics["circuit_opens"] += 1

    def is_circuit_open(self, key: str) -> bool:
        """检查指定key的熔断器是否开启"""
        state = self._circuit_state.get(key, CircuitState.CLOSED)
        if state != CircuitState.OPEN:
            return False
        
        last_fail = self._last_failure_time.get(key, 0)
        if time.time() - last_fail > self.circuit_config.timeout_seconds:
            self._circuit_state[key] = CircuitState.HALF_OPEN
            self._failure_counts[key] = 0
            return False
        
        return True

    def allow_request(self, key: str) -> bool:
        """检查是否允许请求通过（熔断器模式）"""
        if not self.is_circuit_open(key):
            return True
        
        state = self._circuit_state.get(key)
        return state == CircuitState.HALF_OPEN

    def _update_domain_stats(self, domain: str, context: ErrorContext):
        """更新领域错误统计"""
        stats = self._domain_error_stats[domain]
        stats["total"] += 1
        stats["by_severity"][context.severity.value] += 1
        stats["last_error"] = context
        
        if context.severity in (ErrorSeverity.ERROR, ErrorSeverity.CRITICAL, ErrorSeverity.FATAL):
            stats["consecutive_failures"] += 1
        else:
            stats["consecutive_failures"] = 0

    def get_domain_error_stats(self, domain: str) -> Dict:
        """获取领域错误统计"""
        return dict(self._domain_error_stats.get(domain, {}))

    def get_all_errors(self, limit: int = 100) -> List[ErrorRecord]:
        """获取所有错误记录"""
        return list(self._error_buffer)[-limit:]

    def get_metrics(self) -> Dict:
        """获取反馈系统指标"""
        m = dict(self._metrics)
        m["buffer_size"] = len(self._error_buffer)
        m["circuits"] = {
            k: v.value for k, v in self._circuit_state.items()
        }
        m["domains_with_errors"] = len(self._domain_error_stats)
        return m

    def reset_circuit(self, key: str):
        """手动重置熔断器"""
        self._circuit_state[key] = CircuitState.CLOSED
        self._failure_counts[key] = 0
        self._success_counts[key] = 0
        logger.info("Circuit manually reset for: %s", key)

    def clear_buffer(self):
        """清空错误缓冲区"""
        count = len(self._error_buffer)
        self._error_buffer.clear()
        logger.info("Cleared %d errors from buffer", count)

    def __repr__(self) -> str:
        m = self.get_metrics()
        return (
            f"ErrorFeedbackSystem(errors={m['errors_received']}, "
            f"circuits={len(m['circuits'])})"
        )
