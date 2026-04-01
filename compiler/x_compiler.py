"""
XC 语言编译器 - 将 XC 符号代码编译为 C/Rust/Mojo

使用方法:
    python x_compiler.py --input code.x --target rust
    python x_compiler.py --input code.x --target c
    python x_compiler.py --input code.x --target mojo
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


X_SYMBOLS = {
    "!MAIN": "main",
    "!VAR": "let",
    "!FUNC": "fn",
    "!STRUCT": "struct",
    "!IF": "if",
    "!ELSE": "else",
    "!LOOP": "for",
    "!WHILE": "while",
    "!RETURN": "return",
    "!PRINT": "println!",
    "!INPUT": "readline",
    "!TRUE": "true",
    "!FALSE": "false",
    "!NULL": "None",
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
    "!ARROW": "->",
    "!LPAREN": "(",
    "!RPAREN": ")",
    "!LBRACE": "{",
    "!RBRACE": "}",
    "!LBRACKET": "[",
    "!RBRACKET": "]",
    "!SEMICOLON": ";",
    "!COLON": ":",
    "!COMMA": ",",
    "!DOT": ".",
}

X_TYPES = {
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

X_PREPROCESSOR = {
    "~INCLUDE": "#include",
    "~IMPORT": "use",
    "~MACRO": "macro",
}

X_ATTRIBUTES = {
    "@SAFE": "&mut",
    "@ASYNC": "async",
    "@THREAD": "thread",
    "@MEM": "mem",
}

X_MEMORY = {
    "%STACK": "stack",
    "%HEAP": "heap",
    "%REF": "ref_count",
}


class XLexer:
    """XC 语言词法分析器"""

    TOKEN_TYPES = [
        ("KEYWORD", r"!(?:MAIN|VAR|FUNC|STRUCT|IF|ELSE|LOOP|WHILE|RETURN|PRINT|INPUT|TRUE|FALSE|NULL|AND|OR|NOT|EQUAL|NOTEQUAL|GREATER|LESS|ADD|SUB|MUL|DIV|MOD|ASSIGN|ARROW|LPAREN|RPAREN|LBRACE|RBRACE|LBRACKET|RBRACKET|SEMICOLON|COLON|COMMA|DOT)"),
        ("TYPE_KW", r"\^(?:INT|FLOAT|BOOL|STRING|VOID|UINT|INT8|INT16|INT64)"),
        ("PREPROC", r"~(?:INCLUDE|IMPORT|MACRO)"),
        ("ATTR", r"@(?:SAFE|ASYNC|THREAD|MEM)"),
        ("MEMORY", r"%(?:STACK|HEAP|REF)"),
        ("IDENT", r"[a-zA-Z_]\w*"),
        ("NUMBER", r"\d+\.?\d*"),
        ("STRING", r'"[^"]*"'),
        ("COMMENT", r"//.*|/\*[\s\S]*?\*/"),
        ("WHITESPACE", r"\s+"),
    ]

    def __init__(self, code: str):
        self.code = code
        self.tokens = []
        self.line = 1
        self.errors = []

    def tokenize(self) -> List[Tuple[str, str]]:
        """分词"""
        pos = 0
        while pos < len(self.code):
            matched = False
            for token_type, pattern in self.TOKEN_TYPES:
                match = re.match(pattern, self.code[pos:])
                if match:
                    value = match.group()
                    if token_type != "WHITESPACE" and token_type != "COMMENT":
                        self.tokens.append((token_type, value, self.line))
                    if "\n" in value:
                        self.line += value.count("\n")
                    pos += len(value)
                    matched = True
                    break

            if not matched:
                self.errors.append(f"未知字符 at line {self.line}: {self.code[pos]}")
                pos += 1

        return self.tokens


class XParser:
    """XC 语言解析器"""

    def __init__(self, tokens: List[Tuple[str, str, int]]):
        self.tokens = tokens
        self.pos = 0
        self.ast = []

    def current(self) -> Optional[Tuple[str, str, int]]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def eat(self):
        self.pos += 1

    def parse(self) -> Dict:
        """解析 tokens 为 AST"""
        while self.current():
            stmt = self.parse_statement()
            if stmt:
                self.ast.append(stmt)
            else:
                self.eat()

        return {"type": "program", "body": self.ast}

    def parse_statement(self) -> Optional[Dict]:
        """解析语句"""
        token = self.current()
        if not token:
            return None

        token_type, value, line = token

        if token_type == "KEYWORD":
            return self.parse_keyword(value)
        elif token_type == "PREPROC":
            return self.parse_preprocessor(value)
        elif token_type == "IDENT":
            return self.parse_ident_expression(value)

        return None

    def parse_keyword(self, kw: str) -> Optional[Dict]:
        """解析关键字"""
        handlers = {
            "!FUNC": self.parse_function,
            "!VAR": self.parse_variable,
            "!STRUCT": self.parse_struct,
            "!IF": self.parse_if,
            "!LOOP": self.parse_for,
            "!WHILE": self.parse_while,
            "!RETURN": self.parse_return,
            "!PRINT": self.parse_print,
        }

        handler = handlers.get(kw)
        if handler:
            return handler()
        return None

    def parse_function(self) -> Dict:
        """解析函数"""
        self.eat()
        name = self.parse_ident()
        params = self.parse_params()
        return_type = self.parse_return_type()
        body = self.parse_block()

        return {
            "type": "function",
            "name": name,
            "params": params,
            "return_type": return_type,
            "body": body,
        }

    def parse_ident(self) -> str:
        """解析标识符"""
        token = self.current()
        if token and token[0] == "IDENT":
            val = token[1]
            self.eat()
            return val
        return "unknown"

    def parse_type(self) -> Optional[str]:
        """解析类型"""
        token = self.current()
        if token and token[0] == "TYPE_KW":
            val = token[1]
            self.eat()
            return val
        return None

    def parse_params(self) -> List[Dict]:
        """解析参数列表"""
        params = []
        token = self.current()
        if token and token[1] == "!LPAREN":
            self.eat()
            while self.current() and self.current()[1] != "!RPAREN":
                param_name = self.parse_ident()
                param_type = self.parse_type()
                params.append({"name": param_name, "type": param_type})
                if self.current() and self.current()[1] == "!COMMA":
                    self.eat()
            if self.current() and self.current()[1] == "!RPAREN":
                self.eat()
        return params

    def parse_return_type(self) -> Optional[str]:
        """解析返回类型"""
        if self.current() and self.current()[1] == "!ARROW":
            self.eat()
            return self.parse_type()
        return None

    def parse_block(self) -> List[Dict]:
        """解析代码块"""
        statements = []
        token = self.current()
        if token and token[1] == "!LBRACE":
            self.eat()
            while self.current() and self.current()[1] != "!RBRACE":
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
                else:
                    self.eat()
            if self.current() and self.current()[1] == "!RBRACE":
                self.eat()
        return statements

    def parse_variable(self) -> Dict:
        """解析变量声明"""
        self.eat()
        name = self.parse_ident()
        var_type = self.parse_type()
        value = None
        if self.current() and self.current()[1] == "!ASSIGN":
            self.eat()
            value = self.parse_expression()
        return {
            "type": "variable",
            "name": name,
            "var_type": var_type,
            "value": value,
        }

    def parse_function_call(self) -> Dict:
        """解析函数调用"""
        name = self.parse_ident()
        args = []
        if self.current() and self.current()[1] == "!LPAREN":
            self.eat()
            while self.current() and self.current()[1] != "!RPAREN":
                arg = self.parse_expression()
                if arg:
                    args.append(arg)
                if self.current() and self.current()[1] == "!COMMA":
                    self.eat()
            if self.current() and self.current()[1] == "!RPAREN":
                self.eat()
        return {"type": "call", "name": name, "args": args}

    def parse_expression(self) -> Optional[Dict]:
        """解析表达式"""
        token = self.current()
        if not token:
            return None

        token_type, value, _ = token

        if token_type == "NUMBER":
            self.eat()
            return {"type": "number", "value": value}
        elif token_type == "STRING":
            self.eat()
            return {"type": "string", "value": value}
        elif token_type == "IDENT":
            self.eat()
            if self.current() and self.current()[1] == "!LPAREN":
                self.pos -= 1
                return self.parse_function_call()
            return {"type": "identifier", "name": value}
        elif token_type in ("KEYWORD", "TYPE_KW") and value in X_SYMBOLS:
            self.eat()
            op = X_SYMBOLS.get(value, value)
            return {"type": "operator", "op": op}
        elif token_type == "ATTR":
            self.eat()
            return {"type": "attribute", "value": value}
        elif token_type == "MEMORY":
            self.eat()
            return {"type": "memory", "value": value}

        return None

    def parse_if(self) -> Dict:
        """解析 if"""
        self.eat()
        condition = self.parse_expression()
        body = self.parse_block()
        else_body = None
        if self.current() and self.current()[1] == "!ELSE":
            self.eat()
            else_body = self.parse_block()
        return {"type": "if", "condition": condition, "body": body, "else": else_body}

    def parse_for(self) -> Dict:
        """解析 for 循环"""
        self.eat()
        var = self.parse_ident()
        start = self.parse_expression()
        end = self.parse_expression()
        body = self.parse_block()
        return {"type": "for", "var": var, "start": start, "end": end, "body": body}

    def parse_while(self) -> Dict:
        """解析 while 循环"""
        self.eat()
        condition = self.parse_expression()
        body = self.parse_block()
        return {"type": "while", "condition": condition, "body": body}

    def parse_return(self) -> Dict:
        """解析 return"""
        self.eat()
        value = self.parse_expression()
        return {"type": "return", "value": value}

    def parse_print(self) -> Dict:
        """解析 print"""
        self.eat()
        args = []
        while self.current() and self.current()[1] != "!SEMICOLON":
            arg = self.parse_expression()
            if arg:
                args.append(arg)
        return {"type": "print", "args": args}

    def parse_struct(self) -> Dict:
        """解析 struct"""
        self.eat()
        name = self.parse_ident()
        fields = []
        if self.current() and self.current()[1] == "!LBRACE":
            self.eat()
            while self.current() and self.current()[1] != "!RBRACE":
                field_name = self.parse_ident()
                field_type = self.parse_type()
                fields.append({"name": field_name, "type": field_type})
                if self.current() and self.current()[1] == "!SEMICOLON":
                    self.eat()
        return {"type": "struct", "name": name, "fields": fields}

    def parse_ident_expression(self, name: str) -> Dict:
        """解析标识符表达式"""
        return {"type": "identifier", "name": name}

    def parse_preprocessor(self, directive: str) -> Dict:
        """解析预处理器"""
        self.eat()
        value = ""
        if self.current():
            value = self.current()[1]
            self.eat()
        return {"type": "preprocessor", "directive": directive, "value": value}


class XCodeGenerator:
    """代码生成器"""

    def __init__(self, target: str = "rust"):
        self.target = target

    def generate(self, ast: Dict) -> str:
        """生成目标语言代码"""
        if self.target == "rust":
            return self.generate_rust(ast)
        elif self.target == "c":
            return self.generate_c(ast)
        elif self.target == "mojo":
            return self.generate_mojo(ast)
        return ""

    def map_type(self, x_type: str) -> str:
        """映射类型"""
        if self.target == "rust":
            return X_TYPES.get(x_type, "i32")
        elif self.target == "c":
            type_map = {"^INT": "int", "^FLOAT": "double", "^BOOL": "int", "^STRING": "char*", "^VOID": "void"}
            return type_map.get(x_type, "int")
        elif self.target == "mojo":
            type_map = {"^INT": "Int", "^FLOAT": "Float64", "^BOOL": "Bool", "^STRING": "String", "^VOID": "None"}
            return type_map.get(x_type, "Int")
        return "i32"

    def generate_rust(self, ast: Dict) -> str:
        """生成 Rust 代码"""
        lines = ["fn main() {"]

        for node in ast.get("body", []):
            if node["type"] == "function":
                params = ", ".join(f"{p['name']}: {self.map_type(p['type'])}" for p in node["params"])
                ret = f" -> {self.map_type(node['return_type'])}" if node.get("return_type") else ""
                lines.append(f"    fn {node['name']}({params}){ret} {{")
                for stmt in node["body"]:
                    lines.append(f"        {self.rust_stmt(stmt)}")
                lines.append("    }")
                lines.append("")
            elif node["type"] == "variable":
                t = f": {self.map_type(node['var_type'])}" if node.get("var_type") else ""
                v = self.rust_expr(node["value"]) if node.get("value") else "()"
                lines.append(f"    let {node['name']}{t} = {v};")
            elif node["type"] == "print":
                args = ", ".join(self.rust_expr(a) for a in node.get("args", []))
                lines.append(f'    println!("{{}}", {args});')

        lines.append("}")
        return "\n".join(lines)

    def rust_expr(self, expr: Dict) -> str:
        """Rust 表达式"""
        if not expr:
            return "()"
        t = expr["type"]
        if t == "number":
            return expr["value"]
        elif t == "string":
            return expr["value"]
        elif t == "identifier":
            return expr["name"]
        elif t == "operator":
            return expr["op"]
        elif t == "call":
            args = ", ".join(self.rust_expr(a) for a in expr.get("args", []))
            return f"{expr['name']}({args})"
        return "()"

    def rust_stmt(self, stmt: Dict) -> str:
        """Rust 语句"""
        t = stmt["type"]
        if t == "return":
            return f"return {self.rust_expr(stmt['value'])};"
        elif t == "print":
            args = ", ".join(self.rust_expr(a) for a in stmt.get("args", []))
            return f'println!("{{}}", {args});'
        elif t == "if":
            cond = self.rust_expr(stmt["condition"])
            body = "; ".join(self.rust_stmt(s) for s in stmt["body"])
            return f"if {cond} {{ {body} }}"
        elif t == "for":
            var = stmt["var"]
            start = self.rust_expr(stmt["start"])
            end = self.rust_expr(stmt["end"])
            return f"for {var} in {start}..{end} {{ }}"
        return ";"

    def generate_c(self, ast: Dict) -> str:
        """生成 C 代码"""
        lines = ['#include <stdio.h>', '']

        has_main = False
        for node in ast.get("body", []):
            if node["type"] == "function" and node["name"] == "main":
                has_main = True

        if not has_main:
            lines.append("int main() {")

        for node in ast.get("body", []):
            if node["type"] == "function":
                params = ", ".join(f"{self.map_type(p['type'])} {p['name']}" for p in node["params"])
                ret_type = self.map_type(node["return_type"]) if node.get("return_type") else "void"
                lines.append(f"{ret_type} {node['name']}({params}) {{")
                for stmt in node["body"]:
                    lines.append(f"    {self.c_stmt(stmt)};")
                lines.append("}")
                lines.append("")
            elif node["type"] == "variable":
                t = self.map_type(node["var_type"]) if node.get("var_type") else "int"
                v = self.rust_expr(node["value"]) if node.get("value") else "0"
                lines.append(f"{t} {node['name']} = {v};")
            elif node["type"] == "print":
                args = ", ".join(self.rust_expr(a) for a in node.get("args", []))
                lines.append(f'printf("%d\\n", {args});')

        if not has_main:
            lines.append("    return 0;")
            lines.append("}")

        return "\n".join(lines)

    def c_stmt(self, stmt: Dict) -> str:
        """C 语句"""
        return self.rust_stmt(stmt)

    def generate_mojo(self, ast: Dict) -> str:
        """生成 Mojo 代码"""
        lines = ["fn main():"]

        for node in ast.get("body", []):
            if node["type"] == "function":
                params = ", ".join(f"{p['name']}: {self.map_type(p['type'])}" for p in node["params"])
                ret = f" -> {self.map_type(node['return_type'])}" if node.get("return_type") else ""
                lines.append(f"    fn {node['name']}({params}){ret}:")
                for stmt in node["body"]:
                    lines.append(f"        {self.mojo_stmt(stmt)}")
                lines.append("")
            elif node["type"] == "variable":
                t = f": {self.map_type(node['var_type'])}" if node.get("var_type") else ""
                v = self.rust_expr(node["value"]) if node.get("value") else "0"
                lines.append(f"    var {node['name']}{t} = {v}")
            elif node["type"] == "print":
                args = ", ".join(self.rust_expr(a) for a in node.get("args", []))
                lines.append(f"    print({args})")

        return "\n".join(lines)

    def mojo_stmt(self, stmt: Dict) -> str:
        """Mojo 语句"""
        t = stmt["type"]
        if t == "return":
            return f"return {self.rust_expr(stmt['value'])}"
        elif t == "print":
            args = ", ".join(self.rust_expr(a) for a in stmt.get("args", []))
            return f"print({args})"
        elif t == "if":
            cond = self.rust_expr(stmt["condition"])
            body = "; ".join(self.mojo_stmt(s) for s in stmt["body"])
            return f"if {cond}: {body}"
        elif t == "for":
            var = stmt["var"]
            start = self.rust_expr(stmt["start"])
            end = self.rust_expr(stmt["end"])
            return f"for {var} in range({start}, {end}): pass"
        return "pass"


class XCompiler:
    """XC 语言编译器主类"""

    def __init__(self, target: str = "rust"):
        self.target = target
        self.lexer = None
        self.parser = None
        self.generator = XCodeGenerator(target)

    def compile(self, x_code: str) -> str:
        """编译 XC 代码到目标语言"""
        self.lexer = XLexer(x_code)
        tokens = self.lexer.tokenize()

        if self.lexer.errors:
            print(f"词法错误: {self.lexer.errors}")

        self.parser = XParser(tokens)
        ast = self.parser.parse()

        return self.generator.generate(ast)

    def compile_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """编译文件"""
        with open(input_path, "r", encoding="utf-8") as f:
            x_code = f.read()

        result = self.compile(x_code)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)

        return result


def x_to_target(x_code: str, target: str) -> str:
    """快捷翻译函数"""
    compiler = XCompiler(target)
    return compiler.compile(x_code)


SAMPLE_X_CODE = """!FUNC add !LPAREN a ^INT !COMMA b ^INT !RPAREN !ARROW ^INT
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
    """演示"""
    print("=" * 60)
    print("XC 语言编译器演示")
    print("=" * 60)

    print("\n原始 XC 代码:")
    print(SAMPLE_X_CODE)

    compiler = XCompiler("rust")
    print("\n编译为 Rust:")
    print(compiler.compile(SAMPLE_X_CODE))

    compiler = XCompiler("c")
    print("\n编译为 C:")
    print(compiler.compile(SAMPLE_X_CODE))

    compiler = XCompiler("mojo")
    print("\n编译为 Mojo:")
    print(compiler.compile(SAMPLE_X_CODE))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="XC 语言编译器")
    parser.add_argument("--input", "-i", type=str, help="输入文件 (.x)")
    parser.add_argument("--output", "-o", type=str, help="输出文件")
    parser.add_argument("--target", "-t", type=str, default="rust", choices=["rust", "c", "mojo"], help="目标语言")

    args = parser.parse_args()

    if args.input:
        compiler = XCompiler(args.target)
        result = compiler.compile_file(args.input, args.output)
        print(result)
    else:
        demo()
