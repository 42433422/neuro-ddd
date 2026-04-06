from .core.types import (
    ProcessingMode, SignalPriority, DomainRole,
    ConcurrencyStrategy, ErrorSeverity, FeedbackType,
    DualModeStrategy,
    ProcessingContext, ErrorContext, ProcessingResult
)
from .core.signal import NeuroSignal
from .core.async_bus import AsyncNeuroBus
from .core.domain import SoftwareDomain
from .processing.conscious_processor import ConsciousProcessor
from .processing.subconscious_processor import SubconsciousProcessor
from .processing.dual_mode_engine import DualModeEngine
from .concurrency.concurrent_scheduler import ConcurrentScheduler
from .feedback.error_feedback import ErrorFeedbackSystem
from .feedback.reflex_arc import ReflexArc

__version__ = "1.0.0"
__author__ = "Neuro-DDD Team"

__all__ = [
    'ProcessingMode', 'SignalPriority', 'DomainRole',
    'ConcurrencyStrategy', 'ErrorSeverity', 'FeedbackType',
    'ProcessingContext', 'ErrorContext',
    'NeuroSignal', 'AsyncNeuroBus', 'SoftwareDomain',
    'ConsciousProcessor', 'SubconsciousProcessor', 'DualModeEngine',
    'ConcurrentScheduler', 'ErrorFeedbackSystem', 'ReflexArc',
]
