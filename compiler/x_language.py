"""
C ↔ Rust ↔ Mojo 三语互译模型 - 快速启动脚本

使用方法:
1. 先安装依赖: pip install torch transformers peft datasets unsloth
2. 下载数据集: python dataset/dataset_builder.py
3. 训练模型: python training/train_translator.py --model qwen2.5-coder-1.5b --epochs 3
4. 运行翻译: python inference/translator.py --source c --target rust --input your_code.c
"""

import os
import sys


def check_dependencies():
    """检查依赖是否安装"""
    required = {
        "torch": "PyTorch (深度学习框架)",
        "transformers": "Transformers (模型库)",
        "peft": "PEFT (LoRA微调)",
        "datasets": "Datasets (数据处理)",
    }

    optional = {
        "unsloth": "UnSloth (加速训练, 推荐安装)",
        "bitsandbytes": "BitsAndBytes (4bit量化)",
    }

    missing_required = []
    missing_optional = []

    for module, name in required.items():
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            missing_required.append(name)
            print(f"✗ {name} - 未安装")

    for module, name in optional.items():
        try:
            __import__(module)
            print(f"✓ {name} (可选)")
        except ImportError:
            missing_optional.append(name)
            print(f"○ {name} - 可选未安装")

    if missing_required:
        print("\n请安装缺失的必需依赖:")
        print(f"pip install {' '.join(missing_required)}")
        return False

    if missing_optional:
        print("\n建议安装可选依赖以提升性能:")
        print(f"pip install {' '.join(missing_optional)}")

    return True


def check_models_dir():
    """检查模型目录"""
    models_dir = Path("e:/X语音/models")
    if not models_dir.exists():
        models_dir.mkdir(parents=True)
        print(f"✓ 创建模型目录: {models_dir}")
    else:
        print(f"✓ 模型目录已存在: {models_dir}")

    return True


def print_help():
    """打印帮助信息"""
    help_text = """
╔══════════════════════════════════════════════════════════════════════════╗
║                    C ↔ Rust ↔ Mojo 三语互译模型                            ║
║                          XC语言 - AI 代码翻译器                              ║
╚══════════════════════════════════════════════════════════════════════════╝

📋 工作流程:

1️⃣  安装依赖:
    pip install torch transformers peft datasets unsloth

2️⃣  构建数据集:
    python dataset/dataset_builder.py

3️⃣  训练模型 (选择一种):
    # 快速验证 (Qwen2.5-Coder-1.5B, ~4GB显存)
    python training/train_translator.py --model qwen2.5-coder-1.5b --epochs 3

    # 推荐配置 (Qwen2.5-Coder-7B, ~16GB显存)
    python training/train_translator.py --model qwen2.5-coder-7b --epochs 3

    # StarCoder2 (7B版本)
    python training/train_translator.py --model starcoder2-7b --epochs 3

4️⃣  运行翻译:
    # 单文件翻译
    python inference/translator.py --source c --target rust --input code.c

    # 交互模式
    python inference/translator.py --source rust --target mojo

🔧 支持的翻译方向:
    • C ↔ Rust
    • C ↔ Mojo
    • Rust ↔ Mojo

📁 项目结构:
    dataset/          - 数据集目录
      C_Rust/         - C-Rust 配对数据
      Rust_Mojo/      - Rust-Mojo 配对数据
      final/          - 合并后的完整数据集

    models/            - 保存的模型
    training/          - 训练脚本
    inference/         - 推理脚本
    utils/             - 工具函数

⚡ 数据集来源:
    • CRUST-Bench (C→Rust, 100个仓库级配对)
    • TransCoder-IR (竞赛级代码配对)
    • CodeSearchNet (代码搜索数据集)
    • 合成生成 (Rust↔Mojo)

💡 提示:
    • 建议使用至少 16GB 显存进行训练
    • 可以使用 GGUF 量化后在消费级GPU运行
    • 翻译结果建议人工检查编译正确性
"""
    print(help_text)


def main():
    from pathlib import Path

    print("=" * 60)
    print("XC语言 - C ↔ Rust ↔ Mojo 三语互译模型")
    print("=" * 60)
    print()

    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        return

    if len(sys.argv) == 1:
        print_help()
        print("\n🔍 正在检查环境...\n")
        check_dependencies()
        check_models_dir()
    else:
        check_dependencies()


if __name__ == "__main__":
    main()
