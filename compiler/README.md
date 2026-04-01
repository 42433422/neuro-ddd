# XC AI Compiler

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PyTorch-2.0+-orange?style=flat-square&logo=pytorch" alt="PyTorch">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/RISC--V-64--bit-purple?style=flat-square" alt="RISC-V">
</p>

> 🤖 纯AI驱动的XC语言编译器 - XC → Transformer → RISC-V64 Assembly

## ✨ 特性

- 🎯 **纯AI编译** - 无传统编译器后端，Transformer直接生成目标代码
- ⚡ **自研RISC-V Oracle** - 独立规则编译器生成训练标签，不依赖GCC/Clang
- 🔄 **多目标代码生成** - 支持 C / Rust / Mojo / RISC-V64 汇编
- 🧪 **可复现实验** - 完整的数据生成、训练、评估流程
- 📊 **层级注意力架构** - 针对程序结构优化的Transformer设计

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        XC AI Compiler                           │
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
│   │           Hierarchical Transformer                     │   │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │   │
│   │  │ Token    │  │Function  │  │Program   │  │Assembly│  │   │
│   │  │ Embedding│  │Attention │  │Attention│  │Decoder │  │   │
│   │  └──────────┘  └──────────┘  └──────────┘  └────────┘  │   │
│   └────────────────────────────────────────────────────────┘   │
│                         │                                        │
│                         ▼                                        │
│   Output: Assembly / C / Rust / Mojo                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
xc-ai-compiler/
├── xc_compiler.py          # XC语言编译器 (XC → C/Rust/Mojo)
├── x_compiler.py           # 简化版XC编译器
├── xc_preprocess.py        # 预处理模块
├── xc_asm_oracle.py        # RISC-V64 Oracle (规则编译器)
├── xc_asm_config.py        # 工具链配置
├── xc_translate.py         # AI翻译推理脚本
├── x_language.py          # 项目启动器
├── AI_Compiler_Roadmap.md  # 技术路线图
│
├── dataset/                # 数据集目录 (需生成)
│   └── xc_riscv64/        # XC ↔ RISC-V 配对数据
│
├── training/              # 训练脚本 (需实现)
│   └── train_translator.py
│
├── models/                # 模型目录
│   └── xc-translator/     # 微调后的模型
│
├── examples/              # 示例XC程序
│   ├── hello.x
│   ├── fibonacci.x
│   └── algorithm.x
│
└── eval/                  # 评估脚本
    └── benchmark.py
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install torch transformers peft datasets unsloth
```

### 2. 编译XC代码 (传统方式)

```bash
# XC → C
python x_compiler.py --input examples/hello.x --target c

# XC → Rust
python x_compiler.py --input examples/hello.x --target rust

# XC → RISC-V64 汇编
python x_compiler.py --input examples/hello.x --target riscv64
```

### 3. 使用AI翻译器

```bash
# 交互模式
python xc_translate.py --demo

# 文件翻译
python xc_translate.py --input code.x --source x --target rust
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

## 🔬 训练自己的模型

### 步骤1: 生成训练数据

```python
from xc_asm_oracle import compile_xc_to_asm_riscv64

# 生成 XC ↔ RISC-V 配对数据
def generate_training_pair():
    xc_code = generate_random_xc_program()  # 你的随机生成器
    asm_code = compile_xc_to_asm_riscv64(xc_code)
    return {"xc": xc_code, "asm": asm_code}
```

### 步骤2: 微调模型

```bash
python training/train_translator.py \
    --model qwen2.5-coder-1.5b \
    --epochs 3 \
    --batch_size 4
```

### 步骤3: 评估

```bash
python eval/benchmark.py --model models/xc-translator
```

## 📊 技术规格

| 组件 | 实现 |
|------|------|
| 词法分析器 | 正则表达式 + 状态机 |
| 语法分析器 | 递归下降解析器 |
| AST | dataclass 树结构 |
| 代码生成器 | C / Rust / Mojo / RISC-V64 |
| Oracle | RV64G 整数子集 |
| 目标ISA | RISC-V 64-bit (RV64GC) |

## 🎯 路线图

- [x] XC语言编译器 (XC → C/Rust/Mojo)
- [x] RISC-V64 Oracle 规则后端
- [ ] 数据生成器 (100K+ 训练样本)
- [ ] Hierarchical Transformer 实现
- [ ] RLHF 微调
- [ ] 性能优化与量化

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📚 参考

- [Transformer: Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [CodeGen: Open Code Generation](https://arxiv.org/abs/2203.13474)
- [RISC-V ISA Specification](https://riscv.org/technical/specifications/)
