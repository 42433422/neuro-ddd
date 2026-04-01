"""
XC → 汇编工具链配置（根目录入口）。
"""

from __future__ import annotations

import os
import shutil

ISA_NAME = "riscv64"
ASM_DIALECT = "gnu"
XLEN = 64

ENV_AS = "XC_RISCV_AS"
ENV_LD = "XC_RISCV_LD"
ENV_QEMU = "XC_RISCV_QEMU"

DEFAULT_AS_CMDS = ("riscv64-linux-gnu-as", "riscv64-unknown-linux-gnu-as", "as")
DEFAULT_LD_CMDS = ("riscv64-linux-gnu-ld", "riscv64-unknown-linux-gnu-ld", "ld")
DEFAULT_QEMU_CMDS = ("qemu-riscv64",)


def resolve_tool(cmds: tuple[str, ...], env_key: str) -> str | None:
    override = os.environ.get(env_key, "").strip()
    if override:
        return override
    for c in cmds:
        p = shutil.which(c)
        if p:
            return p
    return None


def get_toolchain_info() -> dict:
    return {
        "isa": ISA_NAME,
        "dialect": ASM_DIALECT,
        "as": resolve_tool(DEFAULT_AS_CMDS, ENV_AS),
        "ld": resolve_tool(DEFAULT_LD_CMDS, ENV_LD),
        "qemu": resolve_tool(DEFAULT_QEMU_CMDS, ENV_QEMU),
    }
"""
XC → 汇编 Oracle：固定 ISA 与元数据（训练/校验共用）。
采用 RISC-V 64 位、GNU 汇编方言、整数子集；不依赖 LLVM 作运行时。
"""

from __future__ import annotations

ISA_NAME = "riscv64"
ASM_DIALECT = "gnu"
# XC int 按 32 位语义用 *w 指令
XLEN = 64

# 数据工厂与校验器识别的环境变量 / 默认命令前缀（可选）
import os

ENV_AS = "XC_RISCV_AS"
ENV_LD = "XC_RISCV_LD"
ENV_QEMU = "XC_RISCV_QEMU"

DEFAULT_AS_CMDS = (
    "riscv64-linux-gnu-as",
    "riscv64-unknown-linux-gnu-as",
    "as",
)
DEFAULT_LD_CMDS = (
    "riscv64-linux-gnu-ld",
    "riscv64-unknown-linux-gnu-ld",
    "ld",
)
DEFAULT_QEMU_CMDS = (
    "qemu-riscv64",
)


def resolve_tool(cmds: tuple[str, ...], env_key: str) -> str | None:
    override = os.environ.get(env_key, "").strip()
    if override:
        return override
    import shutil

    for c in cmds:
        p = shutil.which(c)
        if p:
            return p
    return None


def get_toolchain_info() -> dict:
    return {
        "isa": ISA_NAME,
        "dialect": ASM_DIALECT,
        "as": resolve_tool(DEFAULT_AS_CMDS, ENV_AS),
        "ld": resolve_tool(DEFAULT_LD_CMDS, ENV_LD),
        "qemu": resolve_tool(DEFAULT_QEMU_CMDS, ENV_QEMU),
    }
