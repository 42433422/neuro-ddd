# XC AI Compiler

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Mamba-SSM-orange?style=flat-square" alt="Mamba">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/RISC--V-64--bit-purple?style=flat-square" alt="RISC-V">
</p>

> 🤖 基于Mamba架构的XC语言AI编译器 - XC → Mamba → RISC-V64 Assembly

## ✨ 特性

- 🎯 **Mamba架构** - 线性时间复杂度的状态空间模型，比Transformer更高效
- ⚡ **自研RISC-V Oracle** - 独立规则编译器生成训练标签，不依赖GCC/Clang
- 🔄 **多目标代码生成** - 支持 C / Rust / Mojo / RISC-V64 汇编
- 🧪 **可复现实验** - 完整的数据生成、训练、评估流程
- 📊 **课程学习** - 支持分阶段训练（base/feature/mix）
- 💾 **单卡可训** - 130M/370M参数，RTX GPU即可

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      XC AI Compiler (Mamba)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   XC Source ──► [Lexer] ──► [Parser] ──► AST                   │
│                                              │                   │
│                                              ▼                   │
│   ┌────────────────────────────────────────────────────────┐   │
│   │                   数据工厂 (Data Factory)                │   │
│   │  ┌─────────────┐    ┌─────────────────────────────┐  │   │
│   │  │ Random XC   │───►│ RISC-V64 Oracle (规则编译器)  │  │   │
│   │  │ Generator   │    │ 生成Ground Truth汇编         │  │   │
│   │  └─────────────┘    └─────────────────────────────┘  │   │
│   └────────────────────────────────────────────────────────┘   │
│                         │                                        │
│                         ▼                                        │
│   ┌────────────────────────────────────────────────────────┐   │
│   │                      Mamba SSM                          │   │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │   │
│   │  │ Token    │  │ Selective│  │ Hardware  │  │Assembly│  │   │
│   │  │Embedding │──►│  State   │──►│  Aware   │──►│Decoder │  │   │
│   │  │          │  │  Space    │  │  Scan     │  │        │  │   │
│   │  └──────────┘  └──────────┘  └──────────┘  └────────┘  │   │
│   └────────────────────────────────────────────────────────┘   │
│                         │                                        │
│                         ▼                                        │
│   Output: RISC-V64 GNU Assembly                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 为什么用Mamba？

| 特性 | Transformer | Mamba |
|------|-------------|-------|
| 复杂度 | O(n²) | **O(n)** |
| 序列长度 | 受限于attention | **可处理超长序列** |
| 推理速度 | 慢（完整attention） | **快（线性扫描）** |
| 显存占用 | 高 | **低** |
| 代码生成 | 稳定 | **相当/更好** |

## 📁 项目结构

```
xc-ai-compiler/
├── xc_compiler.py          # XC语言编译器 (XC → C/Rust/Mojo)
├── x_compiler.py           # 简化版XC编译器
├── xc_preprocess.py        # 预处理模块
├── xc_asm_oracle.py        # RISC-V64 Oracle (规则编译器)
├── xc_asm_config.py        # 工具链配置
├── xc_asm_validate.py      # 汇编校验工具
│
├── dataset/                # 数据集
│   ├── build_xc_asm_corpus.py   # 数据集构建脚本
│   ├── xc_asm_synth.py          # XC程序随机生成器
│   ├── xc_asm_train.jsonl       # 训练数据
│   ├── xc_asm_val.jsonl         # 验证数据
│   └── xc_asm_test.jsonl        # 测试数据
│
├── training/              # 训练脚本
│   └── train_xc_mamba.py       # Mamba微调入口
│
├── inference/             # 推理脚本
│   └── xc_compile_ml.py        # AI编译器推理
│
├── run_first_ai_compiler.py    # 一键训练脚本
│
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install torch transformers datasets accelerate
pip install mamba-ssm    # 可选，提升性能
```

### 2. 一键训练（推荐）

```bash
# Step 1: 生成训练数据
python run_first_ai_compiler.py prepare --count 500

# Step 2: Mamba微调
python run_first_ai_compiler.py train --epochs 2 --model mamba-130m

# Step 3: 验证集评估
python run_first_ai_compiler.py gate
```

### 3. 使用AI编译器

```bash
# 交互模式
python inference/xc_compile_ml.py --model models/xc-asm-mamba/final --xc '# { $x = 10 ! x }'

# 文件模式
python inference/xc_compile_ml.py --model models/xc-asm-mamba/final --file input.x
```

### 4. Oracle对照（无需训练）

```bash
python run_first_ai_compiler.py demo
```

## 📖 XC 语言示例

```xc
# 程序入口
{
    $x: int = 10
    $y: int = 20
    $sum: int = x + y

    ! "x + y = ", sum

    % add(a: int, b: int) -> int {
        ^ a + b
    }

    ! add(3, 5)

    ? (x > y) {
        ! "x > y"
    } ?: {
        ! "x <= y"
    }

    ~i: int = 0; i < 5; i = i + 1 {
        ! i
    }
}
```

### 语法速查

| XC符号 | 含义 | 示例 |
|--------|------|------|
| `# { }` | 程序入口 | `# { ... }` |
| `$x` | 变量声明 | `$x = 10` |
| `$x: int` | 显式类型 | `$x: int = 10` |
| `@PI` | 常量 | `@PI = 3.14` |
| `% func` | 函数定义 | `% add(a, b) { ... }` |
| `^` | 返回 | `^ a + b` |
| `? (cond) { }` | 条件 | `? (x > 0) { ... }` |
| `?: { }` | else | `?: { ... }` |
| `?? (cond) { }` | else if | `?? (x < 0) { ... }` |
| `@ (cond) { }` | while循环 | `@ (i < 10) { ... }` |
| `~i=0; i<10; i++ { }` | for循环 | `~i=0; i<10; i=i+1 { ... }` |
| `>` | break | `>` |
| `<` | continue | `<` |
| `! x` | 打印 | `! "hello"` |
| `& Point { }` | 结构体 | `& Point { x: int; y: int; }` |

## 🔬 技术细节

### Mamba模型配置

```python
MODEL_CONFIGS = {
    "mamba-130m": {"name": "state-spaces/mamba-130m-hf", "max_len": 4096},
    "mamba-370m": {"name": "state-spaces/mamba-370m-hf", "max_len": 4096},
}
```

### 训练策略

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--model` | mamba-130m | 130M或370M参数 |
| `--epochs` | 2 | 训练轮数 |
| `--batch_size` | 2 | 批次大小 |
| `--lr` | 2e-4 | 学习率 |
| `--curriculum_phase` | mix | 课程学习阶段 |

### 课程学习阶段

- `base` - 仅简单样本（easy难度）
- `feature` - 仅复杂样本（medium/hard难度）
- `mix` - 混合所有难度

## 📊 技术规格

| 组件 | 实现 |
|------|------|
| 词法分析器 | 正则表达式 + 状态机 |
| 语法分析器 | 递归下降解析器 |
| AST | dataclass 树结构 |
| 代码生成器 | C / Rust / Mojo / RISC-V64 |
| Oracle | RV64G 整数子集 |
| AI模型 | Mamba (SSM) |
| 目标ISA | RISC-V 64-bit (RV64GC) |

## 🎯 路线图

- [x] XC语言编译器 (XC → C/Rust/Mojo)
- [x] RISC-V64 Oracle 规则后端
- [x] Mamba架构微调框架
- [x] 数据生成器 (xc_asm_synth)
- [ ] 层级注意力增强
- [ ] RLHF微调
- [ ] 性能优化与量化

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📚 参考

- [Mamba: Linear-Time Sequence Modeling](https://arxiv.org/abs/2312.00752)
- [RISC-V ISA Specification](https://riscv.org/technical/specifications/)
- [XC Language Compiler](file:///e:/X语音/compiler/)
