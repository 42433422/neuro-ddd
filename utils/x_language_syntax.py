"""
XC 语言 - 符号化语法规范
使用 !@#￥%^&* 等符号作为关键字

设计理念: 让代码看起来像神秘符号,但逻辑清晰可编译

---------------------------------------------------------------------------
V3 定稿附录（与 .trae/specs/x-language-fusion/spec.md 对齐，实现可渐进）
总命名律：符号 = 种类（范畴），首字母 = 作用（细分子操作，多为英文首字母）。
---------------------------------------------------------------------------
- 打印/输入：◎O(expr)、◎I($x)；勿再用单独「!」表示打印。
- 逻辑非：仅「!expr」；「! x + y」解析为「(!x)+y」；打印和用 ◎O (x+y)。
- 条件：「?」仅 if；输入已迁到 ◎I。
- 类型：$x: int = 0；list<int>；bool 字面 true/false。
- 函数：%name(a: t, ...) -> r { ... }；^ 返回。
- 结构体：&Name { f: t, ... }；值 &Name{ f: e }；字段 obj.f。
- 标准库：IO ◎+字母；网络 ≈+字母；数学 µ+字母（见 spec V3 表）。
- 功能状态 / match·enum·泛型·trait·闭包·Result·async·测试：见 spec「功能覆盖与实现状态」与「vNext 符号草案」；V3 的 ? 不可兼作 Rust 的 ? 传播。
- 替代 C：见 spec「XC 作为 C 替代语言（C-Parity 扩展）」— 预处理 ⟨H/⟨D/…、C 类型全集、union/¶C、switch ?▶、§L/§G、⌁ 函数指针、Ω 堆、上下文 ~ 按位非 等。
---------------------------------------------------------------------------
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int


class XCLanguageSyntax:
    """
    XC 语言语法规则定义

    符号对照表:
    ═══════════════════════════════════════════════════════════════════
    XC 符号        | C/Rust/Mojo 对应      | 含义
    ═══════════════════════════════════════════════════════════════════
    !MAIN         | int main()            | 程序入口
    !VAR          | let/var/int           | 变量声明
    !FUNC         | fn                    | 函数定义
    !STRUCT       | struct                | 结构体
    !IF           | if                    | 条件判断
    !ELSE         | else                  | 否则
    !LOOP         | for/while             | 循环
    !WHILE        | while                 | 当循环
    !RETURN       | return                | 返回
    !PRINT        | println!/printf       | 打印输出
    !INPUT        | scanf/readline        | 输入
    !TRUE         | true/True/1           | 真
    !FALSE        | false/False/0         | 假
    !NULL         | null/None/NULL        | 空
    !AND          | && / and / &&         | 逻辑与
    !OR           | || / or               | 逻辑或
    !NOT          | ! / not               | 逻辑非
    !EQUAL        | ==                    | 等于
    !NOTEQUAL     | !=                    | 不等于
    !GREATER      | >                     | 大于
    !LESS         | <                     | 小于
    !ADD          | +                     | 加法
    !SUB          | -                     | 减法
    !MUL          | *                     | 乘法
    !DIV          | /                     | 除法
    !MOD          | %                     | 取模
    !ASSIGN       | =                     | 赋值
    !POINTER      | * / & / ref           | 指针/引用
    !ARROW        | ->                    | 返回/指向
    !LPAREN       | (                     | 左括号
    !RPAREN       | )                     | 右括号
    !LBRACE       | {                     | 左花括号
    !RBRACE       | }                     | 右花括号
    !LBRACKET     | [                     | 左方括号
    !RBRACKET     | ]                     | 右方括号
    !SEMICOLON    | ;                     | 分号
    !COLON        | :                     | 冒号
    !COMMA        | ,                     | 逗号
    !DOT          | .                     | 点号
    !STRING       | "..."                | 字符串
    !COMMENT      | // /* */ #            | 注释
    ═══════════════════════════════════════════════════════════════════
    ^INT          | i32/i64/u32           | 整数类型
    ^FLOAT        | f32/f64               | 浮点类型
    ^BOOL         | bool                  | 布尔类型
    ^STRING       | String                | 字符串类型
    ^VOID         | ()/void               | 空类型
    ═══════════════════════════════════════════════════════════════════
    ~INCLUDE      | #include              | 包含头文件
    ~IMPORT       | import/use            | 导入模块
    ~MACRO        | macro/const           | 宏定义
    ═══════════════════════════════════════════════════════════════════
    @SAFE         | &mut / owned          | 内存安全
    @ASYNC        | async                 | 异步
    @THREAD       | thread                | 线程
    @MEM          | alloc/free            | 内存管理
    ═══════════════════════════════════════════════════════════════════
    $LOOP         | Iterator/trait        | 迭代器
    $YIELD        | yield                 | 生成器
    $MATCH        | match/switch         | 模式匹配
    $CASE         | case/_               | 分支
    ═══════════════════════════════════════════════════════════════════
    #DEFINE       | const/let             | 常量定义
    #TYPE         | typedef/type          | 类型定义
    ═══════════════════════════════════════════════════════════════════
    %STACK        | stack alloc           | 栈分配
    %HEAP         | heap/Box              | 堆分配
    %REF          | reference             | 引用计数
    ═══════════════════════════════════════════════════════════════════
    """

    KEYWORDS = {
        "!MAIN": "main",
        "!VAR": "var",
        "!FUNC": "fn",
        "!STRUCT": "struct",
        "!IF": "if",
        "!ELSE": "else",
        "!LOOP": "for",
        "!WHILE": "while",
        "!RETURN": "return",
        "!PRINT": "print",
        "!INPUT": "input",
        "!TRUE": "true",
        "!FALSE": "false",
        "!NULL": "null",
        "!AND": "&&",
        "!OR": "||",
        "!NOT": "!",
        "!EQUAL": "==",
        "!NOTEQUAL": "!=",
        "!GREATER": ">",
        "!LESS": "<",
        "!ADD": "+",
        "!SUB": "-",
        "!MUL": "*",
        "!DIV": "/",
        "!MOD": "%",
        "!ASSIGN": "=",
        "!POINTER": "*",
        "!ARROW": "->",
    }

    TYPE_KEYWORDS = {
        "^INT": "i32",
        "^FLOAT": "f64",
        "^BOOL": "bool",
        "^STRING": "String",
        "^VOID": "()",
        "^UINT": "u32",
        "^INT8": "i8",
        "^INT16": "i16",
        "^INT64": "i64",
    }

    PREPROCESSOR = {
        "~INCLUDE": "#include",
        "~IMPORT": "use",
        "~MACRO": "macro",
    }

    ATTRIBUTES = {
        "@SAFE": "&mut",
        "@ASYNC": "async",
        "@THREAD": "thread",
        "@MEM": "mem",
    }

    SPECIAL = {
        "$LOOP": "iter",
        "$YIELD": "yield",
        "$MATCH": "match",
        "$CASE": "_",
    }

    DEFINES = {
        "#DEFINE": "const",
        "#TYPE": "type",
    }

    MEMORY = {
        "%STACK": "stack",
        "%HEAP": "heap",
        "%REF": "ref_count",
    }

    OPERATORS = {
        "!ADD": "+",
        "!SUB": "-",
        "!MUL": "*",
        "!DIV": "/",
        "!MOD": "%",
        "!EQUAL": "==",
        "!NOTEQUAL": "!=",
        "!GREATER": ">",
        "!LESS": "<",
        "!AND": "&&",
        "!OR": "||",
        "!NOT": "!",
    }


class XCLanguageLexer:
    """XC 语言词法分析器"""

    TOKEN_PATTERNS = [
        ("KEYWORD", r"!(?:MAIN|VAR|FUNC|STRUCT|IF|ELSE|LOOP|WHILE|RETURN|PRINT|INPUT|TRUE|FALSE|NULL|AND|OR|NOT|EQUAL|NOTEQUAL|GREATER|LESS|ADD|SUB|MUL|DIV|MOD|ASSIGN|POINTER|ARROW|LPAREN|RPAREN|LBRACE|RBRACE|LBRACKET|RBRACKET|SEMICOLON|COLON|COMMA|DOT)"),
        ("TYPE_KEYWORD", r"\^(?:INT|FLOAT|BOOL|STRING|VOID|UINT|INT8|INT16|INT64)"),
        ("PREPROCESSOR", r"~(?:INCLUDE|IMPORT|MACRO)"),
        ("ATTRIBUTE", r"@(?:SAFE|ASYNC|THREAD|MEM)"),
        ("SPECIAL", r"\$(?:LOOP|YIELD|MATCH|CASE)"),
        ("DEFINE", r"#(?:DEFINE|TYPE)"),
        ("MEMORY", r"%(?:STACK|HEAP|REF)"),
        ("IDENTIFIER", r"[a-zA-Z_]\w*"),
        ("NUMBER", r"\d+\.?\d*"),
        ("STRING", r'"(?:[^"\\]|\\.)*"'),
        ("OPERATOR", r"[+\-*/%=<>!&|^~]+"),
        ("PUNCTUATION", r"[()\[\]{}:;,.]"),
        ("NEWLINE", r"\n"),
        ("WHITESPACE", r"[ \t]+"),
        ("COMMENT", r"//.*?$|/\*[\s\S]*?\*/"),
    ]

    def __init__(self, code: str):
        self.code = code
        self.tokens = []
        self.errors = []
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        """分词"""
        token_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in self.TOKEN_PATTERNS)
        token_pattern = re.compile(token_regex, re.MULTILINE)

        pos = 0
        while pos < len(self.code):
            match = token_pattern.match(self.code, pos)
            if not match:
                self.errors.append(f"无法识别的字符: '{self.code[pos]}' at line {self.line}")
                pos += 1
                continue

            kind = match.lastgroup
            value = match.group()

            if kind not in ("WHITESPACE", "NEWLINE", "COMMENT"):
                self.tokens.append(Token(kind, value, self.line, self.column))

            if kind == "NEWLINE":
                self.line += 1
                self.column = 1
            else:
                self.column += len(value)

            pos = match.end()

        return self.tokens


class XCLanguageParser:
    """XC 语言语法分析器"""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.ast = []

    def parse(self) -> Dict:
        """解析为 AST"""
        while self.pos < len(self.tokens):
            stmt = self.parse_statement()
            if stmt:
                self.ast.append(stmt)
            else:
                self.pos += 1

        return {"type": "program", "body": self.ast}

    def parse_statement(self) -> Optional[Dict]:
        """解析语句"""
        token = self.current_token()
        if not token:
            return None

        if token.type == "KEYWORD":
            return self.parse_keyword_statement()
        elif token.type == "PREPROCESSOR":
            return self.parse_preprocessor()
        elif token.type == "IDENTIFIER":
            return self.parse_expression_statement()

        return None

    def current_token(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self):
        self.pos += 1

    def parse_keyword_statement(self) -> Dict:
        """解析关键字语句"""
        token = self.current_token()
        value = token.value

        if value == "!FUNC":
            return self.parse_function()
        elif value == "!VAR":
            return self.parse_variable()
        elif value == "!STRUCT":
            return self.parse_struct()
        elif value == "!IF":
            return self.parse_if()
        elif value == "!LOOP":
            return self.parse_loop()
        elif value == "!WHILE":
            return self.parse_while()
        elif value == "!RETURN":
            return self.parse_return()
        elif value == "!PRINT":
            return self.parse_print()
        elif value == "!STRUCT":
            return self.parse_struct()

        return None

    def parse_function(self) -> Dict:
        """解析函数定义"""
        self.advance()
        name_token = self.current_token()
        name = name_token.value if name_token and name_token.type == "IDENTIFIER" else "anonymous"
        self.advance()

        params = []
        if self.current_token() and self.current_token().value == "!LPAREN":
            self.advance()
            params = self.parse_param_list()

        return_type = None
        if self.current_token() and self.current_token().value == "!ARROW":
            self.advance()
            type_token = self.current_token()
            if type_token and type_token.type == "TYPE_KEYWORD":
                return_type = type_token.value
                self.advance()

        body = self.parse_block()

        return {
            "type": "function",
            "name": name,
            "params": params,
            "return_type": return_type,
            "body": body,
        }

    def parse_variable(self) -> Dict:
        """解析变量声明"""
        self.advance()
        name_token = self.current_token()
        name = name_token.value if name_token and name_token.type == "IDENTIFIER" else "x"
        self.advance()

        var_type = None
        if self.current_token() and self.current_token().type == "TYPE_KEYWORD":
            var_type = self.current_token().value
            self.advance()

        value = None
        if self.current_token() and self.current_token().value == "!ASSIGN":
            self.advance()
            value = self.parse_expression()

        return {
            "type": "variable",
            "name": name,
            "var_type": var_type,
            "value": value,
        }

    def parse_param_list(self) -> List[Dict]:
        """解析参数列表"""
        params = []
        while self.current_token() and self.current_token().value != "!RPAREN":
            if self.current_token().type == "IDENTIFIER":
                param_name = self.current_token().value
                self.advance()
                param_type = None
                if self.current_token() and self.current_token().type == "TYPE_KEYWORD":
                    param_type = self.current_token().value
                    self.advance()
                params.append({"name": param_name, "type": param_type})
            if self.current_token() and self.current_token().value == "!COMMA":
                self.advance()
        if self.current_token() and self.current_token().value == "!RPAREN":
            self.advance()
        return params

    def parse_block(self) -> List[Dict]:
        """解析代码块"""
        statements = []
        if self.current_token() and self.current_token().value == "!LBRACE":
            self.advance()
            while self.current_token() and self.current_token().value != "!RBRACE":
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
                else:
                    self.advance()
            if self.current_token() and self.current_token().value == "!RBRACE":
                self.advance()
        return statements

    def parse_if(self) -> Dict:
        """解析 if 语句"""
        self.advance()
        condition = self.parse_expression()
        body = self.parse_block()
        else_body = None
        if self.current_token() and self.current_token().value == "!ELSE":
            self.advance()
            else_body = self.parse_block()
        return {
            "type": "if",
            "condition": condition,
            "body": body,
            "else": else_body,
        }

    def parse_loop(self) -> Dict:
        """解析 for 循环"""
        self.advance()
        var_name = None
        if self.current_token() and self.current_token().type == "IDENTIFIER":
            var_name = self.current_token().value
            self.advance()
        start = self.parse_expression()
        end = None
        if self.current_token() and self.current_token().value == "!COMMA":
            self.advance()
            end = self.parse_expression()
        body = self.parse_block()
        return {
            "type": "for",
            "var": var_name,
            "start": start,
            "end": end,
            "body": body,
        }

    def parse_while(self) -> Dict:
        """解析 while 循环"""
        self.advance()
        condition = self.parse_expression()
        body = self.parse_block()
        return {
            "type": "while",
            "condition": condition,
            "body": body,
        }

    def parse_return(self) -> Dict:
        """解析 return 语句"""
        self.advance()
        value = self.parse_expression()
        return {"type": "return", "value": value}

    def parse_print(self) -> Dict:
        """解析 print 语句"""
        self.advance()
        args = []
        while self.current_token() and self.current_token().value not in ("!SEMICOLON",):
            arg = self.parse_expression()
            if arg:
                args.append(arg)
        return {"type": "print", "args": args}

    def parse_struct(self) -> Dict:
        """解析 struct 定义"""
        self.advance()
        name_token = self.current_token()
        name = name_token.value if name_token and name_token.type == "IDENTIFIER" else "XStruct"
        self.advance()
        fields = []
        if self.current_token() and self.current_token().value == "!LBRACE":
            self.advance()
            while self.current_token() and self.current_token().value != "!RBRACE":
                if self.current_token().type == "IDENTIFIER":
                    field_name = self.current_token().value
                    self.advance()
                    field_type = None
                    if self.current_token() and self.current_token().type == "TYPE_KEYWORD":
                        field_type = self.current_token().value
                        self.advance()
                    fields.append({"name": field_name, "type": field_type})
                else:
                    self.advance()
            if self.current_token() and self.current_token().value == "!RBRACE":
                self.advance()
        return {"type": "struct", "name": name, "fields": fields}

    def parse_expression(self) -> Optional[Dict]:
        """解析表达式"""
        token = self.current_token()
        if not token:
            return None

        if token.type == "NUMBER":
            self.advance()
            return {"type": "number", "value": token.value}
        elif token.type == "STRING":
            self.advance()
            return {"type": "string", "value": token.value}
        elif token.type == "IDENTIFIER":
            self.advance()
            return {"type": "identifier", "name": token.value}
        elif token.type in ("KEYWORD", "TYPE_KEYWORD") and token.value in XCLanguageSyntax.OPERATORS:
            self.advance()
            return {"type": "operator", "op": XCLanguageSyntax.OPERATORS[token.value]}

        return None

    def parse_preprocessor(self) -> Dict:
        """解析预处理器指令"""
        token = self.current_token()
        self.advance()
        value = token.value if token else ""
        return {"type": "preprocessor", "directive": value}

    def parse_expression_statement(self) -> Optional[Dict]:
        """解析表达式语句"""
        token = self.current_token()
        if not token or token.type != "IDENTIFIER":
            return None
        self.advance()
        return {"type": "expr_statement", "name": token.value}


class XCLanguageCompiler:
    """XC 语言编译器 - 将 XC 代码编译为目标语言"""

    def __init__(self, target_lang: str = "rust"):
        self.target_lang = target_lang
        self.syntax = XCLanguageSyntax()

    def compile(self, x_code: str) -> str:
        """编译 XC 代码到目标语言"""
        lexer = XCLanguageLexer(x_code)
        tokens = lexer.tokenize()

        if lexer.errors:
            print(f"词法分析错误: {lexer.errors}")

        parser = XCLanguageParser(tokens)
        ast = parser.parse()

        return self.generate_code(ast)

    def generate_code(self, ast: Dict) -> str:
        """从 AST 生成目标语言代码"""
        if self.target_lang == "rust":
            return self.generate_rust(ast)
        elif self.target_lang == "c":
            return self.generate_c(ast)
        elif self.target_lang == "mojo":
            return self.generate_mojo(ast)
        return ""

    def generate_rust(self, ast: Dict) -> str:
        """生成 Rust 代码"""
        lines = ["fn main() {"]

        for node in ast.get("body", []):
            if node["type"] == "function":
                params = ", ".join(
                    f"{p['name']}: {self.map_type(p['type'])}" for p in node["params"]
                )
                return_type = f" -> {self.map_type(node['return_type'])}" if node["return_type"] else ""
                lines.append(f"    fn {node['name']}({params}){return_type} {{")
                for stmt in node["body"]:
                    lines.append(f"        {self.rust_stmt(stmt)}")
                lines.append("    }")
            elif node["type"] == "variable":
                var_type = f": {self.map_type(node['var_type'])}" if node['var_type'] else ""
                lines.append(f"    let {node['name']}{var_type} = {self.rust_expr(node['value'])};")
            elif node["type"] == "print":
                for arg in node.get("args", []):
                    lines.append(f'    println!("{{{self.rust_expr(arg)}}}");')

        lines.append("}")
        return "\n".join(lines)

    def generate_c(self, ast: Dict) -> str:
        """生成 C 代码"""
        lines = ['#include <stdio.h>', '']

        for node in ast.get("body", []):
            if node["type"] == "function":
                params = ", ".join(
                    f"{self.map_type(p['type'])} {p['name']}" for p in node["params"]
                )
                return_type = self.map_type(node["return_type"]) if node["return_type"] else "void"
                lines.append(f"{return_type} {node['name']}({params}) {{")
                for stmt in node["body"]:
                    lines.append(f"    {self.c_stmt(stmt)};")
                lines.append("}")
            elif node["type"] == "variable":
                var_type = self.map_type(node["var_type"]) if node["var_type"] else "int"
                lines.append(f"{var_type} {node['name']} = {self.rust_expr(node['value'])};")

        lines.insert(2, "int main() {")
        lines.append("    return 0;")
        lines.append("}")
        return "\n".join(lines)

    def generate_mojo(self, ast: Dict) -> str:
        """生成 Mojo 代码"""
        lines = ["fn main():"]

        for node in ast.get("body", []):
            if node["type"] == "function":
                params = ", ".join(
                    f"{p['name']}: {self.map_type(p['type'])}" for p in node["params"]
                )
                return_type = f" -> {self.map_type(node['return_type'])}" if node["return_type"] else ""
                lines.append(f"    fn {node['name']}({params}){return_type}:")
                for stmt in node["body"]:
                    lines.append(f"        {self.mojo_stmt(stmt)}")
            elif node["type"] == "variable":
                var_type = f": {self.map_type(node['var_type'])}" if node["var_type"] else ""
                lines.append(f"    var {node['name']}{var_type} = {self.rust_expr(node['value'])}")

        return "\n".join(lines)

    def map_type(self, x_type: str) -> str:
        """映射 XC 语言类型到目标语言类型"""
        if not x_type:
            return "i32"

        type_map = {
            "^INT": "i32",
            "^FLOAT": "f64",
            "^BOOL": "bool",
            "^STRING": "String",
            "^VOID": "()",
            "^UINT": "u32",
        }
        return type_map.get(x_type, "i32")

    def rust_stmt(self, stmt: Dict) -> str:
        """生成 Rust 语句"""
        if stmt["type"] == "return":
            return f"return {self.rust_expr(stmt['value'])};"
        elif stmt["type"] == "print":
            return f'println!("{{{self.rust_expr(stmt["args"][0])}}}");'
        return ""

    def rust_expr(self, expr: Dict) -> str:
        """生成 Rust 表达式"""
        if not expr:
            return "()"
        if expr["type"] == "number":
            return expr["value"]
        elif expr["type"] == "string":
            return expr["value"]
        elif expr["type"] == "identifier":
            return expr["name"]
        elif expr["type"] == "operator":
            return expr["op"]
        return "()"

    def c_stmt(self, stmt: Dict) -> str:
        """生成 C 语句"""
        return self.rust_stmt(stmt)

    def mojo_stmt(self, stmt: Dict) -> str:
        """生成 Mojo 语句"""
        if stmt["type"] == "return":
            return f"return {self.rust_expr(stmt['value'])}"
        elif stmt["type"] == "print":
            return f"print({self.rust_expr(stmt['args'][0])})"
        return ""


class XCLanguageToTargetTranslator:
    """XC 语言到目标语言翻译器"""

    def __init__(self):
        self.syntax = XCLanguageSyntax()

    def translate(self, x_code: str, target: str = "rust") -> str:
        """翻译 XC 代码到目标语言"""
        compiler = XCLanguageCompiler(target)
        return compiler.compile(x_code)

    def translate_to_c(self, x_code: str) -> str:
        return self.translate(x_code, "c")

    def translate_to_rust(self, x_code: str) -> str:
        return self.translate(x_code, "rust")

    def translate_to_mojo(self, x_code: str) -> str:
        return self.translate(x_code, "mojo")


SAMPLE_X_CODE = """
!FUNC add !LPAREN a ^INT !COMMA b ^INT !RPAREN !ARROW ^INT
!LBRACE
    !RETURN a !ADD b
!RBRACE

!FUNC main
!LBRACE
    !VAR result ^INT !ASSIGN !FUNC add !LPAREN !NUMBER 5 !COMMA !NUMBER 3 !RPAREN
    !PRINT result
!RBRACE
"""


def demo():
    """演示 XC 语言"""
    print("=" * 60)
    print("XC 语言演示")
    print("=" * 60)
    print("\n原始 XC 代码:")
    print(SAMPLE_X_CODE)

    translator = XCLanguageToTargetTranslator()

    print("\n编译为 Rust:")
    rust_code = translator.translate_to_rust(SAMPLE_X_CODE)
    print(rust_code)

    print("\n编译为 C:")
    c_code = translator.translate_to_c(SAMPLE_X_CODE)
    print(c_code)

    print("\n编译为 Mojo:")
    mojo_code = translator.translate_to_mojo(SAMPLE_X_CODE)
    print(mojo_code)


if __name__ == "__main__":
    demo()
