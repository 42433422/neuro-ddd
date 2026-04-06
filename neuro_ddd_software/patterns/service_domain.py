"""服务领域模板 - Neuro-DDD软件层的服务封装模式

用于将业务逻辑封装为独立的服务领域，
通过神经总线与其他领域通信。
"""

from ..core.domain import SoftwareDomain
from ..core.types import DomainRole, ProcessingMode, ProcessingContext, ProcessingResult
from ..core.signal import NeuroSignal


class ServiceDomain(SoftwareDomain):
    """服务领域模板
    
    适用场景：
    - 业务逻辑封装
    - 第三方API调用封装
    - 复杂计算逻辑
    - 需要显意识处理的精确业务
    """

    def __init__(
        self,
        service_name: str,
        version: str = "1.0.0",
        **kwargs
    ):
        super().__init__(
            domain_name=f"service:{service_name}",
            role=DomainRole.CORE,
            default_mode=ProcessingMode.CONSCIOUS,
            **kwargs
        )
        self.service_name = service_name
        self.version = version
        self._business_handlers: dict = {}

    def register_handler(self, action: str, handler):
        """注册业务处理器"""
        self._business_handlers[action] = handler

    async def async_process_signal(
        self,
        signal: NeuroSignal,
        context: ProcessingContext
    ) -> ProcessingResult:
        action = signal.payload.get("action")
        
        if action and action in self._business_handlers:
            handler = self._business_handlers[action]
            try:
                result = handler(signal.payload)
                if hasattr(result, '__awaitable__'):
                    result = await result
                
                return ProcessingResult(
                    success=True,
                    result_data=result,
                    signals_generated=[
                        signal.child_signal(
                            f"{action}_response",
                            {"result": result}
                        )
                    ],
                )
            except Exception as e:
                return ProcessingResult(
                    success=False,
                    error=str(e),
                )

        return ProcessingResult(
            success=False,
            error=f"Unknown action: {action}",
        )

    async def call_service(
        self,
        action: str,
        data: dict = None,
        target_domains: list = None,
        priority=None
    ) -> ProcessingResult:
        """便捷方法：调用自身服务"""
        signal = NeuroSignal.create_request(
            source=self.domain_name,
            signal_type="service_call",
            payload={"action": action, "data": data or {}},
            targets=target_domains or [],
            priority=priority,
        )
        return await self.on_receive(signal)

    def __repr__(self) -> str:
        return (
            f"ServiceDomain(name={self.service_name}, "
            f"v={self.version}, handlers={len(self._business_handlers)})"
        )
