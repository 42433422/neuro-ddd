"""
XC 语言 - 纯符号化语法规范 V2

设计原则: 全部使用符号,只有符号不够用时才用英文

═══════════════════════════════════════════════════════════════════════════════
X 符号                    对应含义                    示例
═══════════════════════════════════════════════════════════════════════════════

▶ MAIN                  程序入口                     ▶MAIN{ }
◀ RET                   返回                         ◀x+1
◎ PRINT                 输出打印                     ◎x
◎> PRINTLN              换行打印                     ◎>"hello"
◎< SCANF/INPUT          输入                         ◎<x
? IF                    条件判断                     ?x>0{ }
?/ ELSE                 否则                         ?/ { }
?▶ SWITCH               多分支                       ?▶x{1:... 2:...}
▶ LOOP                  循环                         ▶i∈[0,10]{ }

◈ VAR                   变量声明                     ◈x=10
◈C CONST                常量                         ◈C PI=3.14
◈F FUNC                 函数定义                     ◈F add(a,b)◀a+b
◈S STRUCT               结构体                       ◈S Point{x,y}

∈ TYPE_INT              整数类型                     ⊂x∈Int
∉ TYPE_FLOAT            浮点类型                     ⊂x∉Float
∈b TYPE_BOOL            布尔类型                     ⊂x∈b
∈s TYPE_STRING          字符串                       ⊂x∈s
∈a TYPE_ARRAY           数组类型                     ⊂x∈a[Int]
∈o TYPE_OPTION          可选类型                     ⊂x∈o[Int]

+ ADD                   加法                         x+y
- SUB                   减法                         x-y
* MUL                   乘法                         x*y
/ DIV                   除法                         x/y
% MOD                   取模                         x%y
= ASSIGN                赋值                         x=10
+= ADD_ASSIGN           加法赋值                     x+=1
-= SUB_ASSIGN           减法赋值                     x-=1

== EQ                   等于                         x==y
!= NEQ                  不等于                       x!=y
>  GT                   大于                         x>y
<  LT                   小于                         x<y
>= GTE                  大于等于                      x>=y
<= LTE                  小于等于                      x<=y

&& AND                  逻辑与                       x&&y
|| OR                   逻辑或                       x||y
!  NOT                  逻辑非                       !x

&  REF                  引用/指针                     &x
*  DEREF                解引用                       *ptr
→  ARROW                返回/指向                     fn→Int
→* PTR_ARROW           指针指向                      obj→field

( ) PAREN               括号                         f(a,b)
{ } BRACE               代码块                       {a;b;c}
[ ] BRACKET             数组索引                     arr[0]
;  SEMI                 语句分隔                     a;b;c
,  COMMA                参数分隔                     f(a,b)

∈ IN                    属于(循环)                   i∈[0,10]
∉ NOT_IN                不属于
∅  NULL                 空值                         ∅
√  TRUE                 真                          √
×  FALSE                假                          ×

@  ATTR                 属性                         @safe
#  MACRO                宏定义                       #DEFINE
$  INCLUDE              包含                         $"stdio.h"
%  MODULE               模块                         %io

▲ THREAD                线程                         ▲spawn{ }
▼ ASYNC                 异步                         ▼async{ }
★ LOCK                  锁                           ★mutex{ }
☆ UNLOCK                解锁                         ☆mutex{ }

∑ ITERATE               迭代器                       ∑i∈arr{print i}
∏ REDUCE                累计                         ∏acc,i{acc+i}
√ SOME                  Some值                       √Some
× NONE                  None值                       ×None
∞ ERROR                 错误                         ∞Err
∞? CHECK                错误检查                      ∞?result

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


class XSymbolTable:
    """XC 语言符号表"""

    KEYWORDS = {
        "▶MAIN": "main",
        "◀RET": "return",
        "◎": "print",
        "◎>": "println",
        "◎<": "input",
        "?": "if",
        "?/": "else",
        "?▶": "switch",
        "▶LOOP": "for",
        "▶WHILE": "while",
        "◈": "let",
        "◈C": "const",
        "◈F": "fn",
        "◈S": "struct",
        "∈": "i32",
        "∉": "f64",
        "∈b": "bool",
        "∈s": "String",
        "∈a": "array",
        "∈o": "Option",
        "+": "add",
        "-": "sub",
        "*": "mul",
        "/": "div",
        "%": "mod",
        "==": "eq",
        "!=": "neq",
        "&&": "and",
        "||": "or",
        "!": "not",
        "&": "ref",
        "*": "deref",
        "→": "arrow",
        "∈": "in",
        "∉": "notin",
        "∅": "null",
        "√": "true",
        "×": "false",
        "@": "attr",
        "#": "macro",
        "$": "include",
        "%": "module",
        "▲": "thread",
        "▼": "async",
        "★": "lock",
        "☆": "unlock",
        "∑": "iter",
        "∏": "reduce",
        "∞": "error",
        "∞?": "try",
    }

    TYPE_KEYWORDS = {
        "Int": "i32",
        "Float": "f64",
        "Bool": "bool",
        "String": "String",
        "Array": "Vec",
        "Option": "Option",
    }


class XLexerV2:
    """XC 语言纯符号词法分析器"""

    TOKEN_PATTERNS = [
        ("KEYWORD", r"(?:▶MAIN|◀RET|◎|◎>|◎<|\?\/|\?▶|▶LOOP|▶WHILE|◈|◈C|◈F|◈S|∈|∉|∈b|∈s|∈a|∈o|∅|√|×|@|#|\$|%|▲|▼|★|☆|∑|∏|∞|∞\?)"),
        ("OPERATOR", r"(?:==|!=|<=|>=|&&|\|\||->|→|&&|\+=|-=|\+|-|\*|/|%|=|&|\*|!|<|>)"),
        ("LPAREN", r"\(."),
        ("RPAREN", r"\)"),
        ("LBRACE", r"\{"),
        ("RBRACE", r"\}"),
        ("LBRACKET", r"\["),
        ("RBRACKET", r"\]"),
        ("NUMBER", r"\d+\.?\d*"),
        ("STRING", r'"[^"]*"'),
        ("IDENT", r"[a-zA-Z_]\w*"),
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


class XCompilerV2:
    """XC 语言编译器 V2"""

    def __init__(self, target: str = "rust"):
        self.target = target
        self.keywords = XSymbolTable.KEYWORDS

    def compile(self, x_code: str) -> str:
        """编译 XC 代码"""
        lexer = XLexerV2(x_code)
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

            if token.value == "◈F":
                func_lines, i = self.parse_function(tokens, i, "rust")
                lines.extend(func_lines)
            elif token.value == "◈":
                var_line, i = self.parse_variable(tokens, i, "rust")
                lines.append(var_line)
            elif token.value == "◎>":
                print_line, i = self.parse_print(tokens, i, "rust")
                lines.append(print_line)
            elif token.value == "▶MAIN":
                i += 1
                if i < len(tokens) and tokens[i].value == "{":
                    i += 1

            i += 1

        lines.append("}")
        return "\n".join(lines)

    def to_c(self, tokens: List[XToken]) -> str:
        """转换为 C"""
        lines = ['#include <stdio.h>', '', 'int main() {']

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.value == "◈F":
                func_lines, i = self.parse_function(tokens, i, "c")
                lines.extend(func_lines)
            elif token.value == "◈":
                var_line, i = self.parse_variable(tokens, i, "c")
                lines.append(var_line)
            elif token.value == "◎>":
                print_line, i = self.parse_print(tokens, i, "c")
                lines.append(print_line)
            elif token.value == "▶MAIN":
                i += 1
                if i < len(tokens) and tokens[i].value == "{":
                    i += 1

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

            if token.value == "◈F":
                func_lines, i = self.parse_function(tokens, i, "mojo")
                lines.extend(func_lines)
            elif token.value == "◈":
                var_line, i = self.parse_variable(tokens, i, "mojo")
                lines.append(var_line)
            elif token.value == "◎>":
                print_line, i = self.parse_print(tokens, i, "mojo")
                lines.append(print_line)
            elif token.value == "▶MAIN":
                i += 1
                if i < len(tokens) and tokens[i].value == "{":
                    i += 1

            i += 1

        return "\n".join(lines)

    def parse_function(self, tokens: List[XToken], start: int, lang: str) -> Tuple[List[str], int]:
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
                    if i < len(tokens) and tokens[i].value == "∈":
                        i += 1
                        if i < len(tokens):
                            param_type = self.map_type(tokens[i].value, lang)
                            i += 1
                    params.append(f"{param_name}: {param_type}")
                i += 1
            if i < len(tokens) and tokens[i].value == ")":
                i += 1

        ret_type = ""
        if i < len(tokens) and tokens[i].value == "→":
            i += 1
            if i < len(tokens):
                ret_type = f" -> {self.map_type(tokens[i].value, lang)}"
                i += 1

        if lang == "rust":
            lines = [f"    fn {name}({', '.join(params)}){ret_type} {{"]
        elif lang == "c":
            ret_c = ret_type.replace("->", "").strip() if ret_type else "void"
            lines = [f"{ret_c} {name}({', '.join(params)}) {{"]
        else:
            lines = [f"    fn {name}({', '.join(params)}){ret_type}:"]

        i += 1
        brace_count = 1
        while i < len(tokens) and brace_count > 0:
            if tokens[i].value == "{":
                brace_count += 1
            elif tokens[i].value == "}":
                brace_count -= 1
            if brace_count > 0:
                if lang == "rust":
                    lines.append(f"        {self.rustify_token(tokens[i])};")
                elif lang == "c":
                    lines.append(f"        {self.cify_token(tokens[i])};")
                else:
                    lines.append(f"        {self.mojofy_token(tokens[i])}")
            i += 1

        if lang in ("rust", "mojo"):
            lines.append("    }")
        else:
            lines.append("}")

        return lines, i

    def parse_variable(self, tokens: List[XToken], start: int, lang: str) -> Tuple[str, int]:
        """解析变量"""
        i = start + 1

        name = ""
        if i < len(tokens) and tokens[i].type == "IDENT":
            name = tokens[i].value
            i += 1

        var_type = ""
        if i < len(tokens) and tokens[i].value == "∈":
            i += 1
            if i < len(tokens):
                var_type = self.map_type(tokens[i].value, lang)
                i += 1

        value = ""
        if i < len(tokens) and tokens[i].value == "=":
            i += 1
            while i < len(tokens) and tokens[i].value not in (";", "{", "}"):
                value += self.rustify_token(tokens[i])
                i += 1

        if lang == "rust":
            type_str = f": {var_type}" if var_type else ""
            return f"    let {name}{type_str} = {value};", i
        elif lang == "c":
            type_str = var_type if var_type else "int"
            return f"    {type_str} {name} = {value};", i
        else:
            type_str = f": {var_type}" if var_type else ""
            return f"    var {name}{type_str} = {value}", i

    def parse_print(self, tokens: List[XToken], start: int, lang: str) -> Tuple[str, int]:
        """解析打印"""
        i = start + 1
        args = []

        while i < len(tokens) and tokens[i].value not in (";", "{", "}"):
            if tokens[i].type in ("IDENT", "NUMBER", "STRING"):
                args.append(tokens[i].value)
            i += 1

        if lang == "rust":
            return f'    println!("{{}}", {", ".join(args)});', i
        elif lang == "c":
            return f'    printf("{args[0] if args else ""}\\n");', i
        else:
            return f'    print({", ".join(args)});', i

    def map_type(self, x_type: str, lang: str) -> str:
        """类型映射"""
        type_map = {
            "Int": {"rust": "i32", "c": "int", "mojo": "Int"},
            "Float": {"rust": "f64", "c": "double", "mojo": "Float64"},
            "Bool": {"rust": "bool", "c": "int", "mojo": "Bool"},
            "String": {"rust": "String", "c": "char*", "mojo": "String"},
        }
        return type_map.get(x_type, {}).get(lang, "i32")

    def rustify_token(self, token: XToken) -> str:
        """转换为 Rust 风格"""
        conversions = {
            "◀RET": "return",
            "◎>": "println!",
            "◎": "print",
            "?": "if",
            "◈": "let",
            "∈": ": i32",
            "∉": ": f64",
            "∈b": ": bool",
            "√": "true",
            "×": "false",
            "∅": "None",
        }
        return conversions.get(token.value, token.value)

    def cify_token(self, token: XToken) -> str:
        """转换为 C 风格"""
        conversions = {
            "◀RET": "return",
            "◎>": 'printf("\\n")',
            "◎": "printf",
            "?": "if",
            "◈": "",
            "∈": "int",
            "∉": "double",
            "∈b": "int",
            "√": "1",
            "×": "0",
            "∅": "NULL",
        }
        return conversions.get(token.value, token.value)

    def mojofy_token(self, token: XToken) -> str:
        """转换为 Mojo 风格"""
        conversions = {
            "◀RET": "return",
            "◎>": "print",
            "◎": "print",
            "?": "if",
            "◈": "var",
            "∈": ": Int",
            "∉": ": Float64",
            "∈b": ": Bool",
            "√": "True",
            "×": "False",
            "∅": "None",
        }
        return conversions.get(token.value, token.value)


SAMPLE_X_V2 = """▶MAIN{
◈F add(a,b)∈→Int{
◀a+b
}
◈ result = ◈F add(5,3)
◎>result
}"""


def demo():
    """演示"""
    print("=" * 60)
    print("XC 语言 V2 (纯符号版) 编译器演示")
    print("=" * 60)

    print("\n原始 XC 代码 (纯符号):")
    print(SAMPLE_X_V2)

    compiler = XCompilerV2("rust")
    print("\n编译为 Rust:")
    print(compiler.compile(SAMPLE_X_V2))

    compiler = XCompilerV2("c")
    print("\n编译为 C:")
    print(compiler.compile(SAMPLE_X_V2))

    compiler = XCompilerV2("mojo")
    print("\n编译为 Mojo:")
    print(compiler.compile(SAMPLE_X_V2))


if __name__ == "__main__":
    demo()
