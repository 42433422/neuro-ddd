"""
XC → C 预处理：抽取 #include / #define / #ifdef 等行，并将 ⟨ 族指令降为 C 预处理。
"""

import re
from typing import List, Tuple

_C_LINE = re.compile(
    r"^\s*#(?:include|define|ifdef|ifndef|endif|else|undef)\b.*$"
)
_ANGLE = re.compile(
    r"^\s*⟨([HDUFNEJ])\s*(.*)$"
)


def translate_angle_line(line: str) -> str:
    """⟨H "x.h" → #include "x.h"；⟨D A 1 → #define A 1；等。"""
    m = _ANGLE.match(line)
    if not m:
        return line
    cmd, rest = m.group(1), m.group(2).rstrip()
    rest = rest.strip()
    if cmd == "H":
        return f"#include {rest}"
    if cmd == "D":
        return f"#define {rest}"
    if cmd == "U":
        return f"#undef {rest}"
    if cmd == "F":
        return f"#ifdef {rest}"
    if cmd == "N":
        return f"#ifndef {rest}"
    if cmd == "E":
        return "#else"
    if cmd == "J":
        return "#endif"
    return line


def split_preprocessor_and_body(source: str) -> Tuple[List[str], str]:
    """
    抽出可直通 C 的预处理行（#... 或 ⟨...），其余拼回 XC 正文供词法分析。
    """
    prep: List[str] = []
    body_lines: List[str] = []
    for line in source.splitlines():
        raw = line
        s = line.strip()
        if _C_LINE.match(line):
            prep.append(line.rstrip())
        elif s.startswith("⟨"):
            prep.append(translate_angle_line(line).rstrip())
        else:
            body_lines.append(raw)
    return prep, "\n".join(body_lines)


def needs_stdlib_h(xc_and_c: str) -> bool:
    if re.search(r"\b(malloc|calloc|realloc|free)\b", xc_and_c):
        return True
    return "\u03a9" in xc_and_c  # ΩM / ΩF / …


def needs_string_h(xc_and_c: str) -> bool:
    return bool(re.search(r"\b(strlen|strcpy|strcmp|strcat|memcmp)\b", xc_and_c))


def needs_stdio_extra(xc_and_c: str) -> bool:
    return bool(re.search(r"\b(fopen|fread|fwrite|fclose|fprintf|fscanf)\b", xc_and_c))
