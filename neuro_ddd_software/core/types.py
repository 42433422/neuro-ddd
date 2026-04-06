"""Neuro-DDD 软件层核心类型定义

包含显意识/潜意识处理模式、信号优先级、并发策略、错误反馈等核心枚举和数据类。
"""

from enum import Enum, IntEnum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


class ProcessingMode(Enum):
    """神经处理模式 - 模拟人脑的两种认知模式"""
    CONSCIOUS = "conscious"
    SUBCONSCIOUS = "subconscious"
    DUAL = "dual"


class SignalPriority(IntEnum):
    """信号优先级 - 数值越小优先级越高"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class DomainRole(Enum):
    """领域角色分类"""
    CORE = "core"
    SUPPORT = "support"
    GENERIC = "generic"
    CROSS_CUTTING = "cross_cutting"


class ConcurrencyStrategy(Enum):
    """并发策略"""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    PIPELINE = "pipeline"
    FAN_OUT = "fan_out"
    FAN_IN = "fan_in"


class ErrorSeverity(Enum):
    """错误严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class FeedbackType(Enum):
    """反馈类型"""
    IMMEDIATE = "immediate"
    DEFERRED = "deferred"
    ACCUMULATED = "accumulated"
    BATCH = "batch"


class DualModeStrategy(Enum):
    """双模式协调策略"""
    FAST_FIRST = "fast_first"
    ACCURATE_FIRST = "accurate_first"
    PARALLEL = "parallel_dual"
    ADAPTIVE = "adaptive"


@dataclass
class ProcessingContext:
    """处理上下文 - 携带处理的元信息"""
    mode: ProcessingMode = ProcessingMode.DUAL
    priority: SignalPriority = SignalPriority.NORMAL
    timeout: float = 30.0
    retry_count: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ErrorContext:
    """错误上下文 - 结构化错误信息"""
    severity: ErrorSeverity
    source_domain: str
    error_type: str
    message: str
    original_signal: Any = None
    stack_trace: Optional[str] = None
    recovery_hints: Optional[List[str]] = None
    timestamp: float = 0.0

    def __post_init__(self):
        import time
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if self.recovery_hints is None:
            self.recovery_hints = []


@dataclass
class ProcessingResult:
    """处理结果 - 统一的结果封装"""
    success: bool
    result_data: Any = None
    error: Optional[ErrorContext] = None
    processing_mode_used: ProcessingMode = ProcessingMode.DUAL
    processing_time_ms: float = 0.0
    signals_generated: List['NeuroSignal'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.signals_generated is None:
            self.signals_generated = []
        if self.metadata is None:
            self.metadata = {}
