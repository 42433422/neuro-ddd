"""Neuro-DDD 增强版神经信号协议

支持优先级、关联追踪、回调、TTL等企业级特性。
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .types import (
    SignalPriority, ProcessingMode,
    ErrorSeverity, ProcessingResult
)


@dataclass
class NeuroSignal:
    """神经信号 - Neuro-DDD软件层核心通信单元
    
    设计理念：
    - 模拟生物神经元的电信号/化学信号传递
    - 支持信号链追踪（correlation_id + parent_signal_id）
    - 内置优先级和生存时间（TTL）控制
    - 支持异步回调（on_complete / on_error）
    """

    signal_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    signal_type: str = ""
    source_domain: str = ""
    target_domains: List[str] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)

    priority: SignalPriority = SignalPriority.NORMAL
    processing_mode: ProcessingMode = ProcessingMode.DUAL
    timestamp: float = field(default_factory=time.time)
    ttl: int = 10
    correlation_id: Optional[str] = None
    parent_signal_id: Optional[str] = None

    on_complete: Optional[Callable] = None
    on_error: Optional[Callable[[Exception], None]] = None

    hop_count: int = 0
    processing_history: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        if self.target_domains is None:
            self.target_domains = []
        if self.payload is None:
            self.payload = {}
        if self.processing_history is None:
            self.processing_history = []

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type,
            "source_domain": self.source_domain,
            "target_domains": self.target_domains,
            "priority": self.priority.name,
            "processing_mode": self.processing_mode.value,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "correlation_id": self.correlation_id,
            "parent_signal_id": self.parent_signal_id,
            "hop_count": self.hop_count,
            "payload": self.payload,
        }

    def child_signal(
        self,
        signal_type: str,
        payload: Dict[str, Any] = None,
        target_domains: List[str] = None
    ) -> 'NeuroSignal':
        """创建子信号，保持与父信号的关联关系"""
        child = NeuroSignal(
            signal_type=signal_type,
            source_domain=self.source_domain,
            target_domains=target_domains or [],
            payload=payload or {},
            priority=self.priority,
            correlation_id=self.correlation_id or self.signal_id,
            parent_signal_id=self.signal_id,
            ttl=self.ttl - 1,
        )
        child.hop_count = self.hop_count + 1
        return child

    def add_processing_record(
        self,
        domain: str,
        action: str,
        result: str,
        duration_ms: float = 0.0
    ):
        """添加处理记录，用于追踪和调试"""
        self.processing_history.append({
            "domain": domain,
            "action": action,
            "result": result,
            "timestamp": time.time(),
            "duration_ms": duration_ms,
        })

    def is_expired(self) -> bool:
        """检查信号是否已过期（TTL耗尽）"""
        return self.ttl <= 0

    def decrement_ttl(self) -> int:
        """递减TTL并返回新值"""
        self.ttl -= 1
        return self.ttl

    async def complete(self, result: ProcessingResult):
        """标记信号处理完成，触发回调"""
        self.add_processing_record(
            "system", "complete",
            "success" if result.success else "failed"
        )
        if callable(self.on_complete):
            if hasattr(self.on_complete, '__awaitable__'):
                await self.on_complete(result)
            else:
                self.on_complete(result)

    async def fail(self, error: Exception):
        """标记信号处理失败，触发错误回调"""
        self.add_processing_record("system", "fail", str(error))
        if callable(self.on_error):
            self.on_error(error)

    def clone(self) -> 'NeuroSignal':
        """创建信号的深拷贝（用于重试等场景）"""
        import copy
        cloned = copy.deepcopy(self)
        cloned.signal_id = uuid.uuid4().hex[:12]
        cloned.timestamp = time.time()
        return cloned

    @classmethod
    def create_request(
        cls,
        source: str,
        signal_type: str,
        payload: Dict[str, Any],
        targets: List[str] = None,
        priority: SignalPriority = SignalPriority.NORMAL,
        **kwargs
    ) -> 'NeuroSignal':
        """工厂方法：创建请求信号"""
        return cls(
            signal_type=signal_type,
            source_domain=source,
            target_domains=targets or [],
            payload=payload,
            priority=priority,
            **kwargs
        )

    @classmethod
    def create_response(
        cls,
        request_signal: 'NeuroSignal',
        result_data: Any,
        success: bool = True
    ) -> 'NeuroSignal':
        """工厂方法：创建响应信号（自动关联请求）"""
        response_type = f"{request_signal.signal_type}_response"
        return request_signal.child_signal(
            signal_type=response_type,
            payload={
                "success": success,
                "data": result_data,
                "request_id": request_signal.signal_id,
            }
        )

    @classmethod
    def create_error_response(
        cls,
        request_signal: 'NeuroSignal',
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.ERROR
    ) -> 'NeuroSignal':
        """工厂方法：创建错误响应信号"""
        return request_signal.child_signal(
            signal_type=f"{request_signal.signal_type}_error",
            payload={
                "success": False,
                "error": str(error),
                "error_type": type(error).__name__,
                "severity": severity.value,
                "request_id": request_signal.signal_id,
            }
        )

    def __repr__(self) -> str:
        targets = ",".join(self.target_domains[:3])
        if len(self.target_domains) > 3:
            targets += f"...(+{len(self.target_domains)-3})"
        return (
            f"NeuroSignal(id={self.signal_id[:8]}, "
            f"type={self.signal_type}, "
            f"src={self.source_domain}, "
            f"dst=[{targets}], "
            f"prio={self.priority.name})"
        )
