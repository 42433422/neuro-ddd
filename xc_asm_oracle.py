"""
XC → RISC-V64 (GNU as) Oracle：自研规则后端，覆盖整数算法子集。
不经过 C；用于数据工厂标签与规则校验金标准。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from xc_preprocess import split_preprocessor_and_body

from xc_compiler import (
    ASTNode,
    BinaryOp,
    BoolLiteral,
    BreakStmt,
    Call,
    ContinueStmt,
    ForStmt,
    FuncDef,
    Identifier,
    IfStmt,
    NumberLiteral,
    Program,
    ReturnStmt,
    UnaryOp,
    VarDecl,
    WhileStmt,
    XCLexer,
    XCParser,
)


class AsmOracleUnsupported(Exception):
    """当前子集不支持的 AST 构造"""

    def __init__(self, msg: str, node: Optional[ASTNode] = None):
        super().__init__(msg)
        self.node = node


def parse_xc_program(xc_source: str) -> Program:
    _prep, body = split_preprocessor_and_body(xc_source)
    lexer = XCLexer(body)
    parser = XCParser(lexer.tokenize())
    return parser.parse()


_UNSUPPORTED_TYPES = frozenset(
    {
        "PrintStmt",
        "InputStmt",
        "StructDef",
        "UnionDef",
        "SwitchStmt",
        "LabelStmt",
        "GotoStmt",
        "StringLiteral",
        "IndexAccess",
        "MemberAccess",
        "StructInit",
        "ArrayLiteral",
        "TypeCast",
    }
)

_EXTERN_CALLS = frozenset(
    {
        "malloc",
        "free",
        "calloc",
        "realloc",
        "fopen",
        "fread",
        "fwrite",
        "fclose",
        "strlen",
        "strcpy",
        "strcmp",
    }
)


def _check_node(n: ASTNode, func_names: Set[str]) -> None:
    t = type(n).__name__
    if t in _UNSUPPORTED_TYPES:
        raise AsmOracleUnsupported(f"不支持 {t}", n)
    if isinstance(n, Call):
        if n.name not in func_names and n.name not in _EXTERN_CALLS:
            raise AsmOracleUnsupported(f"仅允许调用本程序内函数: {n.name}", n)
        for a in n.args:
            _check_node(a, func_names)
        return
    if isinstance(n, BinaryOp):
        _check_node(n.left, func_names)
        _check_node(n.right, func_names)
    elif isinstance(n, UnaryOp):
        _check_node(n.operand, func_names)
    elif isinstance(n, VarDecl):
        if n.value:
            _check_node(n.value, func_names)
    elif isinstance(n, ReturnStmt):
        if n.value:
            _check_node(n.value, func_names)
    elif isinstance(n, IfStmt):
        _check_node(n.condition, func_names)
        for s in n.then_body:
            _check_node(s, func_names)
        if n.else_body:
            for s in n.else_body:
                _check_node(s, func_names)
        if n.else_if:
            _check_node(n.else_if, func_names)
    elif isinstance(n, WhileStmt):
        _check_node(n.condition, func_names)
        for s in n.body:
            _check_node(s, func_names)
    elif isinstance(n, ForStmt):
        if n.init:
            _check_node(n.init, func_names)
        if n.condition:
            _check_node(n.condition, func_names)
        if n.update:
            _check_node(n.update, func_names)
        for s in n.body:
            _check_node(s, func_names)


def verify_asm_subset(program: Program) -> None:
    funcs = {n.name for n in program.body if isinstance(n, FuncDef)}
    funcs.add("main")
    for node in program.body:
        if isinstance(node, FuncDef):
            for s in node.body:
                _check_node(s, funcs)
        else:
            _check_node(node, funcs)


@dataclass
class _FuncCtx:
    name: str
    slots: Dict[str, int]
    frame_size: int
    label_counter: int = 0
    loop_break: List[str] = field(default_factory=list)
    loop_continue: List[str] = field(default_factory=list)

    def fresh_label(self, prefix: str = "L") -> str:
        self.label_counter += 1
        return f".{prefix}_{self.name}_{self.label_counter}"


def _walk_var_decls_if(st: IfStmt, slots: Dict[str, int], off: int) -> int:
    off = _walk_var_decls(st.then_body, slots, off)
    if st.else_body is not None:
        off = _walk_var_decls(st.else_body, slots, off)
    elif st.else_if is not None:
        off = _walk_var_decls_if(st.else_if, slots, off)
    return off


def _walk_var_decls(stmts: List[ASTNode], slots: Dict[str, int], off: int) -> int:
    """递归收集块内所有变量名（含 if/while/for 内），单槽复用同名 XC 变量。"""
    for st in stmts:
        if isinstance(st, VarDecl):
            if st.name not in slots:
                slots[st.name] = off
                off += 8
        elif isinstance(st, IfStmt):
            off = _walk_var_decls_if(st, slots, off)
        elif isinstance(st, WhileStmt):
            off = _walk_var_decls(st.body, slots, off)
        elif isinstance(st, ForStmt):
            if st.init and isinstance(st.init, VarDecl):
                if st.init.name not in slots:
                    slots[st.init.name] = off
                    off += 8
            off = _walk_var_decls(st.body, slots, off)
    return off


def _collect_slots_func(fd: FuncDef) -> Dict[str, int]:
    slots: Dict[str, int] = {}
    off = 0
    for pname, _ in fd.params:
        slots[pname] = off
        off += 8
    _walk_var_decls(fd.body, slots, off)
    return slots


def _collect_slots_main(stmts: List[ASTNode]) -> Dict[str, int]:
    slots: Dict[str, int] = {}
    _walk_var_decls(stmts, slots, 0)
    return slots


class RISCV64AsmOracle:
    """生成带 .globl main 的 RV64 汇编；参数 a0–a7，返回 a0。"""

    def __init__(self, program: Program):
        self.program = program
        self.lines: List[str] = []

    def emit(self) -> str:
        verify_asm_subset(self.program)
        self.lines = [
            "\t.file\t\"xc_oracle.s\"",
            "\t.text",
        ]
        main_stmts: List[ASTNode] = []
        for node in self.program.body:
            if isinstance(node, FuncDef):
                if node.name == "main":
                    raise AsmOracleUnsupported("勿定义 % main；入口用 # { }")
                self._emit_function(node)
            else:
                main_stmts.append(node)
        self._emit_main(main_stmts)
        return "\n".join(self.lines) + "\n"

    def _compute_frame_size(self, ctx: _FuncCtx) -> int:
        n = len(ctx.slots)
        base = 16 + n * 8 + 128
        return (base + 15) // 16 * 16

    def _emit_main(self, stmts: List[ASTNode]) -> None:
        fd = FuncDef(name="main", params=[], return_type="int", body=stmts)
        slots = _collect_slots_main(stmts)
        ctx = _FuncCtx("main", slots, 0)
        ctx.frame_size = self._compute_frame_size(ctx)
        self.lines.append("\t.globl\tmain")
        self.lines.append("\t.type\tmain, @function")
        self._emit_func_body(fd, ctx, default_return_zero=True)
        self.lines.append("\t.size\tmain, .-main")

    def _emit_function(self, fd: FuncDef) -> None:
        slots = _collect_slots_func(fd)
        ctx = _FuncCtx(fd.name, slots, 0)
        ctx.frame_size = self._compute_frame_size(ctx)
        self.lines.append(f"\t.globl\t{fd.name}")
        self.lines.append(f"\t.type\t{fd.name}, @function")
        self._emit_func_body(fd, ctx, default_return_zero=True)
        self.lines.append(f"\t.size\t{fd.name}, .-{fd.name}")

    def _emit_func_body(self, fd: FuncDef, ctx: _FuncCtx, default_return_zero: bool) -> None:
        fsz = ctx.frame_size
        exit_lbl = f".L_exit_{fd.name}"
        self.lines.append(f"{fd.name}:")
        self.lines.append(f"\taddi\tsp, sp, -{fsz}")
        self.lines.append(f"\tsd\tra, {fsz - 8}(sp)")
        self.lines.append(f"\tsd\ts0, {fsz - 16}(sp)")
        self.lines.append("\tmv\ts0, sp")
        regs = ["a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"]
        for i, (pname, _) in enumerate(fd.params):
            if i < len(regs):
                off = ctx.slots[pname]
                self.lines.append(f"\tsw\t{regs[i]}, {off}(s0)")
        scratch_base = max((max(ctx.slots.values()) if ctx.slots else -8) + 8, 0)

        for st in fd.body:
            self._emit_stmt(st, ctx, scratch_base, exit_lbl)

        if default_return_zero:
            self.lines.append("\tli\ta0, 0")
        self.lines.append(f"{exit_lbl}:")
        self.lines.append("\tmv\tsp, s0")
        self.lines.append(f"\tld\ts0, {fsz - 16}(sp)")
        self.lines.append(f"\tld\tra, {fsz - 8}(sp)")
        self.lines.append(f"\taddi\tsp, sp, {fsz}")
        self.lines.append("\tret")

    def _emit_stmt(
        self,
        st: ASTNode,
        ctx: _FuncCtx,
        scratch_base: int,
        exit_lbl: str,
    ) -> None:
        if isinstance(st, VarDecl):
            if st.value:
                self._emit_expr(st.value, ctx, scratch_base, "a0")
                off = ctx.slots[st.name]
                self.lines.append(f"\tsw\ta0, {off}(s0)")
            else:
                off = ctx.slots[st.name]
                self.lines.append(f"\tsw\tzero, {off}(s0)")
        elif isinstance(st, ReturnStmt):
            if st.value:
                self._emit_expr(st.value, ctx, scratch_base, "a0")
            else:
                self.lines.append("\tli\ta0, 0")
            self.lines.append(f"\tj\t{exit_lbl}")
        elif isinstance(st, IfStmt):
            self._emit_if(st, ctx, scratch_base, exit_lbl)
        elif isinstance(st, WhileStmt):
            self._emit_while(st, ctx, scratch_base, exit_lbl)
        elif isinstance(st, ForStmt):
            self._emit_for(st, ctx, scratch_base, exit_lbl)
        elif isinstance(st, BreakStmt):
            if not ctx.loop_break:
                raise AsmOracleUnsupported("break 不在循环内", st)
            self.lines.append(f"\tj\t{ctx.loop_break[-1]}")
        elif isinstance(st, ContinueStmt):
            if not ctx.loop_continue:
                raise AsmOracleUnsupported("continue 不在循环内", st)
            self.lines.append(f"\tj\t{ctx.loop_continue[-1]}")
        elif isinstance(st, Call):
            self._emit_call(st, ctx, scratch_base, "a0")
        else:
            raise AsmOracleUnsupported(f"语句未实现: {type(st).__name__}", st)

    def _emit_if(
        self,
        st: IfStmt,
        ctx: _FuncCtx,
        scratch_base: int,
        exit_lbl: str,
    ) -> None:
        le = ctx.fresh_label("else")
        lend = ctx.fresh_label("endif")
        self._emit_expr(st.condition, ctx, scratch_base, "a0")
        self.lines.append(f"\tbeqz\ta0, {le}")
        for s in st.then_body:
            self._emit_stmt(s, ctx, scratch_base, exit_lbl)
        skip_then_j = st.then_body and isinstance(st.then_body[-1], ReturnStmt)
        if not skip_then_j:
            self.lines.append(f"\tj\t{lend}")
        self.lines.append(f"{le}:")
        if st.else_body:
            for s in st.else_body:
                self._emit_stmt(s, ctx, scratch_base, exit_lbl)
        elif st.else_if:
            self._emit_if(st.else_if, ctx, scratch_base, exit_lbl)
        self.lines.append(f"{lend}:")

    def _emit_while(
        self,
        st: WhileStmt,
        ctx: _FuncCtx,
        scratch_base: int,
        exit_lbl: str,
    ) -> None:
        lb = ctx.fresh_label("w_beg")
        le = ctx.fresh_label("w_end")
        ctx.loop_continue.append(lb)
        ctx.loop_break.append(le)
        self.lines.append(f"{lb}:")
        self._emit_expr(st.condition, ctx, scratch_base, "a0")
        self.lines.append(f"\tbeqz\ta0, {le}")
        for s in st.body:
            self._emit_stmt(s, ctx, scratch_base, exit_lbl)
        self.lines.append(f"\tj\t{lb}")
        self.lines.append(f"{le}:")
        ctx.loop_continue.pop()
        ctx.loop_break.pop()

    def _emit_for(
        self,
        st: ForStmt,
        ctx: _FuncCtx,
        scratch_base: int,
        exit_lbl: str,
    ) -> None:
        if st.init:
            if isinstance(st.init, VarDecl):
                self._emit_stmt(st.init, ctx, scratch_base, exit_lbl)
            else:
                raise AsmOracleUnsupported("for 初始化仅支持 $ 变量声明", st)
        lb = ctx.fresh_label("f_beg")
        le = ctx.fresh_label("f_end")
        ctx.loop_continue.append(lb)
        ctx.loop_break.append(le)
        self.lines.append(f"{lb}:")
        if st.condition:
            self._emit_expr(st.condition, ctx, scratch_base, "a0")
            self.lines.append(f"\tbeqz\ta0, {le}")
        for s in st.body:
            self._emit_stmt(s, ctx, scratch_base, exit_lbl)
        if st.update:
            self._emit_for_update(st.update, ctx, scratch_base)
        self.lines.append(f"\tj\t{lb}")
        self.lines.append(f"{le}:")
        ctx.loop_continue.pop()
        ctx.loop_break.pop()

    def _emit_for_update(self, up: ASTNode, ctx: _FuncCtx, scratch_base: int) -> None:
        if isinstance(up, UnaryOp) and up.op == "++post" and isinstance(up.operand, Identifier):
            off = ctx.slots[up.operand.name]
            self.lines.append(f"\tlw\ta0, {off}(s0)")
            self.lines.append("\taddiw\ta0, a0, 1")
            self.lines.append(f"\tsw\ta0, {off}(s0)")
        elif isinstance(up, UnaryOp) and up.op == "--post" and isinstance(up.operand, Identifier):
            off = ctx.slots[up.operand.name]
            self.lines.append(f"\tlw\ta0, {off}(s0)")
            self.lines.append("\taddiw\ta0, a0, -1")
            self.lines.append(f"\tsw\ta0, {off}(s0)")
        elif isinstance(up, VarDecl) and up.value:
            self._emit_expr(up.value, ctx, scratch_base, "a0")
            off = ctx.slots[up.name]
            self.lines.append(f"\tsw\ta0, {off}(s0)")
        else:
            raise AsmOracleUnsupported("for 步进仅支持 i++/i-- 或带值的 $ 声明", up)

    def _emit_call(self, c: Call, ctx: _FuncCtx, scratch_base: int, result_reg: str) -> None:
        regs = ["a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"]
        for i, arg in enumerate(c.args):
            if i >= len(regs):
                raise AsmOracleUnsupported("最多 8 个参数", c)
            self._emit_expr(arg, ctx, scratch_base, regs[i])
        self.lines.append(f"\tcall\t{c.name}")
        if result_reg != "a0":
            self.lines.append(f"\tmv\t{result_reg}, a0")

    def _emit_expr(
        self,
        node: ASTNode,
        ctx: _FuncCtx,
        scratch_base: int,
        target: str,
    ) -> None:
        if isinstance(node, NumberLiteral):
            self.lines.append(f"\tli\t{target}, {int(node.value)}")
        elif isinstance(node, BoolLiteral):
            self.lines.append(f"\tli\t{target}, {1 if node.value else 0}")
        elif isinstance(node, Identifier):
            off = ctx.slots[node.name]
            self.lines.append(f"\tlw\t{target}, {off}(s0)")
        elif isinstance(node, UnaryOp):
            self._emit_unary(node, ctx, scratch_base, target)
        elif isinstance(node, BinaryOp):
            self._emit_binary(node, ctx, scratch_base, target)
        elif isinstance(node, Call):
            self._emit_call(node, ctx, scratch_base, result_reg=target)
        else:
            raise AsmOracleUnsupported(f"表达式未实现: {type(node).__name__}", node)

    def _emit_unary(
        self,
        node: UnaryOp,
        ctx: _FuncCtx,
        scratch_base: int,
        target: str,
    ) -> None:
        self._emit_expr(node.operand, ctx, scratch_base, target)
        if node.op == "!":
            self.lines.append(f"\tseqz\t{target}, {target}")
        elif node.op == "-":
            self.lines.append(f"\tsubw\t{target}, zero, {target}")
        elif node.op == "~":
            self.lines.append(f"\txori\t{target}, {target}, -1")
        else:
            raise AsmOracleUnsupported(f"一元运算符 {node.op}", node)

    def _emit_binary(
        self,
        node: BinaryOp,
        ctx: _FuncCtx,
        scratch_base: int,
        target: str,
    ) -> None:
        # 用 sp 临时槽，保证嵌套二元表达式不互相覆盖（每处配对 addi）
        self._emit_expr(node.left, ctx, scratch_base, target)
        self.lines.append("\taddi\tsp, sp, -16")
        self.lines.append(f"\tsd\t{target}, 8(sp)")
        self._emit_expr(node.right, ctx, scratch_base, target)
        self.lines.append("\tld\tt0, 8(sp)")
        self.lines.append("\taddi\tsp, sp, 16")
        op = node.op
        if op == "+":
            self.lines.append(f"\taddw\t{target}, t0, {target}")
        elif op == "-":
            self.lines.append(f"\tsubw\t{target}, t0, {target}")
        elif op == "*":
            self.lines.append(f"\tmulw\t{target}, t0, {target}")
        elif op == "/":
            self.lines.append(f"\tdivw\t{target}, t0, {target}")
        elif op == "%":
            self.lines.append(f"\tremw\t{target}, t0, {target}")
        elif op == "==":
            self.lines.append(f"\tsubw\tt1, t0, {target}")
            self.lines.append(f"\tseqz\t{target}, t1")
        elif op == "!=":
            self.lines.append(f"\tsubw\tt1, t0, {target}")
            self.lines.append(f"\tsnez\t{target}, t1")
        elif op == "<":
            self.lines.append(f"\tslt\t{target}, t0, {target}")
        elif op == ">":
            self.lines.append(f"\tslt\t{target}, {target}, t0")
        elif op == "<=":
            self.lines.append(f"\tslt\tt1, {target}, t0")
            self.lines.append(f"\txori\t{target}, t1, 1")
        elif op == ">=":
            self.lines.append(f"\tslt\tt1, t0, {target}")
            self.lines.append(f"\txori\t{target}, t1, 1")
        elif op == "&&":
            self.lines.append(f"\tand\t{target}, t0, {target}")
            self.lines.append(f"\tsnez\t{target}, {target}")
        elif op == "||":
            self.lines.append(f"\tor\t{target}, t0, {target}")
            self.lines.append(f"\tsnez\t{target}, {target}")
        elif op == "&":
            self.lines.append(f"\tand\t{target}, t0, {target}")
        elif op == "|":
            self.lines.append(f"\tor\t{target}, t0, {target}")
        elif op == "^":
            self.lines.append(f"\txor\t{target}, t0, {target}")
        elif op == "<<":
            self.lines.append(f"\tsllw\t{target}, t0, {target}")
        elif op == ">>":
            self.lines.append(f"\tsraw\t{target}, t0, {target}")
        else:
            raise AsmOracleUnsupported(f"二元运算符 {op}", node)


def compile_xc_to_asm_riscv64(xc_source: str) -> str:
    ast = parse_xc_program(xc_source)
    return RISCV64AsmOracle(ast).emit()


def compile_xc_to_asm_riscv64_with_reason(xc_source: str) -> dict:
    """
    安全编译入口：返回 {"ok": bool, "asm": str|None, "unsupported_reason": str|None}
    供数据工厂记录失败原因，而不是直接丢样本。
    """
    try:
        asm = compile_xc_to_asm_riscv64(xc_source)
        return {"ok": True, "asm": asm, "unsupported_reason": None}
    except AsmOracleUnsupported as e:
        return {"ok": False, "asm": None, "unsupported_reason": str(e)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "asm": None, "unsupported_reason": f"internal:{type(e).__name__}:{e}"}
