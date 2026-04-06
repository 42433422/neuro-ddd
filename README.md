# Neuro-DDD: Neuro-Inspired Domain-Driven Design

<div align="center">

🧠 **类脑神经 DDD 架构框架** | 仿生人脑神经元工作机制的下一代领域驱动设计

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Async](https://img.shields.io/badge/Async-Await-green?style=flat-square)](https://docs.python.org/3/library/asyncio.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](https://opensource.org/licenses/MIT)

</div>

---

## 📖 简介

Neuro-DDD 是一个创新的软件架构框架，灵感来源于人脑神经元的工作机制。它通过**显意识/潜意识双模式处理**、**异步广播通信**和**并发调度**，为复杂的多领域协同场景提供高性能、松耦合的解决方案。

### 核心问题解决

传统 DDD（领域驱动设计）在复杂系统中面临以下挑战：
- ❌ 领域间紧耦合，调用链复杂
- ❌ 同步阻塞导致性能瓶颈
- ❌ 错误传播和恢复机制不完善
- ❌ 难以平衡响应速度和处理准确性

Neuro-DDD 通过仿生人脑的神经信号传递机制，实现：
- ✅ **发布/订阅模式**的广播通信
- ✅ **System 1 & System 2** 双模式处理（潜意识快速响应 + 显意识精确推理）
- ✅ **异步并发**架构，多领域同时处理
- ✅ **自愈能力**，三级错误反馈 + 熔断器模式

---

## 🚀 核心特性

### 1. 显意识/潜意识双模式处理

```python
from neuro_ddd_software import DualModeStrategy, DualModeEngine

# 快速优先策略：先尝试潜意识快速处理，失败后降级到显意识
engine = DualModeEngine(strategy=DualModeStrategy.FAST_FIRST)

# 处理信号，潜意识模式 <10ms，显意识模式 ~100ms
result = await engine.process(signal, context, handler)
```

| 模式 | 延迟 | 准确性 | 使用场景 |
|------|------|--------|----------|
| **潜意识 (Subconscious)** | <10ms | 85-95% | 模式匹配、缓存查询、直觉决策 |
| **显意识 (Conscious)** | 100ms~ | 99%+ | 复杂计算、逻辑推理、验证确认 |

### 2. 异步广播通信

```python
from neuro_ddd_software import AsyncNeuroBus, NeuroSignal

async with AsyncNeuroBus() as bus:
    # 注册领域
    bus.register("order_domain", order_handler)
    bus.register("inventory_domain", inventory_handler)
    bus.register("payment_domain", payment_handler)
    
    # 广播信号，所有领域同时接收并处理
    signal = NeuroSignal.create_request(
        signal_type="order.created",
        payload={"order_id": "12345"},
        target_domains=["order", "inventory", "payment"]
    )
    
    # 并行投递，非阻塞
    results = await bus.broadcast(signal, wait_for_results=True)
```

### 3. 四种并发策略

```python
from neuro_ddd_software import ConcurrencyStrategy, ConcurrentScheduler

scheduler = ConcurrentScheduler()

# 并行执行：所有任务同时运行
await scheduler.execute(tasks, strategy=ConcurrencyStrategy.PARALLEL)

# 顺序执行：按顺序一个接一个
await scheduler.execute(tasks, strategy=ConcurrencyStrategy.SEQUENTIAL)

# 流水线：阶段间并行
await scheduler.execute(tasks, strategy=ConcurrencyStrategy.PIPELINE)

# FAN_OUT/FAN_IN：分发 - 聚合模式
results = await scheduler.execute(tasks, strategy=ConcurrencyStrategy.FAN_OUT)
aggregated = scheduler.fan_in(results)
```

### 4. 错误反馈系统

```python
from neuro_ddd_software import ErrorFeedbackSystem, ErrorSeverity

feedback_system = ErrorFeedbackSystem()

# 即时反馈：立即重试
await feedback_system.report_error(error, severity=ErrorSeverity.IMMEDIATE)

# 延迟反馈：稍后重试
await feedback_system.report_error(error, severity=ErrorSeverity.DELAYED)

# 批量反馈：累积后统一处理
await feedback_system.report_error(error, severity=ErrorSeverity.BATCH)
```

### 5. 神经反射弧

```python
from neuro_ddd_software import ReflexArc

# 超快速响应 <1ms，绕过常规处理流程
reflex = ReflexArc()
reflex.register_reflex("emergency.stop", emergency_handler)

# 触发反射，直接执行处理器
await reflex.trigger("emergency.stop", payload)
```

---

## 📦 安装

本仓库为**框架源码**；将克隆目录加入 `PYTHONPATH` 或按需 `pip install -e .`（若根目录提供 `pyproject.toml` / `setup.cfg`）。

```bash
git clone https://github.com/42433422/neuro-ddd.git
cd neuro-ddd
export PYTHONPATH="$PWD:$PYTHONPATH"   # Linux/macOS
# set PYTHONPATH=%CD%;%PYTHONPATH%     # Windows cmd
```

---

## 🔧 快速开始

### 示例：电商订单系统（异步总线 + 订阅）

```python
import asyncio
from neuro_ddd_software import AsyncNeuroBus, NeuroSignal, ProcessingResult, SoftwareDomain

class OrderDomain(SoftwareDomain):
    def __init__(self) -> None:
        super().__init__("order")

    async def async_process_signal(self, signal, context):
        if signal.signal_type == "order.created":
            print(f"处理订单：{signal.payload}")
            return ProcessingResult(success=True)
        return ProcessingResult(success=True, result_data=None, metadata={"skipped": True})

class InventoryDomain(SoftwareDomain):
    def __init__(self) -> None:
        super().__init__("inventory")

    async def async_process_signal(self, signal, context):
        if signal.signal_type == "order.created":
            print(f"扣减库存：{signal.payload}")
            return ProcessingResult(success=True)
        return ProcessingResult(success=True, result_data=None, metadata={"skipped": True})

class PaymentDomain(SoftwareDomain):
    def __init__(self) -> None:
        super().__init__("payment")

    async def async_process_signal(self, signal, context):
        if signal.signal_type == "order.created":
            print(f"处理支付：{signal.payload}")
            return ProcessingResult(success=True)
        return ProcessingResult(success=True, result_data=None, metadata={"skipped": True})

async def main():
    async with AsyncNeuroBus() as bus:
        domains = [OrderDomain(), InventoryDomain(), PaymentDomain()]
        for d in domains:
            await d.set_bus(bus)
            bus.subscribe(d.domain_name, ["order.created"], d.on_receive)

        signal = NeuroSignal(
            signal_type="order.created",
            source_domain="api",
            target_domains=[d.domain_name for d in domains],
            payload={"order_id": "12345", "amount": 99.99},
        )
        results = await bus.broadcast(signal, wait_for_results=True)
        print(f"处理完成：{len(results)} 个领域响应")

asyncio.run(main())
```

**输出：**
```
处理订单：{'order_id': '12345', 'amount': 99.99}
扣减库存：{'order_id': '12345', 'amount': 99.99}
处理支付：{'order_id': '12345', 'amount': 99.99}
处理完成：3 个领域响应
```

---

## 📊 性能对比（可复现）

在仓库根目录执行：

```bash
python tools/benchmark_neuro_ddd_performance.py
```

完整原始数据写入 [`reports/neuro_ddd_benchmark.json`](reports/neuro_ddd_benchmark.json)（随 CI / 本机重跑更新）。以下为一次 **Windows / Python 3.11** 样例摘要（**非保证值**，以你机器上 JSON 为准）。

### 并行 vs 串行（3 个 handler / 领域，各带同等 `asyncio.sleep` 或 `time.sleep`）

| 场景 | 传统（同线程顺序 sleep） | AsyncNeuroBus 并行 `gather` | 说明 |
|------|--------------------------|----------------------------|------|
| 微延迟（每 handler ~2ms） | ~6.95 ms（中位数） | ~15.6 ms（中位数） | 延迟极短时，async 框架与调度开销可能超过收益 |
| I/O 型延迟（每 handler ~12ms） | ~37.2 ms（中位数） | ~15.5 ms（中位数） | 墙钟接近「单次 sleep」而非三次之和，约 **2.4×** 于并行侧更优 |

**结论**：加速比取决于「单次领域耗时」与领域数量；应用层应把 Neuro-DDD 用于 **I/O 边界 / 多领域协同**，勿与「纳秒级纯计算」对标。

### 简单 CRUD（500 次迭代样例）

| 路径 | 中位数延迟（单次 set+get） |
|------|---------------------------|
| 传统 Service + Repository | ~0.0004 ms |
| `SoftwareDomain.on_receive` ×2（不经总线广播） | ~0.020 ms |

### 同步内核 `neuro_ddd.NeuroBus`（2500 次广播样例）

| 方式 | 中位数 |
|------|--------|
| 手写 `for` 调 `on_receive` ×3 | ~0.0013 ms |
| `NeuroBus.broadcast` → 3 领域 | ~0.0040 ms |

总线含线程安全、路由与日志等，约为手写循环的 **数倍级微秒开销**（量级仍极低）。

### 双模式处理（示意）

双模式延迟与「准确率」依赖具体模型与负载，未在基准脚本中硬编码；请参考 `DualModeEngine` 与业务评测。

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                   AsyncNeuroBus                         │
│              (异步神经总线 - 广播中枢)                   │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Order Domain   │ │ Inventory Domain│ │ Payment Domain  │
│                 │ │                 │ │                 │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │Conscious  │  │ │  │Conscious  │  │ │  │Conscious  │  │
│  │Processor  │  │ │  │Processor  │  │ │  │Processor  │  │
│  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │Subconscious│ │ │  │Subconscious│ │ │  │Subconscious│ │
│  │Processor  │  │ │  │Processor  │  │ │  │Processor  │  │
│  └───────────┘  │ │  └───────────┘  │ │  └───────────┘  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 🔩 同步内核 `neuro_ddd`（工业向）

本仓库包含 **`neuro_ddd`** Python 包：同步总线、主题订阅、显式目标路由、`DomainEvent` / 聚合 / 仓储、`NeuroUnitOfWork`、**Outbox**、投递隔离策略（`DeliveryErrorPolicy`）等，可与 `neuro_ddd_software` 异步层组合使用。

```python
from neuro_ddd import NeuroBus, Signal, DomainType, DeliveryErrorPolicy
from neuro_ddd import NeuroUnitOfWork, InMemoryRepository, DomainEvent, AggregateRoot
```

---

## 📚 文档

- [完整软件框架文档](neuro_ddd_software/SOFTWARE_FRAMEWORK.md)（异步层）

---

## 🧪 测试与基准

```bash
# 可复现性能对比（生成 reports/neuro_ddd_benchmark.json）
python tools/benchmark_neuro_ddd_performance.py
```

可在本仓库根目录将 `neuro_ddd`、`neuro_ddd_software` 加入 `PYTHONPATH` 后编写自有 `pytest` 用例。

---

## 🎯 使用场景

### ✅ 适合的场景
- 多领域协同的复杂业务系统
- 需要高并发、低延迟的场景
- 需要快速响应和精确处理平衡的场景
- 事件驱动的架构设计

### ❌ 不适合的场景
- 简单的 CRUD 应用
- 单领域、无协同的系统
- 对性能要求不高的后台任务

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

<div align="center">

**Neuro-DDD** - 让软件架构更像人脑 🧠

Made with ❤️ by [42433422](https://github.com/42433422)

</div>
