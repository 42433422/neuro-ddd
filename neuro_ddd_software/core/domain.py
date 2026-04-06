"""软件领域基类 - Neuro-DDD软件层的核心抽象

提供：
- 异步信号处理接口
- 内置重试机制
- 生命周期管理
- 健康检查
- 信号过滤
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Set

from .signal import NeuroSignal
from .types import (
    DomainRole, ProcessingMode, ProcessingContext,
    ProcessingResult, ErrorContext, ErrorSeverity
)

logger = logging.getLogger(__name__)


class SoftwareDomain(ABC):
    """软件领域基类 - 所有Neuro-DDD领域的父类
    
    设计理念：
    - 每个领域是一个独立的自治单元
    - 通过神经总线进行松耦合通信
    - 支持显意识/潜意识双模式处理
    - 内置容错和重试机制
    """

    def __init__(
        self,
        domain_name: str,
        role: DomainRole = DomainRole.GENERIC,
        supported_signals: List[str] = None,
        default_mode: ProcessingMode = ProcessingMode.DUAL,
        retry_config: Dict = None
    ):
        self.domain_name = domain_name
        self.role = role
        self.supported_signals = set(supported_signals or ["*"])
        self.default_mode = default_mode
        
        self.retry_config = retry_config or {
            "max_retries": 3,
            "base_delay": 0.1,
            "max_delay": 5.0,
            "exponential_base": 2.0,
            "jitter": True,
        }
        
        self._state = "initialized"
        self._bus = None
        self._signal_filters: List[Callable[[NeuroSignal], bool]] = []
        self._preprocessors: List[Callable] = []
        self._postprocessors: List[Callable] = []
        self._metrics = {
            "signals_received": 0,
            "signals_processed": 0,
            "signals_errored": 0,
            "avg_process_time_ms": 0.0,
        }

    @property
    def state(self) -> str:
        return self._state

    @property
    def bus(self):
        return self._bus

    async def set_bus(self, bus) -> None:
        """设置关联的总线"""
        self._bus = bus
        await bus.register_domain(self)

    def add_signal_filter(self, filter_fn: Callable[[NeuroSignal], bool]):
        """添加信号过滤器 - 返回False则拒绝处理该信号"""
        self._signal_filters.append(filter_fn)

    def add_preprocessor(self, processor: Callable):
        """添加预处理器 - 在主逻辑之前执行"""
        self._preprocessors.append(processor)

    def add_postprocessor(self, processor: Callable):
        """添加后处理器 - 在主逻辑之后执行"""
        self._postprocessors.append(processor)

    async def on_receive(self, signal: NeuroSignal) -> ProcessingResult:
        """接收信号的入口点（由总线调用）"""
        self._metrics["signals_received"] += 1
        start_time = time.time()

        try:
            if not self._should_accept_signal(signal):
                return ProcessingResult(
                    success=True,
                    result_data=None,
                    metadata={"filtered": True}
                )

            context = ProcessingContext(
                mode=self.default_mode,
                priority=signal.priority,
            )

            for preproc in self._preprocessors:
                if asyncio.iscoroutinefunction(preproc):
                    await preproc(signal, context)
                else:
                    preproc(signal, context)

            result = await self.process_with_retry(signal, context)

            for postproc in self._postprocessors:
                if asyncio.iscoroutinefunction(postproc):
                    await postproc(signal, result, context)
                else:
                    postproc(signal, result, context)

            process_time = (time.time() - start_time) * 1000
            result.processing_time_ms = process_time
            result.metadata["domain"] = self.domain_name

            if result.success:
                self._metrics["signals_processed"] += 1
            else:
                self._metrics["signals_errored"] += 1

            alpha = 0.3
            self._metrics["avg_process_time_ms"] = (
                alpha * process_time +
                (1 - alpha) * self._metrics["avg_process_time_ms"]
            )

            await signal.complete(result)
            return result

        except Exception as e:
            self._metrics["signals_errored"] += 1
            error_ctx = ErrorContext(
                severity=ErrorSeverity.ERROR,
                source_domain=self.domain_name,
                error_type=type(e).__name__,
                message=str(e),
                original_signal=signal,
            )
            result = ProcessingResult(
                success=False,
                error=error_ctx,
                processing_time_ms=(time.time() - start_time) * 1000,
            )
            await signal.fail(e)
            return result

    def _should_accept_signal(self, signal: NeuroSignal) -> bool:
        """检查是否应该接受该信号"""
        if "*" not in self.supported_signals:
            if signal.signal_type not in self.supported_signals:
                return False

        for filter_fn in self._signal_filters:
            try:
                if not filter_fn(signal):
                    return False
            except Exception as e:
                logger.warning("Filter error in %s: %s", self.domain_name, e)
                return False

        return True

    async def process_with_retry(
        self,
        signal: NeuroSignal,
        context: ProcessingContext
    ) -> ProcessingResult:
        """带重试的处理逻辑"""
        last_error = None
        max_retries = self.retry_config.get("max_retries", 3)
        base_delay = self.retry_config.get("base_delay", 0.1)
        max_delay = self.retry_config.get("max_delay", 5.0)
        exp_base = self.retry_config.get("exponential_base", 2.0)
        use_jitter = self.retry_config.get("jitter", True)

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    delay = min(base_delay * (exp_base ** (attempt - 1)), max_delay)
                    if use_jitter:
                        import random
                        delay *= (0.5 + random.random())
                    await asyncio.sleep(delay)
                    logger.debug(
                        "Retry #%d for signal %s in domain '%s'",
                        attempt, signal.signal_id[:8], self.domain_name
                    )

                result = await self.async_process_signal(signal, context)
                
                if result.success or attempt == max_retries:
                    result.metadata.setdefault("retry_count", attempt)
                    return result
                    
                last_error = result.error

            except Exception as e:
                last_error = ErrorContext(
                    severity=ErrorSeverity.ERROR,
                    source_domain=self.domain_name,
                    error_type=type(e).__name__,
                    message=str(e),
                )
                if attempt == max_retries:
                    break

        return ProcessingResult(
            success=False,
            error=last_error,
            metadata={"retry_count": max_retries, "exhausted": True}
        )

    @abstractmethod
    async def async_process_signal(
        self,
        signal: NeuroSignal,
        context: ProcessingContext
    ) -> ProcessingResult:
        """核心抽象方法 - 子类必须实现异步信号处理逻辑"""
        pass

    async def send_signal(
        self,
        signal: NeuroSignal,
        broadcast: bool = True
    ) -> List[ProcessingResult]:
        """通过总线发送信号"""
        if self._bus is None:
            raise RuntimeError(f"Domain '{self.domain_name}' has no bus attached")
        
        signal.source_domain = self.domain_name
        
        if broadcast:
            return await self._bus.broadcast(signal)
        else:
            await self._bus.publish(signal)
            return []

    async def on_start(self) -> None:
        """生命周期钩子 - 领域启动时调用"""
        self._state = "running"
        logger.info("Domain started: %s", self.domain_name)

    async def on_stop(self) -> None:
        """生命周期钩子 - 领域停止时调用"""
        self._state = "stopped"
        logger.info("Domain stopped: %s", self.domain_name)

    async def on_error(self, error: ErrorContext) -> None:
        """生命周期钩子 - 发生错误时调用"""
        logger.error("Error in domain %s: %s", self.domain_name, error.message)

    async def health_check(self) -> Dict[str, Any]:
        """健康检查接口"""
        return {
            "domain": self.domain_name,
            "state": self._state,
            "role": self.role.value,
            "metrics": dict(self._metrics),
            "healthy": self._state == "running",
        }

    def get_metrics(self) -> Dict[str, Any]:
        """获取领域运行指标"""
        return dict(self._metrics)

    def __repr__(self) -> str:
        return (
            f"SoftwareDomain(name={self.domain_name}, "
            f"role={self.role.value}, "
            f"state={self._state})"
        )
