#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证门控：统计 assemble pass（总体 + feature 分桶）。
输入 JSONL 需含:
- feature_tags
- asm_riscv64 (oracle) 或 pred_asm 字段（默认优先 pred_asm）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from xc_asm_validate import assemble_check


def load_jsonl(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", type=str, required=True)
    ap.add_argument("--pred_field", type=str, default="pred_asm")
    ap.add_argument("--fallback_field", type=str, default="asm_riscv64")
    ap.add_argument("--threshold", type=float, default=0.99)
    args = ap.parse_args()

    path = Path(args.jsonl)
    total = 0
    ok = 0
    by_tag: dict[str, list[int]] = {}
    for row in load_jsonl(path):
        asm = row.get(args.pred_field) or row.get(args.fallback_field) or ""
        tags = row.get("feature_tags") or ["_untagged"]
        passed, _ = assemble_check(asm)
        total += 1
        if passed:
            ok += 1
        for t in tags:
            by_tag.setdefault(t, [0, 0])
            by_tag[t][0] += 1
            by_tag[t][1] += 1 if passed else 0

    overall = (ok / total) if total else 0.0
    print(f"overall: {ok}/{total} = {overall:.4f}")
    for t, (n, p) in sorted(by_tag.items(), key=lambda x: x[0]):
        r = p / n if n else 0.0
        print(f"tag={t}: {p}/{n} = {r:.4f}")
    if overall >= args.threshold:
        print(f"GATE_PASS >= {args.threshold:.2f}")
    else:
        print(f"GATE_FAIL < {args.threshold:.2f}")


if __name__ == "__main__":
    main()
