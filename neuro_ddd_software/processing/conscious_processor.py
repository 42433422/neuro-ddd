"""显意识处理器 - 模拟人脑精确但较慢的认知模式

特征：
- 逐步验证每个处理步骤
- 完整记录推理过程
- 支持复杂决策逻辑
- 资源消耗较大
- 输出可解释的结果
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from ..core.signal import NeuroSignal
from ..core.types import (
    ProcessingMode, ProcessingContext,
    ProcessingResult, ErrorContext, ErrorSeverity
)

logger = logging.getLogger(__name__)


class ConsciousProcessor:
    """显意识处理器
    
    设计理念：
    - 对应人脑的"慢思考"系统（System 2）
    - 适合复杂决策、需要高精度的场景
    - 处理时间较长但结果可靠
    - 提供完整的推理链路用于调试和审计
    """

    def __init__(
        self,
        name: str = "conscious",
        validation_rules: List[Callable] = None,
        max_reasoning_steps: int = 100,
        timeout_per_step: float = 5.0
    ):
        self.name = name
        self.validation_rules = validation_rules or []
        self.max_reasoning_steps = max_reasoning_steps
        self.timeout_per_step = timeout_per_step
        
        self._reasoning_chain: List[Dict] = []
        self._cache: Dict[str, Any] = {}
        self._metrics = {
            "total_processed": 0,
            "avg_time_ms": 0.0,
            "cache_hits": 0,
            "validation_failures": 0,
        }

    async def process(
        self,
        signal: NeuroSignal,
        context: ProcessingContext,
        handler: Callable
    ) -> ProcessingResult:
        """执行显意识处理流程"""
        start_time = time.time()
        self._reasoning_chain = []
        
        try:
            await self._record_step("start", "开始显意识处理", {"signal_type": signal.signal_type})

            cached = self._check_cache(signal)
            if cached is not None:
                self._metrics["cache_hits"] += 1
                await self._record_step("cache_hit", "命中缓存", {})
                return ProcessingResult(
                    success=True,
                    result_data=cached,
                    processing_mode_used=ProcessingMode.CONSCIOUS,
                    metadata={"cached": True, "reasoning_steps": len(self._reasoning_chain)},
                )

            intermediate_result = await self._pre_validate(signal)
            if intermediate_result is not None:
                return intermediate_result

            result_data = await self._execute_with_validation(signal, context, handler)
            
            validated = await self._post_validate(result_data)
            if not validated:
                self._metrics["validation_failures"] += 1
                return ProcessingResult(
                    success=False,
                    error=ErrorContext(
                        severity=ErrorSeverity.ERROR,
                        source_domain=self.name,
                        error_type="ValidationError",
                        message="后验证失败",
                    ),
                    processing_mode_used=ProcessingMode.CONSCIOUS,
                )

            cache_key = self._generate_cache_key(signal)
            self._cache[cache_key] = result_data
            
            process_time = (time.time() - start_time) * 1000
            self._update_metrics(process_time)

            explanation = await self.generate_explanation(result_data)
            
            return ProcessingResult(
                success=True,
                result_data=result_data,
                processing_mode_used=ProcessingMode.CONSCIOUS,
                processing_time_ms=process_time,
                metadata={
                    "reasoning_chain": list(self._reasoning_chain),
                    "explanation": explanation,
                    "steps_count": len(self._reasoning_chain),
                    "processor": self.name,
                }
            )

        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.exception("Conscious processing error: %s", e)
            return ProcessingResult(
                success=False,
                error=ErrorContext(
                    severity=ErrorSeverity.ERROR,
                    source_domain=self.name,
                    error_type=type(e).__name__,
                    message=str(e),
                    original_signal=signal,
                ),
                processing_mode_used=ProcessingMode.CONSCIOUS,
                processing_time_ms=process_time,
            )

    async def _pre_validate(self, signal: NeuroSignal) -> Optional[ProcessingResult]:
        """预处理验证阶段"""
        await self._record_step("pre_validate", "预处理验证", {})
        
        for rule in self.validation_rules:
            try:
                if asyncio.iscoroutinefunction(rule):
                    valid = await rule(signal)
                else:
                    valid = rule(signal)
                
                if valid is False:
                    self._metrics["validation_failures"] += 1
                    await self._record_step(
                        "pre_validate_fail",
                        f"规则 {rule.__name__ if hasattr(rule, '__name__') else 'unknown'} 验证失败",
                        {}
                    )
                    return ProcessingResult(
                        success=False,
                        error=ErrorContext(
                            severity=ErrorSeverity.WARNING,
                            source_domain=self.name,
                            error_type="PreValidationError",
                            message=f"预处理验证失败: {rule}",
                        ),
                        processing_mode_used=ProcessingMode.CONSCIOUS,
                    )
            except Exception as e:
                logger.warning("Validation rule error: %s", e)
        
        return None

    async def _execute_with_validation(
        self,
        signal: NeuroSignal,
        context: ProcessingContext,
        handler: Callable
    ) -> Any:
        """带步骤验证的核心执行"""
        step_count = 0
        
        async def wrapped_handler(sig, ctx):
            nonlocal step_count
            step_count += 1
            if step_count > self.max_reasoning_steps:
                raise RuntimeError(f"超过最大推理步数限制: {self.max_reasoning_steps}")
            
            await self._record_step(
                f"execute_step_{step_count}",
                f"执行处理步骤 #{step_count}",
                {}
            )
            
            result = handler(sig, ctx)
            if asyncio.iscoroutinefunction(handler):
                result = await result
            
            await self._record_step(
                f"step_{step_count}_complete",
                f"步骤 #{step_count} 完成",
                {"result_type": type(result).__name__}
            )
            
            return result

        result = await wrapped_handler(signal, context)
        return result

    async def _post_validate(self, result_data: Any) -> bool:
        """后处理验证"""
        await self._record_step("post_validate", "后处理验证", {})
        
        if result_data is None:
            await self._record_step("post_validate_fail", "结果为空", {})
            return False
        
        return True

    def _check_cache(self, signal: NeuroSignal) -> Optional[Any]:
        """检查缓存"""
        key = self._generate_cache_key(signal)
        return self._cache.get(key)

    def _generate_cache_key(self, signal: NeuroSignal) -> str:
        """生成缓存键"""
        import hashlib
        content = f"{signal.signal_type}:{str(sorted(signal.payload.items()))}"
        return hashlib.md5(content.encode()).hexdigest()

    async def generate_explanation(self, result_data: Any) -> str:
        """生成处理解释（用于可解释性）"""
        steps_info = [f"[{r['step']}] {r['action']}" for r in self._reasoning_chain]
        return (
            f"显意识处理完成，共{len(self._reasoning_chain)}步:\n"
            + "\n".join(steps_info[:10]) +
            (f"\n... 等共{len(steps_info)}步" if len(steps_info) > 10 else "")
        )

    async def _record_step(self, step: str, action: str, details: Dict):
        """记录推理步骤"""
        import time as t
        self._reasoning_chain.append({
            "step": step,
            "action": action,
            "details": details,
            "timestamp": t.time(),
        })

    def _update_metrics(self, process_time: float):
        """更新指标"""
        self._metrics["total_processed"] += 1
        alpha = 0.3
        self._metrics["avg_time_ms"] = (
            alpha * process_time +
            (1 - alpha) * self._metrics["avg_time_ms"]
        )

    def get_metrics(self) -> Dict:
        return dict(self._metrics)

    def get_last_reasoning_chain(self) -> List[Dict]:
        return list(self._reasoning_chain)

    def clear_cache(self):
        self._cache.clear()

    def __repr__(self) -> str:
        m = self.get_metrics()
        return (
            f"ConsciousProcessor(name={self.name}, "
            f"processed={m['total_processed']}, "
            f"avg_time={m['avg_time_ms']:.1f}ms)"
        )
