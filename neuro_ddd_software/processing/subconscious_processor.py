"""潜意识处理器 - 模拟人脑快速直觉式认知模式

特征：
- 基于模式匹配的极速响应
- 并行处理多个简单信号
- 使用缓存和启发式规则
- 低资源消耗
- 可能牺牲部分精度换取速度
"""

import asyncio
import hashlib
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..core.signal import NeuroSignal
from ..core.types import (
    ProcessingMode, ProcessingContext,
    ProcessingResult, ErrorContext, ErrorSeverity
)

logger = logging.getLogger(__name__)


class SubconsciousProcessor:
    """潜意识处理器
    
    设计理念：
    - 对应人脑的"快思考"系统（System 1）
    - 适合简单、重复性、需要快速响应的场景
    - 使用模式匹配和启发式算法
    - 通过并行化实现高速处理
    """

    def __init__(
        self,
        name: str = "subconscious",
        pattern_cache_size: int = 10000,
        enable_parallel: bool = True,
        max_parallel_tasks: int = 50,
        confidence_threshold: float = 0.7
    ):
        self.name = name
        self.pattern_cache_size = pattern_cache_size
        self.enable_parallel = enable_parallel
        self.max_parallel_tasks = max_parallel_tasks
        self.confidence_threshold = confidence_threshold

        self._pattern_cache: Dict[str, Tuple[Any, float]] = {}
        self._heuristic_rules: List[Tuple[Callable, float]] = []
        self._semaphore: Optional[asyncio.Semaphore] = None
        
        self._metrics = {
            "total_processed": 0,
            "pattern_match_hits": 0,
            "heuristic_matches": 0,
            "full_processing": 0,
            "avg_time_ms": 0.0,
            "parallel_utilization": 0.0,
        }

        if self.enable_parallel:
            self._semaphore = asyncio.Semaphore(self.max_parallel_tasks)

    def register_heuristic(self, heuristic_fn: Callable, confidence: float = 0.8):
        """注册启发式规则
        
        Args:
            heuristic_fn: 启发式函数，输入signal，输出(result, confidence_score)
            confidence: 该规则的默认置信度
        """
        self._heuristic_rules.append((heuristic_fn, confidence))

    async def process(
        self,
        signal: NeuroSignal,
        context: ProcessingContext,
        handler: Callable
    ) -> ProcessingResult:
        """执行潜意识处理流程"""
        start_time = time.time()

        try:
            cached_result, confidence = self._pattern_match(signal)
            if cached_result is not None and confidence >= self.confidence_threshold:
                self._metrics["pattern_match_hits"] += 1
                process_time = (time.time() - start_time) * 1000
                self._update_metrics(process_time)
                return ProcessingResult(
                    success=True,
                    result_data=cached_result,
                    processing_mode_used=ProcessingMode.SUBCONSCIOUS,
                    processing_time_ms=process_time,
                    metadata={
                        "source": "pattern_cache",
                        "confidence": confidence,
                        "processor": self.name,
                    }
                )

            heuristic_result, confidence = await self._apply_heuristics(signal)
            if heuristic_result is not None and confidence >= self.confidence_threshold:
                self._metrics["heuristic_matches"] += 1
                process_time = (time.time() - start_time) * 1000
                self._update_metrics(process_time)
                return ProcessingResult(
                    success=True,
                    result_data=heuristic_result,
                    processing_mode_used=ProcessingMode.SUBCONSCIOUS,
                    processing_time_ms=process_time,
                    metadata={
                        "source": "heuristic",
                        "confidence": confidence,
                        "processor": self.name,
                    }
                )

            self._metrics["full_processing"] += 1
            
            if self.enable_parallel and self._semaphore:
                async with self._semaphore:
                    result_data = await self._fast_execute(signal, context, handler)
            else:
                result_data = await self._fast_execute(signal, context, handler)

            cache_key = self._compute_pattern_key(signal)
            self._store_pattern(cache_key, result_data, confidence=1.0)

            process_time = (time.time() - start_time) * 1000
            self._update_metrics(process_time)

            return ProcessingResult(
                success=True,
                result_data=result_data,
                processing_mode_used=ProcessingMode.SUBCONSCIOUS,
                processing_time_ms=process_time,
                metadata={
                    "source": "full_processing",
                    "processor": self.name,
                }
            )

        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.warning("Subconscious processing error (falling back): %s", e)
            return ProcessingResult(
                success=False,
                error=ErrorContext(
                    severity=ErrorSeverity.WARNING,
                    source_domain=self.name,
                    error_type=type(e).__name__,
                    message=str(e),
                    original_signal=signal,
                ),
                processing_mode_used=ProcessingMode.SUBCONSCIOUS,
                processing_time_ms=process_time,
            )

    def _pattern_match(self, signal: NeuroSignal) -> Tuple[Optional[Any], float]:
        """模式匹配 - 从缓存中查找相似信号的处理结果"""
        key = self._compute_pattern_key(signal)
        if key in self._pattern_cache:
            return self._pattern_cache[key]
        return None, 0.0

    async def _apply_heuristics(self, signal: NeuroSignal) -> Tuple[Optional[Any], float]:
        """应用启发式规则"""
        best_result = None
        best_confidence = 0.0

        for heuristic_fn, base_confidence in self._heuristic_rules:
            try:
                if asyncio.iscoroutinefunction(heuristic_fn):
                    result = await heuristic_fn(signal)
                else:
                    result = heuristic_fn(signal)

                if isinstance(result, tuple):
                    data, confidence = result
                else:
                    data, confidence = result, base_confidence

                if data is not None and confidence > best_confidence:
                    best_result = data
                    best_confidence = confidence

            except Exception as e:
                logger.debug("Heuristic error: %s", e)

        return best_result, best_confidence

    async def _fast_execute(
        self,
        signal: NeuroSignal,
        context: ProcessingContext,
        handler: Callable
    ) -> Any:
        """快速执行（无完整验证）"""
        result = handler(signal, context)
        if asyncio.iscoroutinefunction(handler):
            result = await result
        return result

    def _compute_pattern_key(self, signal: NeuroSignal) -> str:
        """计算模式键（用于缓存查找）"""
        payload_str = str(sorted(signal.payload.items())) if signal.payload else ""
        content = f"{signal.signal_type}:{payload_str}"
        return hashlib.md5(content.encode()).hexdigest()

    def _store_pattern(self, key: str, result: Any, confidence: float):
        """存储模式到缓存（LRU策略）"""
        if len(self._pattern_cache) >= self.pattern_cache_size:
            oldest_key = next(iter(self._pattern_cache))
            del self._pattern_cache[oldest_key]
        self._pattern_cache[key] = (result, confidence)

    def heuristic_evaluate(self, signal: NeuroSignal) -> float:
        """启发式评估 - 返回对信号的置信度分数"""
        _, confidence = self._pattern_match(signal)
        if confidence >= self.confidence_threshold:
            return confidence

        score = 0.0
        for _, base_conf in self._heuristic_rules:
            score = max(score, base_conf * 0.5)

        complexity = len(str(signal.payload))
        if complexity < 100:
            score += 0.2
        elif complexity < 500:
            score += 0.1

        return min(score, 1.0)

    def _update_metrics(self, process_time: float):
        """更新指标"""
        self._metrics["total_processed"] += 1
        alpha = 0.3
        old_avg = self._metrics["avg_time_ms"]
        self._metrics["avg_time_ms"] = alpha * process_time + (1 - alpha) * old_avg

        if self.enable_parallel and self._semaphore:
            used = self.max_parallel_tasks - self._semaphore._value
            self._metrics["parallel_utilization"] = (
                used / self.max_parallel_tasks * 100
            )

    def get_metrics(self) -> Dict:
        m = dict(self._metrics)
        m["cache_size"] = len(self._pattern_cache)
        m["heuristic_rules_count"] = len(self._heuristic_rules)
        return m

    def clear_cache(self):
        self._pattern_cache.clear()

    def __repr__(self) -> str:
        m = self.get_metrics()
        return (
            f"SubconsciousProcessor(name={self.name}, "
            f"processed={m['total_processed']}, "
            f"avg_time={m['avg_time_ms']:.2f}ms, "
            f"cache_hits={m['pattern_match_hits']})"
        )
