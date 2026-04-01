"""
XC 语言四语对照数据集生成器
生成用于训练 XC 翻译模型的数据集
"""

import json
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dataset.xc_quad_samples import generate_pairs, get_all_samples


def format_for_training(pairs):
    """格式化训练数据"""
    lang_names = {"x": "XC", "c": "C", "rust": "Rust", "mojo": "Mojo"}

    formatted = []
    templates = [
        "将{l1}代码翻译为{l2}，只输出{l2}代码:",
        "{l1} → {l2}:",
        "Translate this {l1} code to {l2}:",
    ]

    for pair in pairs:
        template = random.choice(templates)
        source_name = lang_names[pair["source_lang"]]
        target_name = lang_names[pair["target_lang"]]

        instruction = template.format(l1=source_name, l2=target_name)

        formatted.append({
            "instruction": instruction,
            "input": pair["source_code"],
            "output": pair["target_code"],
            "source_lang": pair["source_lang"],
            "target_lang": pair["target_lang"],
            "name": pair.get("name", ""),
        })

    return formatted


def generate_training_dataset():
    """生成训练数据集"""
    print("=" * 60)
    print("XC 语言四语对照数据集生成器")
    print("=" * 60)

    output_dir = Path("e:/X语音/dataset")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n[1] 生成语言对配对...")
    pairs = generate_pairs()
    print(f"  生成了 {len(pairs)} 个语言对")

    print("\n[2] 保存原始配对...")
    with open(output_dir / "xc_pairs_raw.json", "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)

    print("\n[3] 格式化训练数据...")
    formatted = format_for_training(pairs)
    with open(output_dir / "xc_training_data.json", "w", encoding="utf-8") as f:
        json.dump(formatted, f, ensure_ascii=False, indent=2)

    print("\n[4] 保存纯文本格式...")
    with open(output_dir / "xc_pairs.txt", "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(f"=== {pair['source_lang'].upper()} → {pair['target_lang'].upper()} ===\n")
            f.write(pair["source_code"] + "\n")
            f.write("---\n")
            f.write(pair["target_code"] + "\n")
            f.write("\n")

    print("\n" + "=" * 60)
    print("数据集统计:")
    print("=" * 60)

    samples = get_all_samples()
    print(f"  原始样本数: {len(samples)}")
    print(f"  语言对配对数: {len(pairs)}")
    print(f"  格式化训练数据: {len(formatted)}")

    lang_counts = {}
    for pair in pairs:
        src = pair["source_lang"]
        lang_counts[src] = lang_counts.get(src, 0) + 1

    print("\n  各语言样本数:")
    for lang, count in sorted(lang_counts.items()):
        print(f"    {lang.upper()}: {count}")

    print("\n" + "=" * 60)
    print(f"数据集已保存到: {output_dir}")
    print("=" * 60)

    return pairs, formatted


if __name__ == "__main__":
    generate_training_dataset()
