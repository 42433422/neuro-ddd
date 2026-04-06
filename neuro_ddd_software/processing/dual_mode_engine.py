"""双模式协调引擎 - 显意识与潜意识的协同处理核心

这是 Neuro-DDD 软件层最核心的创新组件！
实现类似人脑的"快慢思考"协同机制。
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from ..core.signal import NeuroSignal
from ..core.types import (
    ProcessingMode, ProcessingContext,
    ProcessingResult, DualModeStrategy,
    ErrorContext, ErrorSeverity
)
from .conscious_processor import ConsciousProcessor
from .subconscious_processor import SubconsciousProcessor

logger = logging.getLogger(__name__)


class DualModeEngine:
    """双模式协调引擎
    
    核心工作流程：
    1. 信号到达 → 潜意识快速预处理（分类、复杂度评估）
    2. 简单/已知模式 → 潜意识直接处理（<10ms目标）
    3. 复杂/未知模式 → 升级到显意识精细处理
    4. 结果合并/仲裁 → 输出最终结果
    
    支持策略：
    - FAST_FIRST: 先尝试潜意识，失败则升级显意识
    - ACCURATE_FIRST: 先用显意识验证，再用潜意识加速
    - PARALLEL: 两者并行，取最优或合并
    - ADAPTIVE: 根据历史数据自动选择策略
    """

    def __init__(
        self,
        strategy: DualModeStrategy = DualModeStrategy.ADAPTIVE,
        conscious_timeout: float = 30.0,
        subconscious_timeout: float = 0.01,
        complexity_threshold: float = 0.5,
        auto_learn: bool = True
    ):
        self.strategy = strategy
        self.conscious_timeout = conscious_timeout
        self.subconscious_timeout = subconscious_timeout
        self.complexity_threshold = complexity_threshold
        self.auto_learn = auto_learn

        self.conscious = ConsciousProcessor()
        self.subconscious = SubconsciousProcessor()

        self._decision_history: List[Dict] = []
        self._strategy_stats: Dict[DualModeStrategy, Dict] = {
            s: {"used": 0, "success": 0, "avg_time_ms": 0.0}
            for s in DualModeStrategy
        }
        self._pattern_complexity_cache: Dict[str, float] = {}

    async def process(
        self,
        signal: NeuroSignal,
        context: ProcessingContext,
        handler: Callable
    ) -> ProcessingResult:
        """双模式处理入口"""
        start_time = time.time()

        try:
            if self.strategy == DualModeStrategy.FAST_FIRST:
                result = await self._fast_first_strategy(signal, context, handler)
            elif self.strategy == DualModeStrategy.ACCURATE_FIRST:
                result = await self._accurate_first_strategy(signal, context, handler)
            elif self.strategy == DualModeStrategy.PARALLEL:
                result = await self._parallel_strategy(signal, context, handler)
            elif self.strategy == DualModeStrategy.ADAPTIVE:
                result = await self._adaptive_strategy(signal, context, handler)
            else:
                result = await self._adaptive_strategy(signal, context, handler)

            process_time = (time.time() - start_time) * 1000
            result.processing_time_ms = process_time
            result.metadata["dual_mode_engine"] = {
                "strategy_used": self.strategy.value,
                "total_time_ms": round(process_time, 2),
            }

            self._record_decision(signal, result, process_time)

            return result

        except Exception as e:
            logger.exception("Dual mode processing error")
            return ProcessingResult(
                success=False,
                error=ErrorContext(
                    severity=ErrorSeverity.ERROR,
                    source_domain="DualModeEngine",
                    error_type=type(e).__name__,
                    message=str(e),
                    original_signal=signal,
                ),
                processing_mode_used=ProcessingMode.DUAL,
            )

    async def _fast_first_strategy(
        self,
        signal: NeuroSignal,
        context: ProcessingContext,
        handler: Callable
    ) -> ProcessingResult:
        """FAST_FIRST策略：先尝试潜意识"""
        
        sub_result = await asyncio.wait_for(
            self.subconscious.process(signal, context, handler),
            timeout=self.subconscious_timeout
        )

        if sub_result.success and sub_result.result_data is not None:
            sub_confidence = sub_result.metadata.get("confidence", 1.0)
            
            if sub_confidence >= self.complexity_threshold:
                sub_result.metadata["strategy_path"] = "subconscious_only"
                return sub_result

        con_result = await asyncio.wait_for(
            self.conscious.process(signal, context, handler),
            timeout=self.conscious_timeout
        )

        con_result.metadata["strategy_path"] = "subconscious_fallback_to_conscious"
        con_result.metadata["subconscious_attempted"] = True
        
        if sub_result.success and con_result.success:
            return self._merge_results(sub_result, con_result, prefer="conscious")
        
        return con_result if con_result.success else sub_result

    async def _accurate_first_strategy(
        self,
        signal: NeuroSignal,
        context: ProcessingContext,
        handler: Callable
    ) -> ProcessingResult:
        """ACCURATE_FIRST策略：先用显意识验证"""

        complexity = self._estimate_complexity(signal)

        if complexity < self.complexity_threshold:
            sub_result = await self.subconscious.process(signal, context, handler)
            sub_result.metadata["strategy_path"] = "low_complexity_subconscious"
            return sub_result

        con_result = await self.conscious.process(signal, context, handler)

        if not con_result.success:
            sub_result = await self.subconscious.process(signal, context, handler)
            sub_result.metadata["strategy_path"] = "conscious_failed_fallback"
            return sub_result

        can_accelerate = self._can_accelerate_with_subconscious(con_result)
        if can_accelerate:
            sub_result = await self.subconscious.process(signal, context, handler)
            merged = self._merge_results(con_result, sub_result, prefer="conscious")
            merged.metadata["strategy_path"] = "conscious_validated_with_subconscious"
            return merged

        con_result.metadata["strategy_path"] = "conscious_only_high_complexity"
        return con_result

    async def _parallel_strategy(
        self,
        signal: NeuroSignal,
        context: ProcessingContext,
        handler: Callable
    ) -> ProcessingResult:
        """PARALLEL策略：两者并行执行"""

        tasks = [
            asyncio.create_task(self.subconscious.process(signal, context, handler)),
            asyncio.create_task(self.conscious.process(signal, context, handler)),
        ]

        done, pending = await asyncio.wait(
            tasks,
            timeout=self.subconscious_timeout,
            return_when=asyncio.FIRST_COMPLETED
        )

        fast_results = [t.result() for t in done if t.done()]
        
        if fast_results:
            fast_result = fast_results[0]
            if fast_result.success:
                for t in pending:
                    t.cancel()
                
                source = fast_result.metadata.get("source", "unknown")
                fast_result.metadata["strategy_path"] = f"parallel_{source}_first"
                return fast_results[0]

        remaining = await asyncio.gather(*pending, return_exceptions=True)
        all_results = fast_results + [r for r in remaining if isinstance(r, ProcessingResult)]

        successful = [r for r in all_results if r.success]
        if successful:
            best = max(successful, key=lambda r: r.metadata.get("confidence", 0.5))
            best.metadata["strategy_path"] = "parallel_best_of_both"
            return best

        errors = [r for r in all_results if not r.success]
        if errors:
            errors[0].metadata["strategy_path"] = "parallel_all_failed"
            return errors[0]

        return ProcessingResult(success=False, metadata={"strategy_path": "parallel_no_result"})

    async def _adaptive_strategy(
        self,
        signal: NeuroSignal,
        context: ProcessingContext,
        handler: Callable
    ) -> ProcessingResult:
        """ADAPTIVE策略：根据历史数据自动选择"""

        pattern_key = self._get_pattern_key(signal)
        historical_stats = self._get_historical_stats(pattern_key)

        if historical_stats and historical_stats.get("best_strategy"):
            best_strat_name = historical_stats["best_strategy"]
            best_strat = DualModeStrategy(best_strat_name)
            
            dispatch_map = {
                DualModeStrategy.FAST_FIRST: self._fast_first_strategy,
                DualModeStrategy.ACCURATE_FIRST: self._accurate_first_strategy,
                DualModeStrategy.PARALLEL: self._parallel_strategy,
            }

            dispatcher = dispatch_map.get(best_strat, self._adaptive_strategy)
            result = await dispatcher(signal, context, handler)
            result.metadata["adaptive_selected"] = best_strat_name
            result.metadata["strategy_path"] = f"adaptive_{best_strat_name}"
            return result

        complexity = self._estimate_complexity(signal)
        
        if complexity < 0.3:
            result = await self.subconscious.process(signal, context, handler)
            result.metadata["strategy_path"] = "adaptive_low_complexity"
        elif complexity > 0.7:
            result = await self.conscious.process(signal, context, handler)
            result.metadata["strategy_path"] = "adaptive_high_complexity"
        else:
            result = await self._fast_first_strategy(signal, context, handler)
            result.metadata["strategy_path"] = "adaptive_mixed"

        return result

    def _estimate_complexity(self, signal: NeuroSignal) -> float:
        """估计信号处理复杂度 (0.0-1.0)"""
        pattern_key = self._get_pattern_key(signal)
        if pattern_key in self._pattern_complexity_cache:
            return self._pattern_complexity_cache[pattern_key]

        complexity = 0.0

        payload_size = len(str(signal.payload))
        if payload_size > 10000:
            complexity += 0.3
        elif payload_size > 1000:
            complexity += 0.15

        target_count = len(signal.target_domains)
        if target_count > 5:
            complexity += 0.2
        elif target_count > 2:
            complexity += 0.1

        if signal.priority.name == "CRITICAL":
            complexity += 0.2

        nested_depth = self._estimate_payload_depth(signal.payload)
        complexity += min(nested_depth * 0.05, 0.2)

        complexity = min(complexity, 1.0)
        self._pattern_complexity_cache[pattern_key] = complexity
        return complexity

    def _estimate_payload_depth(self, payload: Dict, current_depth: int = 0) -> int:
        if current_depth > 10 or not isinstance(payload, dict):
            return current_depth
        max_depth = current_depth
        for v in payload.values():
            if isinstance(v, dict):
                depth = self._estimate_payload_depth(v, current_depth + 1)
                max_depth = max(max_depth, depth)
            elif isinstance(v, list):
                depth = current_depth + 1
                max_depth = max(max_depth, depth)
        return max_depth

    def _can_accelerate_with_subconscious(self, conscious_result: ProcessingResult) -> bool:
        """判断是否可以用潜意识加速显意识结果"""
        reasoning_steps = conscious_result.metadata.get("steps_count", 0)
        return reasoning_steps <= 5

    def _merge_results(
        self,
        result_a: ProcessingResult,
        result_b: ProcessingResult,
        prefer: str = "conscious"
    ) -> ProcessingResult:
        """合并两个处理结果"""
        preferred = result_a if prefer == "conscious" else result_b
        other = result_b if prefer == "conscious" else result_a

        merged_metadata = dict(preferred.metadata)
        merged_metadata["merged_from"] = [
            result_a.metadata.get("processor"),
            result_b.metadata.get("processor"),
        ]
        merged_metadata["merge_prefer"] = prefer

        return ProcessingResult(
            success=preferred.success or other.success,
            result_data=preferred.result_data or other.result_data,
            error=preferred.error or other.error,
            processing_mode_used=ProcessingMode.DUAL,
            processing_time_ms=max(
                preferred.processing_time_ms,
                other.processing_time_ms
            ),
            signals_generated=(
                preferred.signals_generated + other.signals_generated
            ),
            metadata=merged_metadata,
        )

    def _get_pattern_key(self, signal: NeuroSignal) -> str:
        import hashlib
        content = f"{signal.signal_type}:{sorted(signal.payload.keys()) if signal.payload else ''}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _get_historical_stats(self, pattern_key: str) -> Optional[Dict]:
        """获取历史决策统计"""
        matching = [d for d in self._decision_history if d.get("pattern") == pattern_key]
        if len(matching) < 3:
            return None

        stats = {}
        for d in matching[-20:]:
            strat = d.get("strategy")
            if strat:
                if strat not in stats:
                    stats[strat] = {"count": 0, "success": 0, "total_time": 0}
                stats[strat]["count"] += 1
                stats[strat]["total_time"] += d.get("time_ms", 0)
                if d.get("success"):
                    stats[strat]["success"] += 1

        best_strat = None
        best_score = -1
        for strat, s in stats.items():
            score = s["success"] / s["count"]
            avg_time = s["total_time"] / s["count"]
            score -= avg_time / 1000
            
            if score > best_score:
                best_score = score
                best_strat = strat

        if best_strat:
            return {"best_strategy": best_strat, "score": round(best_score, 3)}
        return None

    def _record_decision(
        self,
        signal: NeuroSignal,
        result: ProcessingResult,
        time_ms: float
    ):
        """记录决策用于自适应学习"""
        self._decision_history.append({
            "pattern": self._get_pattern_key(signal),
            "strategy": self.strategy.value,
            "success": result.success,
            "time_ms": time_ms,
            "timestamp": time.time(),
        })

        if len(self._decision_history) > 10000:
            self._decision_history = self._decision_history[-5000:]

        stats = self._strategy_stats[self.strategy]
        stats["used"] += 1
        if result.success:
            stats["success"] += 1
        old_avg = stats["avg_time_ms"]
        stats["avg_time_ms"] = (
            (old_avg * (stats["used"] - 1) + time_ms) / stats["used"]
        )

    def get_stats(self) -> Dict:
        """获取引擎运行统计"""
        return {
            "strategy": self.strategy.value,
            "decision_history_size": len(self._decision_history),
            "complexity_cache_size": len(self._pattern_complexity_cache),
            "strategy_stats": {
                k.value: dict(v) for k, v in self._strategy_stats.items()
            },
            "conscious_metrics": self.conscious.get_metrics(),
            "subconscious_metrics": self.subconscious.get_metrics(),
        }

    def set_strategy(self, strategy: DualModeStrategy):
        """动态切换策略"""
        old = self.strategy
        self.strategy = strategy
        logger.info("Strategy changed: %s -> %s", old.value, strategy.value)

    def __repr__(self) -> str:
        s = self.get_stats()
        return (
            f"DualModeEngine(strategy={self.strategy.value}, "
            f"decisions={s['decision_history_size']})"
        )
