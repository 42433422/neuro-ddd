"""并发调度器 - Neuro-DDD软件层的并行处理中枢

支持多种并发模式：
- Worker Pool: 固定数量工作进程
- Fork-Join: 分治并行
- Pipeline: 流水线并发
- Actor模型: 领域即Actor
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple

from ..core.signal import NeuroSignal
from ..core.types import ConcurrencyStrategy, ProcessingResult

logger = logging.getLogger(__name__)


class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    task_id: str
    coroutine: Coroutine
    state: TaskState = TaskState.PENDING
    result: Any = None
    error: Optional[Exception] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)


class ConcurrentScheduler:
    """并发调度器
    
    职责：
    1. 任务排队和优先级管理
    2. 并发度控制
    3. 依赖关系解析
    4. 资源分配
    5. 超时和取消
    """

    def __init__(
        self,
        max_concurrent: int = 100,
        default_strategy: ConcurrencyStrategy = ConcurrencyStrategy.PARALLEL,
        queue_timeout: float = 30.0
    ):
        self.max_concurrent = max_concurrent
        self.default_strategy = default_strategy
        self.queue_timeout = queue_timeout

        self._tasks: Dict[str, ScheduledTask] = {}
        self._ready_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._running_tasks: Set[str] = set()
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(max_concurrent)
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

        self._metrics = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "avg_wait_time_ms": 0.0,
            "avg_exec_time_ms": 0.0,
            "peak_concurrency": 0,
        }

    @property
    def active_task_count(self) -> int:
        return len(self._running_tasks)

    @property
    def pending_task_count(self) -> int:
        return len(self._tasks) - len(self._running_tasks)

    async def submit(
        self,
        coro: Coroutine,
        task_id: str = None,
        priority: int = 5,
        dependencies: List[str] = None
    ) -> str:
        """提交任务到调度器"""
        import uuid
        tid = task_id or uuid.uuid4().hex[:12]
        
        task = ScheduledTask(
            task_id=tid,
            coroutine=coro,
            dependencies=set(dependencies or []),
        )
        self._tasks[tid] = task
        self._metrics["tasks_submitted"] += 1

        if dependencies:
            for dep_id in dependencies:
                if dep_id in self._tasks:
                    self._tasks[dep_id].dependents.add(tid)
        else:
            await self._ready_queue.put((priority, time.time(), tid))

        logger.debug("Task submitted: %s (deps=%s)", tid, dependencies)
        return tid

    async def run_parallel(
        self,
        tasks: List[Tuple[Coroutine, Dict]]
    ) -> List[ProcessingResult]:
        """并行运行多个任务
        
        Args:
            tasks: [(coroutine, {optional params}), ...]
            
        Returns:
            处理结果列表
        """
        async def wrapped(coro, **kwargs):
            try:
                result = coro
                if asyncio.iscoroutine(coro):
                    result = await coro
                return ProcessingResult(success=True, result_data=result)
            except Exception as e:
                return ProcessingResult(success=False, error=str(e))

        jobs = [wrapped(coro, **params) for coro, params in tasks]
        results = await asyncio.gather(*jobs, return_exceptions=True)

        return [
            r if isinstance(r, ProcessingResult)
            else ProcessingResult(success=False, error=str(r))
            for r in results
        ]

    async def run_pipeline(
        self,
        stages: List[Callable],
        initial_data: Any
    ) -> ProcessingResult:
        """流水线模式执行
        
        数据依次经过每个阶段，每个阶段可以并行处理
        """
        data = initial_data
        stage_results = []

        for i, stage_fn in enumerate(stages):
            start = time.time()
            try:
                if asyncio.iscoroutinefunction(stage_fn):
                    result = await stage_fn(data)
                else:
                    result = stage_fn(data)
                
                stage_time = (time.time() - start) * 1000
                stage_results.append({
                    "stage": i,
                    "success": True,
                    "time_ms": stage_time,
                })
                data = result

            except Exception as e:
                stage_time = (time.time() - start) * 1000
                stage_results.append({
                    "stage": i,
                    "success": False,
                    "error": str(e),
                    "time_ms": stage_time,
                })
                return ProcessingResult(
                    success=False,
                    error=str(e),
                    metadata={
                        "pipeline_stages": len(stages),
                        "completed_stages": i,
                        "stage_details": stage_results,
                    }
                )

        return ProcessingResult(
            success=True,
            result_data=data,
            metadata={
                "pipeline_stages": len(stages),
                "stage_details": stage_results,
            }
        )

    async def run_fan_out(
        self,
        task: Coroutine,
        fan_out_fn: Callable[[Any], List[Coroutine]],
        fan_in_fn: Callable[[List[Any]], Any]
    ) -> ProcessingResult:
        """Fan-Out/Fan-In模式
        
        1. 执行初始任务
        2. 将结果分发到多个子任务（Fan-Out）
        3. 收集子任务结果并合并（Fan-In）
        """
        start = time.time()
        
        main_result = task
        if asyncio.iscoroutine(task):
            main_result = await task

        sub_tasks = fan_out_fn(main_result)
        
        if sub_tasks:
            sub_results = await asyncio.gather(*sub_tasks, return_exceptions=True)
            final_result = fan_in_fn([
                r for r in sub_results if not isinstance(r, Exception)
            ])
        else:
            final_result = main_result

        total_time = (time.time() - start) * 1000
        return ProcessingResult(
            success=True,
            result_data=final_result,
            processing_time_ms=total_time,
            metadata={
                "fan_out_count": len(sub_tasks) if sub_tasks else 0,
                "strategy": "fan_out_fan_in",
            }
        )

    async def execute_batch(
        self,
        signals: List[NeuroSignal],
        handler: Callable,
        batch_size: int = 10
    ) -> List[ProcessingResult]:
        """批量执行（分批控制并发度）"""
        results = []
        
        for i in range(0, len(signals), batch_size):
            batch = signals[i:i + batch_size]
            batch_results = await self.run_parallel([
                (handler(sig), {}) for sig in batch
            ])
            results.extend(batch_results)

        return results

    async def wait_for_task(self, task_id: str, timeout: float = None) -> ProcessingResult:
        """等待特定任务完成"""
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Task {task_id} not found")

        timeout = timeout or self.queue_timeout
        deadline = time.time() + timeout

        while task.state not in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED):
            if time.time() > deadline:
                await self.cancel_task(task_id)
                raise TimeoutError(f"Task {task_id} timed out after {timeout}s")
            await asyncio.sleep(0.01)

        if task.error:
            raise task.error

        return ProcessingResult(
            success=task.state == TaskState.COMPLETED,
            result_data=task.result,
        )

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self._tasks.get(task_id)
        if not task or task.state == TaskState.COMPLETED:
            return False

        task.state = TaskState.CANCELLED
        self._running_tasks.discard(task_id)
        self._metrics["tasks_cancelled"] += 1
        return True

    async def cancel_all(self) -> int:
        """取消所有待处理任务"""
        count = 0
        for tid, task in list(self._tasks.items()):
            if task.state == TaskState.PENDING:
                task.state = TaskState.CANCELLED
                count += 1
        self._metrics["tasks_cancelled"] += count
        return count

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        task = self._tasks.get(task_id)
        if not task:
            return None
        return {
            "task_id": task.task_id,
            "state": task.state.value,
            "has_result": task.result is not None,
            "has_error": task.error is not None,
            "dependencies": list(task.dependencies),
            "dependents": list(task.dependents),
        }

    def get_metrics(self) -> Dict:
        """获取调度器指标"""
        m = dict(self._metrics)
        m["active_tasks"] = self.active_task_count
        m["pending_tasks"] = self.pending_task_count
        m["max_concurrent"] = self.max_concurrent
        m["utilization"] = (
            self.active_task_count / self.max_concurrent * 100
            if self.max_concurrent > 0 else 0
        )
        return m

    async def shutdown(self, wait_for_running: bool = True):
        """关闭调度器"""
        logger.info("Shutting down scheduler...")
        if wait_for_running:
            while self._running_tasks:
                await asyncio.sleep(0.05)
        await self.cancel_all()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()

    def __repr__(self) -> str:
        m = self.get_metrics()
        return (
            f"ConcurrentScheduler(active={m['active_tasks']}, "
            f"pending={m['pending_tasks']}, "
            f"utilization={m['utilization']:.1f}%)"
        )
