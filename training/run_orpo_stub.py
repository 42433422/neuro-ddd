#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORPO/DPO 训练占位脚本（单卡可执行的前处理与配置检查）。
若未安装 trl/peft/transformers，将仅输出建议命令。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def count_jsonl(path: Path) -> int:
    n = 0
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            if ln.strip():
                n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpo_jsonl", type=str, required=True)
    ap.add_argument("--model", type=str, default="Qwen/Qwen2.5-Coder-1.5B")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--batch_size", type=int, default=1)
    args = ap.parse_args()

    p = Path(args.dpo_jsonl)
    if not p.is_file():
        raise SystemExit(f"missing {p}")
    n = count_jsonl(p)
    print(f"[DPO/ORPO] dataset={p} rows={n} model={args.model}")
    try:
        import trl  # noqa: F401
        import transformers  # noqa: F401
        import peft  # noqa: F401
    except Exception:
        print("缺少依赖，先执行:")
        print("  pip install trl transformers peft accelerate datasets")
        print("然后使用你偏好的 DPOTrainer/ORPOTrainer 读取该 jsonl 开始训练。")
        return
    print("依赖检查通过：请在此脚本中接入你选定的 ORPO/DPO trainer（项目留作后续接线）。")


if __name__ == "__main__":
    main()
