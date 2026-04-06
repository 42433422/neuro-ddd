"""仓储领域模板 - Neuro-DDD软件层的数据访问模式

用于封装数据存储和检索逻辑，支持缓存和批量操作。
"""

from ..core.domain import SoftwareDomain
from ..core.types import DomainRole, ProcessingMode, ProcessingContext, ProcessingResult
from ..core.signal import NeuroSignal


class RepositoryDomain(SoftwareDomain):
    """仓储领域模板
    
    适用场景：
    - 数据库CRUD操作
    - 缓存管理
    - 数据聚合查询
    - 适合潜意识快速处理的数据读取
    """

    def __init__(
        self,
        entity_name: str,
        **kwargs
    ):
        super().__init__(
            domain_name=f"repository:{entity_name}",
            role=DomainRole.SUPPORT,
            default_mode=ProcessingMode.SUBCONSCIOUS,
            **kwargs
        )
        self.entity_name = entity_name
        self._cache: dict = {}
        self._data_store: dict = {}
        self._query_handlers: dict = {}

    def register_query(self, query_type: str, handler):
        """注册查询处理器"""
        self._query_handlers[query_type] = handler

    async def async_process_signal(
        self,
        signal: NeuroSignal,
        context: ProcessingContext
    ) -> ProcessingResult:
        action = signal.payload.get("action")
        query_type = signal.payload.get("query_type")
        
        cache_key = self._make_cache_key(signal.payload)
        
        if action == "get" and cache_key in self._cache:
            return ProcessingResult(
                success=True,
                result_data=self._cache[cache_key],
                metadata={"cached": True},
            )

        if query_type and query_type in self._query_handlers:
            handler = self._query_handlers[query_type]
            try:
                result = handler(signal.payload)
                if hasattr(result, '__awaitable__'):
                    result = await result
                
                if action == "get":
                    self._cache[cache_key] = result
                
                return ProcessingResult(
                    success=True,
                    result_data=result,
                    metadata={"query_type": query_type},
                )
            except Exception as e:
                return ProcessingResult(success=False, error=str(e))

        return await self._default_crud_handler(signal)

    async def _default_crud_handler(self, signal: NeuroSignal) -> ProcessingResult:
        action = signal.payload.get("action")
        entity_id = signal.payload.get("id")
        data = signal.payload.get("data")

        if action == "get":
            result = self._data_store.get(entity_id)
            if entity_id and result is not None:
                self._cache[self._make_cache_key({"id": entity_id})] = result
            return ProcessingResult(
                success=result is not None,
                result_data=result,
            )

        elif action == "save":
            if entity_id and data is not None:
                self._data_store[entity_id] = data
                self._cache.clear()
            return ProcessingResult(success=True, result_data=data)

        elif action == "delete":
            if entity_id in self._data_store:
                del self._data_store[entity_id]
                self._cache.clear()
            return ProcessingResult(success=True)

        elif action == "list":
            items = list(self._data_store.values())
            return ProcessingResult(success=True, result_data=items)

        return ProcessingResult(success=False, error="Invalid CRUD action")

    def _make_cache_key(self, payload: dict) -> str:
        import hashlib
        content = str(sorted(payload.items()))
        return hashlib.md5(content.encode()).hexdigest()[:16]

    @property
    def count(self) -> int:
        return len(self._data_store)

    def clear_cache(self):
        self._cache.clear()

    def __repr__(self) -> str:
        return (
            f"RepositoryDomain(entity={self.entity_name}, "
            f"count={self.count}, cached={len(self._cache)})"
        )
