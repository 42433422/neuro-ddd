#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规模化构建 XC ↔ RISC-V 汇编 JSONL（train/val/test + 去重 + 分桶统计）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dataset.xc_asm_synth import generate_one_with_meta, hierarchical_wrap
from xc_asm_validate import get_toolchain_info
from xc_asm_oracle import compile_xc_to_asm_riscv64_with_reason
from xc_compiler import compile_xc


def _norm(s: str) -> str:
    return "\n".join(x.rstrip() for x in s.strip().splitlines())


def xc_hash(xc: str) -> str:
    return hashlib.sha256(_norm(xc).encode("utf-8")).hexdigest()


def build_record(item: Dict, seed: int, idx: int, keep_unsupported: bool) -> Dict | None:
    xc = item["xc_source"]
    res = compile_xc_to_asm_riscv64_with_reason(xc)
    if (not res["ok"]) and (not keep_unsupported):
        return None
    hier, span_meta = hierarchical_wrap(xc)
    try:
        c_ref = compile_xc(xc, "c")
    except Exception:
        c_ref = None
    return {
        "id": f"xcasm_{idx}_{seed}",
        "xc_source": _norm(xc),
        "asm_riscv64": _norm(res["asm"] or ""),
        "c_reference": c_ref,
        "hierarchical_input": hier,
        "spans": span_meta,
        "feature_tags": item.get("feature_tags", []),
        "difficulty_level": item.get("difficulty_level", "unknown"),
        "unsupported_reason": res.get("unsupported_reason"),
        "meta": {"isa": "riscv64", "dialect": "gnu", "seed": seed, "toolchain_hint": get_toolchain_info()},
    }


def write_jsonl(path: Path, rows: Iterable[Dict]) -> int:
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n


def split_rows(rows: List[Dict], train_ratio: float, val_ratio: float, seed: int) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    rng = random.Random(seed + 991)
    rows = rows[:]
    rng.shuffle(rows)
    n = len(rows)
    nt = int(n * train_ratio)
    nv = int(n * val_ratio)
    return rows[:nt], rows[nt:nt + nv], rows[nt + nv :]


def bucket_stats(rows: List[Dict]) -> Dict:
    by_diff: Dict[str, int] = {}
    by_tag: Dict[str, int] = {}
    unsupported = 0
    for r in rows:
        d = r.get("difficulty_level", "unknown")
        by_diff[d] = by_diff.get(d, 0) + 1
        for t in r.get("feature_tags", []):
            by_tag[t] = by_tag.get(t, 0) + 1
        if r.get("unsupported_reason"):
            unsupported += 1
    return {"count": len(rows), "difficulty": by_diff, "tags": by_tag, "unsupported": unsupported}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out_dir", type=str, default=str(ROOT / "dataset"))
    ap.add_argument("--prefix", type=str, default="xc_asm")
    ap.add_argument("--keep_unsupported", action="store_true")
    ap.add_argument("--train_ratio", type=float, default=0.9)
    ap.add_argument("--val_ratio", type=float, default=0.05)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    rows: List[Dict] = []
    seen = set()
    attempts = 0
    max_attempts = max(args.count * 30, 1000)
    while len(rows) < args.count and attempts < max_attempts:
        attempts += 1
        item = generate_one_with_meta(rng)
        h = xc_hash(item["xc_source"])
        if h in seen:
            continue
        seen.add(h)
        rec = build_record(item, args.seed, len(rows), args.keep_unsupported)
        if rec is None:
            continue
        rec["xc_hash"] = h
        rows.append(rec)

    train, val, test = split_rows(rows, args.train_ratio, args.val_ratio, args.seed)
    p_train = out_dir / f"{args.prefix}_train.jsonl"
    p_val = out_dir / f"{args.prefix}_val.jsonl"
    p_test = out_dir / f"{args.prefix}_test.jsonl"
    n_train = write_jsonl(p_train, train)
    n_val = write_jsonl(p_val, val)
    n_test = write_jsonl(p_test, test)

    write_jsonl(out_dir / f"{args.prefix}_all.jsonl", rows)
    summary = {
        "attempts": attempts,
        "unique_rows": len(rows),
        "files": {"train": str(p_train), "val": str(p_val), "test": str(p_test)},
        "stats": {"train": bucket_stats(train), "val": bucket_stats(val), "test": bucket_stats(test)},
    }
    with open(out_dir / f"{args.prefix}_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(
        f"Built rows={len(rows)} train={n_train} val={n_val} test={n_test} "
        f"(attempts={attempts}, keep_unsupported={args.keep_unsupported})"
    )


if __name__ == "__main__":
    main()
