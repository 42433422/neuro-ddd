"""
XC 语言 - 专属原创符号系统 V3

完全原创的符号语言，不参照任何现有编程语言

═══════════════════════════════════════════════════════════════════════════════
                            XC 语言符号对照表
═══════════════════════════════════════════════════════════════════════════════

【程序结构】
⌘Main          程序入口                    ⌘Main{ → }
⌬Return        返回值                      ⌬x+y
�打印机         打印输出                    �打印机"hello"
⌧扫描          输入                        ⌧x

【变量声明】
▽Var           声明变量                    ▽x=10
▽Con           声明常量                    ▽Con PI=3.14
▽Func          定义函数                    ▽Func add(a,b)⌬a+b
▽Struct        定义结构体                  ▽Struct Point{x,y}

【数据类型】
◈Int           整数类型                    ◈x
◊Float         浮点类型                    ◊x
◉Bool          布尔类型                    ◉flag
◆String        字符串类型                  ◆name
◇Array         数组类型                    ◇arr
▷Option        可选类型                    ▷value
◐Ptr           指针类型                    ◐ptr

【运算符】
⊕Add           加法                        x⊕y
⊖Sub           减法                        x⊖y
⊗Mul           乘法                        x⊗y
⊘Div           除法                        x⊘y
⊙Mod           取模                        x⊙y
≔Assign        赋值                        x≔10
⊕≔AddAssign   加法赋值                    x⊕≔1
⊖≔SubAssign   减法赋值                    x⊖≔1

【比较运算】
≡Equal        等于                        x≡y
≢NotEqual     不等于                      x≢y
⊳Greater       大于                        x⊳y
⊲Less         小于                        x⊲y
⊳≡GreaterEq   大于等于                    x⊳≡y
⊲≡LessEq      小于等于                    x⊲≡y

【逻辑运算】
∧And           逻辑与                      x∧y
∨Or            逻辑或                      x∨y
¬Not           逻辑非                      ¬x

【流程控制】
▷If            条件判断                    ▷x⊳0{ }
▷Else          否则                        ▷/{ }
▷Elif          否则如果                    ▷▷x≡0{ }
▷Switch        多分支                      ▷▶x{1:... 2:...}
⟲Loop          循环                        ⟲i∈[0,10]{ }
⟲While         当循环                      ⟲x⊳0{ }
⟲Do            做循环                      ⟲Do{ }▷x⊳0

【循环控制】
⏎Break         跳出循环                    ⏎
⏭Next          继续循环                    ⏭

【函数相关】
⌦Call          调用函数                    ⌦add(3,5)
⌫Arg           函数参数分隔                add⌫3⌫5

【内存管理】
◉Ref           引用                        ◉x
◐Deref         解引用                      ◐ptr
⊞Alloc         分配内存                    ⊞Alloc(10)
⊟Free          释放内存                    ⊟Free(ptr)

【错误处理】
⊜Try           尝试                        ⊜Try{ }
⊝Catch         捕获错误                    ⊝Catch e{ }
⊖Throw         抛出错误                    ⊖Throw"error"

【类型转换】
⊐Cast          类型转换                    ⊐Cast<Int>(x)
⊑SizeOf        获取大小                    ⊑SizeOf(Int)

【特殊值】
⌀Nil           空/无                      ⌀
✓True          真                         ✓
✗False         假                         ✗

【并发相关】
⚡Thread        线程                        ⚡Thread{ }
⚡Spawn         创建线程                    ⚡Spawn{ }
⏳Sleep         线程休眠                    ⏳Sleep(1000)
⚠Lock          锁                          ⚠Lock{ }
⚡Unlock        解锁                        ⚡Unlock

【其他】
░Import        导入模块                    ░Import"module"
▒Include       包含头文件                  ▒Include<stdio>
░Using         使用命名空间                ░Using"std"

═══════════════════════════════════════════════════════════════════════════════
                            XC 语言示例
═══════════════════════════════════════════════════════════════════════════════

// Hello World
⌘Main{�打印机"Hello World"}

// 两数相加函数
▽Func add(a◈Int,b◈Int)◈Int⌬a⊕b
⌘Main{�打印机⌦add(3,5)}

// 条件判断
⌘Main{▽x◈Int≔10▷x⊳5{�打印机"big"}▷Else{�打印机"small"}}

// for循环累加
⌘Main{▽sum◈Int≔0⟲i◈Int∈[1,101]{sum⊕≔i}�打印机sum}

// 阶乘函数
▽Func fac(n◈Int)◈Int⌬▷n⊲2{⌀1}n⊗⌦fac(n⊖1)
⌘Main{�打印机⌦fac(5)}

// 结构体
▽Struct Point{x◈Int,y◈Int}
⌘Main{▽p◐Point≔▯Point{1,2}�打印机p.x}

// 斐波那契
▽Func fib(n◈Int)◈Int⌬▷n≡0{⌀0}▷n≡1{⌀1}⌦fib(n⊖1)⊕⌦fib(n⊖2)
⌘Main{�打印机⌦fib(10)}

═══════════════════════════════════════════════════════════════════════════════
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class XToken:
    type: str
    value: str
    line: int
    column: int


class XSymbolLexer:
    """XC 语言词法分析器"""

    KEYWORDS = {
        "⌘Main": "main",
        "⌬Return": "return",
        "�打印机": "print",
        "⌧扫描": "input",
        "▽Var": "let",
        "▽Con": "const",
        "▽Func": "fn",
        "▽Struct": "struct",
        "◈Int": "i32",
        "◊Float": "f64",
        "◉Bool": "bool",
        "◆String": "String",
        "◇Array": "Vec",
        "▷Option": "Option",
        "◐Ptr": "ptr",
        "▷If": "if",
        "▷Else": "else",
        "▷Elif": "elif",
        "⟲Loop": "for",
        "⟲While": "while",
        "⟲Do": "loop",
        "⏎Break": "break",
        "⏭Next": "continue",
        "⌦Call": "call",
        "⌀Nil": "nil",
        "✓True": "true",
        "✗False": "false",
        "▯New": "new",
        "◉Ref": "ref",
        "⊞Alloc": "alloc",
        "⊟Free": "free",
        "⊜Try": "try",
        "⊝Catch": "catch",
        "⊖Throw": "throw",
        "⊐Cast": "cast",
        "⊑SizeOf": "sizeof",
        "⚡Thread": "thread",
        "⚡Spawn": "spawn",
        "⏳Sleep": "sleep",
        "⚠Lock": "lock",
    }

    TOKEN_PATTERNS = [
        ("KEYWORD", r"(?:⌘Main|⌬Return|�打印机|⌧扫描|▽Var|▽Con|▽Func|▽Struct|◈Int|◊Float|◉Bool|◆String|◇Array|▷Option|◐Ptr|▷If|▷Else|▷Elif|⟲Loop|⟲While|⟲Do|⏎Break|⏭Next|⌦Call|⌀Nil|✓True|✗False|▯New|◉Ref|⊞Alloc|⊟Free|⊜Try|⊝Catch|⊖Throw|⊐Cast|⊑SizeOf|⚡Thread|⚡Spawn|⏳Sleep|⚠Lock|⚡Unlock|░Import|▒Include|░Using)"),
        ("OPERATOR", r"(?:≡|≢|⊳|⊲|⊳≡|⊲≡|⊕|⊖|⊗|⊘|⊙|≔|⊕≔|⊖≔|∧|∨|¬|∈|∉|→|→\*|\+\+|--|&&|\|\||->|::)"),
        ("PUNCTUATION", r"[{}()\[\];,:.]"),
        ("IDENT", r"[a-zA-Z_\u4e00-\u9fff]\w*"),
        ("NUMBER", r"\d+\.?\d*"),
        ("STRING", r'"[^"]*"'),
        ("NEWLINE", r"\n"),
        ("WHITESPACE", r"[ \t]+"),
        ("COMMENT", r"//.*|/\*[\s\S]*?\*/"),
    ]

    def __init__(self, code: str):
        self.code = code
        self.tokens = []
        self.errors = []
        self.line = 1
        self.pos = 0

    def tokenize(self) -> List[XToken]:
        """分词"""
        while self.pos < len(self.code):
            matched = False

            for token_type, pattern in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(self.code, self.pos)
                if match:
                    value = match.group()

                    if token_type not in ("WHITESPACE", "NEWLINE", "COMMENT"):
                        self.tokens.append(XToken(token_type, value, self.line, self.pos))

                    if "\n" in value:
                        self.line += value.count("\n")

                    self.pos = match.end()
                    matched = True
                    break

            if not matched:
                self.errors.append(f"未知字符 at line {self.line}: '{self.code[self.pos]}'")
                self.pos += 1

        return self.tokens


class XCompilerV3:
    """XC 语言编译器 V3 - 完全原创"""

    def __init__(self, target: str = "rust"):
        self.target = target

    def compile(self, x_code: str) -> str:
        """编译 XC 代码"""
        lexer = XSymbolLexer(x_code)
        tokens = lexer.tokenize()

        if lexer.errors:
            print(f"词法错误: {lexer.errors}")

        if self.target == "rust":
            return self.to_rust(tokens)
        elif self.target == "c":
            return self.to_c(tokens)
        elif self.target == "mojo":
            return self.to_mojo(tokens)
        return ""

    def to_rust(self, tokens: List[XToken]) -> str:
        """转换为 Rust"""
        lines = ["fn main() {"]

        i = 0
        while i < len(tokens):
            token = tokens[i]
            value = token.value

            if value == "⌘Main":
                i += 1
                if i < len(tokens) and tokens[i].value == "{":
                    i += 1

            elif value == "▽Func":
                func_def, i = self.parse_function(tokens, i)
                lines.append("    " + func_def)

            elif value == "▽Var":
                var_line, i = self.parse_var(tokens, i)
                lines.append("    " + var_line)

            elif value == "⌦Call" or value == "�打印机":
                call_line, i = self.parse_call_or_print(tokens, i, value == "�打印机")
                if value == "�打印机":
                    lines.append("    println!(\"{}\", " + call_line + ");")
                else:
                    lines.append("    " + call_line + ";")

            elif value == "▷If":
                if_line, i = self.parse_if(tokens, i)
                lines.append("    " + if_line)

            elif value == "⟲Loop":
                loop_line, i = self.parse_loop(tokens, i)
                lines.append("    " + loop_line)

            elif value == "▽Struct":
                struct_def, i = self.parse_struct(tokens, i)
                lines.append(struct_def)

            else:
                i += 1

        lines.append("}")
        return "\n".join(lines)

    def to_c(self, tokens: List[XToken]) -> str:
        """转换为 C"""
        lines = ['#include <stdio.h>', '', 'int main() {']

        i = 0
        while i < len(tokens):
            token = tokens[i]
            value = token.value

            if value == "⌘Main":
                i += 1
                if i < len(tokens) and tokens[i].value == "{":
                    i += 1

            elif value == "▽Func":
                func_def, i = self.parse_function(tokens, i, "c")
                lines.append(func_def)

            elif value == "▽Var":
                var_line, i = self.parse_var(tokens, i, "c")
                lines.append("    " + var_line)

            elif value == "⌦Call" or value == "�打印机":
                call_line, i = self.parse_call_or_print(tokens, i, value == "�打印机", "c")
                if value == "�打印机":
                    lines.append('    printf("%d\\n", ' + call_line + ');')
                else:
                    lines.append("    " + call_line + ";")

            elif value == "▷If":
                if_line, i = self.parse_if(tokens, i, "c")
                lines.append("    " + if_line)

            elif value == "⟲Loop":
                loop_line, i = self.parse_loop(tokens, i, "c")
                lines.append("    " + loop_line)

            else:
                i += 1

        lines.append("    return 0;")
        lines.append("}")
        return "\n".join(lines)

    def to_mojo(self, tokens: List[XToken]) -> str:
        """转换为 Mojo"""
        lines = ["fn main():"]

        i = 0
        while i < len(tokens):
            token = tokens[i]
            value = token.value

            if value == "⌘Main":
                i += 1
                if i < len(tokens) and tokens[i].value == "{":
                    i += 1

            elif value == "▽Func":
                func_def, i = self.parse_function(tokens, i, "mojo")
                lines.append("    " + func_def)

            elif value == "▽Var":
                var_line, i = self.parse_var(tokens, i, "mojo")
                lines.append("    " + var_line)

            elif value == "⌦Call" or value == "�打印机":
                call_line, i = self.parse_call_or_print(tokens, i, value == "�打印机", "mojo")
                if value == "�打印机":
                    lines.append("    print(" + call_line + ")")
                else:
                    lines.append("    " + call_line)

            elif value == "▷If":
                if_line, i = self.parse_if(tokens, i, "mojo")
                lines.append("    " + if_line)

            elif value == "⟲Loop":
                loop_line, i = self.parse_loop(tokens, i, "mojo")
                lines.append("    " + loop_line)

            else:
                i += 1

        return "\n".join(lines)

    def parse_function(self, tokens: List[XToken], start: int, lang: str = "rust") -> Tuple[str, int]:
        """解析函数"""
        i = start + 1
        name = ""

        if i < len(tokens) and tokens[i].type == "IDENT":
            name = tokens[i].value
            i += 1

        params = []
        if i < len(tokens) and tokens[i].value == "(":
            i += 1
            while i < len(tokens) and tokens[i].value != ")":
                if tokens[i].type == "IDENT":
                    param_name = tokens[i].value
                    i += 1
                    param_type = "i32"
                    if i < len(tokens) and tokens[i].value == "◈Int":
                        param_type = "i32"
                        i += 1
                    params.append(f"{param_name}: {param_type}")
                i += 1
            if i < len(tokens) and tokens[i].value == ")":
                i += 1

        ret_type = ""
        if i < len(tokens) and tokens[i].type == "KEYWORD":
            type_kw = tokens[i].value
            type_map = {"◈Int": "i32", "◊Float": "f64", "◉Bool": "bool", "◆String": "String"}
            ret_type = type_map.get(type_kw, "i32")
            i += 1

        body_expr = ""
        if i < len(tokens) and tokens[i].value == "⌬Return":
            i += 1
            body_expr = self.expr_to_str(tokens, i, lang)

        if lang == "rust":
            type_str = f" -> {ret_type}" if ret_type else ""
            lines = [f"fn {name}({', '.join(params)}){type_str} {{"]
            if body_expr:
                lines.append(f"    {body_expr}")
            lines.append("}")
            return "\n    ".join(lines), i
        elif lang == "c":
            type_str = ret_type if ret_type else "void"
            lines = [f"{type_str} {name}({', '.join(params)}) {{"]
            if body_expr:
                lines.append(f"    return {body_expr};")
            lines.append("}")
            return "\n".join(lines), i
        else:
            type_str = f" -> {ret_type}" if ret_type else ""
            lines = [f"fn {name}({', '.join(params)}){type_str}:"]
            if body_expr:
                lines.append(f"    return {body_expr}")
            return "\n    ".join(lines), i

    def parse_var(self, tokens: List[XToken], start: int, lang: str = "rust") -> Tuple[str, int]:
        """解析变量"""
        i = start + 1
        name = ""

        if i < len(tokens) and tokens[i].type == "IDENT":
            name = tokens[i].value
            i += 1

        var_type = "i32"
        if i < len(tokens) and tokens[i].type == "KEYWORD":
            type_kw = tokens[i].value
            type_map = {"◈Int": "i32", "◊Float": "f64", "◉Bool": "bool", "◆String": "String"}
            var_type = type_map.get(type_kw, "i32")
            i += 1

        value = ""
        if i < len(tokens) and tokens[i].value == "≔":
            i += 1
            value = self.expr_to_str(tokens, i, lang)

        if lang == "rust":
            return f"let {name}: {var_type} = {value};", i
        elif lang == "c":
            return f"{var_type} {name} = {value};", i
        else:
            return f"var {name}: {var_type} = {value}", i

    def parse_call_or_print(self, tokens: List[XToken], start: int, is_print: bool, lang: str = "rust") -> Tuple[str, int]:
        """解析函数调用或打印"""
        i = start + 1
        name = ""

        if i < len(tokens) and tokens[i].type == "IDENT":
            name = tokens[i].value
            i += 1

        args = []
        if i < len(tokens) and tokens[i].value == "(":
            i += 1
            while i < len(tokens) and tokens[i].value != ")":
                if tokens[i].type in ("IDENT", "NUMBER", "STRING"):
                    args.append(tokens[i].value)
                i += 1
            if i < len(tokens) and tokens[i].value == ")":
                i += 1

        return f"{name}({', '.join(args)})", i

    def parse_if(self, tokens: List[XToken], start: int, lang: str = "rust") -> Tuple[str, int]:
        """解析 if 语句"""
        i = start + 1
        condition = self.expr_to_str(tokens, i, lang)

        body = ""
        if i < len(tokens) and tokens[i].value == "{":
            i += 1
            brace_count = 1
            stmt_tokens = []
            while i < len(tokens) and brace_count > 0:
                if tokens[i].value == "{":
                    brace_count += 1
                elif tokens[i].value == "}":
                    brace_count -= 1
                if brace_count > 0:
                    stmt_tokens.append(tokens[i])
                i += 1

            if lang == "rust":
                body = "if " + condition + " { }"
            elif lang == "c":
                body = "if (" + condition + ") { }"
            else:
                body = "if " + condition + ": pass"

        return body, i

    def parse_loop(self, tokens: List[XToken], start: int, lang: str = "rust") -> Tuple[str, int]:
        """解析循环"""
        i = start + 1

        var = ""
        if i < len(tokens) and tokens[i].type == "IDENT":
            var = tokens[i].value
            i += 1

        start_val = ""
        end_val = ""
        if i < len(tokens) and tokens[i].value == "∈":
            i += 1
            if i < len(tokens) and tokens[i].type == "NUMBER":
                start_val = tokens[i].value
                i += 1
            if i < len(tokens) and tokens[i].value == ",":
                i += 1
            if i < len(tokens) and tokens[i].type == "NUMBER":
                end_val = tokens[i].value
                i += 1

        if lang == "rust":
            return f"for {var} in {start_val}..={end_val} {{ }}", i
        elif lang == "c":
            return f"for (int {var} = {start_val}; {var} <= {end_val}; {var}++) {{ }}", i
        else:
            return f"for {var} in range({start_val}, {end_val}+1): pass", i

    def parse_struct(self, tokens: List[XToken], start: int) -> Tuple[str, int]:
        """解析结构体"""
        i = start + 1
        name = ""

        if i < len(tokens) and tokens[i].type == "IDENT":
            name = tokens[i].value
            i += 1

        fields = []
        if i < len(tokens) and tokens[i].value == "{":
            i += 1
            while i < len(tokens) and tokens[i].value != "}":
                if tokens[i].type == "IDENT":
                    field_name = tokens[i].value
                    i += 1
                    field_type = "i32"
                    if i < len(tokens) and tokens[i].type == "KEYWORD":
                        type_kw = tokens[i].value
                        type_map = {"◈Int": "i32", "◊Float": "f64", "◉Bool": "bool", "◆String": "String"}
                        field_type = type_map.get(type_kw, "i32")
                        i += 1
                    fields.append(f"{field_name}: {field_type}")
                i += 1
            if i < len(tokens) and tokens[i].value == "}":
                i += 1

        return f"struct {name} {{ {', '.join(fields)} }}", i

    def expr_to_str(self, tokens: List[XToken], start: int, lang: str) -> str:
        """表达式转字符串"""
        parts = []
        i = start
        while i < len(tokens):
            token = tokens[i]
            if token.value in "{}()[];,":
                break

            op_map = {
                "⊕": "+", "⊖": "-", "⊗": "*", "⊘": "/", "⊙": "%",
                "≡": "==", "≢": "!=", "⊳": ">", "⊲": "<", "⊳≡": ">=", "⊲≡": "<=",
                "∧": "&&", "∨": "||", "¬": "!",
            }

            if token.value in op_map:
                parts.append(op_map[token.value])
            elif token.type in ("IDENT", "NUMBER", "STRING"):
                parts.append(token.value)
            elif token.type == "KEYWORD":
                type_map = {"◈Int": "i32", "◊Float": "f64", "◉Bool": "bool", "◆String": "String"}
                mapped = type_map.get(token.value, token.value)
                parts.append(mapped)

            i += 1

        return " ".join(parts)


SAMPLE_X_V3 = """⌘Main{�打印机"Hello World"}"""


def demo():
    """演示"""
    print("=" * 60)
    print("XC 语言 V3 (完全原创符号) 编译器演示")
    print("=" * 60)

    print("\n原始 XC 代码 (原创符号):")
    print(SAMPLE_X_V3)

    compiler = XCompilerV3("rust")
    print("\n编译为 Rust:")
    print(compiler.compile(SAMPLE_X_V3))

    compiler = XCompilerV3("c")
    print("\n编译为 C:")
    print(compiler.compile(SAMPLE_X_V3))

    compiler = XCompilerV3("mojo")
    print("\n编译为 Mojo:")
    print(compiler.compile(SAMPLE_X_V3))

    print("\n" + "=" * 60)
    print("更多示例:")
    print("=" * 60)

    more_samples = [
        '⌘Main{▽Func add(a◈Int,b◈Int)◈Int⌬a⊕b⌦add(3,5)}',
        '⌘Main{▽x◈Int≔10▷x⊳5{�打印机"big"}▷Else{�打印机"small"}}',
    ]

    for sample in more_samples:
        print(f"\nX: {sample}")
        compiler = XCompilerV3("rust")
        print(f"Rust: {compiler.compile(sample)}")


if __name__ == "__main__":
    demo()
