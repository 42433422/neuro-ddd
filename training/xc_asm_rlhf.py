#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则驱动偏好数据：Oracle 汇编为 chosen，损坏样本为 rejected，供 DPO/ORPO 等离线 RLHF。
同时写入 rule_reward 分量便于过滤。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from xc_asm_validate import basic_asm_sanity, corrupt_asm_negative_sample


def load_jsonl(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def prompt_for_row(row: dict, hierarchical: bool) -> str:
    instr = "将 XC 翻译为 RISC-V64 GNU 汇编，只输出汇编。"
    inp = row["hierarchical_input"] if hierarchical else row["xc_source"]
    return f"{instr}\n\n### 输入\n{inp}\n\n### 汇编\n"


def quick_reward(asm: str) -> dict:
    ok_s, s_msg = basic_asm_sanity(asm)
    n_lines = len([x for x in asm.splitlines() if x.strip()])
    return {"sanity_ok": ok_s, "sanity_msg": s_msg, "lines": n_lines}


def load_failed_pool(path: Path | None) -> list[str]:
    if path is None or not path.is_file():
        return []
    arr: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            t = line.strip()
            if t:
                arr.append(t)
    return arr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_jsonl", type=str, default=str(ROOT / "dataset" / "xc_asm_train.jsonl"))
    ap.add_argument("--out_jsonl", type=str, default=str(ROOT / "dataset" / "xc_asm_dpo.jsonl"))
    ap.add_argument("--hierarchical", action="store_true")
    ap.add_argument("--failed_pool", type=str, default="", help="历史失败汇编文本池（每行一条）")
    ap.add_argument("--rejected_mode", choices=["corrupt", "mix"], default="mix")
    args = ap.parse_args()
    inp = Path(args.in_jsonl)
    if not inp.is_file():
        print(f"Missing {inp}")
        sys.exit(1)
    out = Path(args.out_jsonl)
    out.parent.mkdir(parents=True, exist_ok=True)
    failed_pool = load_failed_pool(Path(args.failed_pool)) if args.failed_pool else []
    n = 0
    with open(out, "w", encoding="utf-8") as fo:
        for row in load_jsonl(inp):
            chosen = row["asm_riscv64"].strip()
            if not chosen:
                continue
            rejected = corrupt_asm_negative_sample(chosen)
            if args.rejected_mode == "mix" and failed_pool and (n % 2 == 1):
                rejected = failed_pool[n % len(failed_pool)]
            prompt = prompt_for_row(row, args.hierarchical)
            rec = {
                "prompt": prompt,
                "chosen": chosen,
                "rejected": rejected,
                "oracle_reward": quick_reward(chosen),
                "rejected_reward": quick_reward(rejected),
                "meta": row.get("meta", {}),
            }
            fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"Wrote {n} preference pairs to {out}")


if __name__ == "__main__":
    main()
