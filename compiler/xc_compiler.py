"""
XC 语言编译器 V4（语法2 - 简化版）
将 XC 代码编译为 C / Rust / Mojo

语法规范：
    # { }                    程序入口
    $x = 10                  变量声明
    $x: int = 10            显式类型
    @PI = 3.14              常量
    % func(a: int) -> int  函数
    ^ expr                  返回
    ? (cond) { }            条件
    ?: { }                  else
    ?? (cond) { }           else if
    @ (cond) { }            while循环
    ~i=0; i<10; i=i+1 { }   for循环
    >                       break
    <                       continue
    ! x                     打印
    & Point { }             结构体
"""

import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum, auto

from xc_preprocess import (
    split_preprocessor_and_body,
    needs_stdlib_h,
    needs_string_h,
    needs_stdio_extra,
)


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int


class TokenType(Enum):
    MAIN = "MAIN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    SEMICOLON = "SEMICOLON"
    COLON = "COLON"
    COMMA = "COMMA"
    DOT = "DOT"
    ASSIGN = "ASSIGN"
    PLUSEQ = "PLUSEQ"
    MINUSEQ = "MINUSEQ"
    MULEQ = "MULEQ"
    DIVEQ = "DIVEQ"
    PLUSPLUS = "PLUSPLUS"
    MINUSMINUS = "MINUSMINUS"
    IDENT = "IDENT"
    NUMBER = "NUMBER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    PLUS = "PLUS"
    MINUS = "MINUS"
    MUL = "MUL"
    DIV = "DIV"
    MOD = "MOD"
    EQ = "EQ"
    NEQ = "NEQ"
    LT = "LT"
    GT = "GT"
    LTE = "LTE"
    GTE = "GTE"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    VAR = "VAR"
    CONST = "CONST"
    FUNC = "FUNC"
    STRUCT = "STRUCT"
    IF = "IF"
    ELSE = "ELSE"
    ELSE_IF = "ELSE_IF"
    WHILE = "WHILE"
    FOR = "FOR"
    BREAK = "BREAK"
    CONTINUE = "CONTINUE"
    RETURN = "RETURN"
    PRINT = "PRINT"
    INPUT_INT = "INPUT_INT"
    INPUT_STRING = "INPUT_STRING"
    TYPE_INT = "TYPE_INT"
    TYPE_FLOAT = "TYPE_FLOAT"
    TYPE_BOOL = "TYPE_BOOL"
    TYPE_STRING = "TYPE_STRING"
    TYPE_VOID = "TYPE_VOID"
    TRUE = "TRUE"
    FALSE = "FALSE"
    NEWLINE = "NEWLINE"
    COMMENT = "COMMENT"
    EOF = "EOF"
    AS = "AS"
    QUESTION = "QUESTION"
    ARROW = "ARROW"
    REF = "REF"
    ADDR_LPAREN = "ADDR_LPAREN"
    OMEGA = "OMEGA"
    SHL = "SHL"
    SHR = "SHR"
    BITAND_U = "BITAND_U"
    BITOR_U = "BITOR_U"
    BITXOR_U = "BITXOR_U"
    NOT_BIT = "NOT_BIT"
    UNION = "UNION"
    SWITCH = "SWITCH"
    CASE = "CASE"
    DEFAULT = "DEFAULT"
    GOTO = "GOTO"
    SECTION_LABEL = "SECTION_LABEL"
    SECTION_GOTO = "SECTION_GOTO"


KEYWORDS = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "return": TokenType.RETURN,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "int": TokenType.TYPE_INT,
    "float": TokenType.TYPE_FLOAT,
    "bool": TokenType.TYPE_BOOL,
    "string": TokenType.TYPE_STRING,
    "void": TokenType.TYPE_VOID,
    "as": TokenType.AS,
    "union": TokenType.UNION,
    "switch": TokenType.SWITCH,
    "case": TokenType.CASE,
    "default": TokenType.DEFAULT,
    "goto": TokenType.GOTO,
}


XC_SYMBOLS = {
    "#": TokenType.MAIN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    ";": TokenType.SEMICOLON,
    ":": TokenType.COLON,
    ",": TokenType.COMMA,
    ".": TokenType.DOT,
    "=": TokenType.ASSIGN,
    "+=": TokenType.PLUSEQ,
    "-=": TokenType.MINUSEQ,
    "*=": TokenType.MULEQ,
    "/=": TokenType.DIVEQ,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.MUL,
    "/": TokenType.DIV,
    "%": TokenType.MOD,
    "==": TokenType.EQ,
    "!=": TokenType.NEQ,
    "<": TokenType.LT,
    ">": TokenType.GT,
    "<=": TokenType.LTE,
    ">=": TokenType.GTE,
    "&&": TokenType.AND,
    "||": TokenType.OR,
    "!": TokenType.NOT,
    "?": TokenType.QUESTION,
    "??": TokenType.ELSE_IF,
    "?:": (TokenType.ELSE, TokenType.QUESTION),
    "^": TokenType.RETURN,
    "$": TokenType.VAR,
    "@": TokenType.CONST,
    "%": TokenType.FUNC,
    "&": TokenType.STRUCT,
    "->": TokenType.ARROW,
    "◎O": TokenType.PRINT,
    "◎I": TokenType.INPUT_INT,
    "◎S": TokenType.INPUT_STRING,
}


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"词法错误 ({line}:{column}): {message}")


class ParserError(Exception):
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"语法错误 ({line}:{column}): {message}")


class XCLexer:
    """XC 语言词法分析器"""

    TOKEN_PATTERNS = [
        ("MAIN", r"#\s*\{"),
        ("DEFAULT_MK", r"#\s*J\b"),
        ("CASE_MK", r"#\s*C\b"),
        ("SWITCH_MK", r"\?▶"),
        ("OMEGA", r"Ω[A-Z]"),
        ("ADDR_LPAREN", r"&\("),
        ("SECTION_GOTO", r"§g\b"),
        ("SECTION_LABEL", r"§l\b"),
        ("SHL", r"<<"),
        ("SHR", r">>"),
        ("BITAND_U", r"\u2227"),
        ("BITOR_U", r"\u2228"),
        ("BITXOR_U", r"\u2295"),
        ("NOT_BIT", r"\u00ac"),
        ("STRING", r'"([^"\\]|\\.)*"'),
        ("NUMBER", r"\d+\.\d+"),
        ("NUMBER", r"\d+"),
        ("IDENT", r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ("PLUSPLUS", r"\+\+"),
        ("MINUSMINUS", r"--"),
        ("PLUSEQ", r"\+="),
        ("MINUSEQ", r"-="),
        ("MULEQ", r"\*="),
        ("DIVEQ", r"/="),
        ("EQ", r"=="),
        ("NEQ", r"!="),
        ("LTE", r"<="),
        ("GTE", r">="),
        ("AND", r"&&"),
        ("OR", r"\|\|"),
        ("ELLIPSIS", r"\.\.\."),
        ("DOT", r"\."),
        ("COLONCOLON", r"::"),
        ("ARROW", r"->"),
        ("ELSE_IF", r"\?\?"),
        ("ELSE", r"\?\:"),
        ("PLUSEQ", r"\+="),
        ("ASSIGN", r"="),
        ("PLUS", r"\+"),
        ("MINUS", r"-"),
        ("MUL", r"\*"),
        ("DIV", r"/"),
        ("MOD", r"%"),
        ("LT", r"<"),
        ("GT", r">"),
        ("NOT", r"!"),
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("LBRACE", r"\{"),
        ("RBRACE", r"\}"),
        ("LBRACKET", r"\["),
        ("RBRACKET", r"\]"),
        ("COLON", r":"),
        ("SEMICOLON", r";"),
        ("COMMA", r","),
        ("QUESTION", r"\?"),
        ("HASH", r"#"),
        ("AMPERSAND", r"&"),
        ("AT", r"@"),
        ("DOLLAR", r"\$"),
        ("PERCENT", r"%"),
        ("CARET", r"\^"),
        ("FOR_MK", r"~"),
        ("NEWLINE", r"\n"),
        ("COMMENT", r"//.*|/\*[\s\S]*?\*/"),
        ("WHITESPACE", r"[ \t\r]+"),
    ]

    def __init__(self, code: str):
        self.code = code
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        """分词"""
        while self.pos < len(self.code):
            matched = False

            for token_type_str, pattern in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(self.code, self.pos)
                if match:
                    value = match.group()

                    if token_type_str not in ("WHITESPACE", "NEWLINE", "COMMENT"):
                        token_type = self._get_token_type(token_type_str, value)
                        self.tokens.append(Token(token_type, value, self.line, self.column))

                    if "\n" in value:
                        self.line += value.count("\n")
                        self.column = 1
                    else:
                        self.column += len(value)

                    self.pos = match.end()
                    matched = True
                    break

            if not matched:
                char = self.code[self.pos]
                raise LexerError(f"未知字符 '{char}'", self.line, self.column)

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    def _get_token_type(self, type_str: str, value: str) -> TokenType:
        """获取 token 类型"""
        if type_str == "MAIN":
            return TokenType.MAIN
        if type_str == "ADDR_LPAREN":
            return TokenType.ADDR_LPAREN
        if type_str == "OMEGA":
            return TokenType.OMEGA
        if type_str == "SHL":
            return TokenType.SHL
        if type_str == "SHR":
            return TokenType.SHR
        if type_str == "BITAND_U":
            return TokenType.BITAND_U
        if type_str == "BITOR_U":
            return TokenType.BITOR_U
        if type_str == "BITXOR_U":
            return TokenType.BITXOR_U
        if type_str == "NOT_BIT":
            return TokenType.NOT_BIT
        if type_str == "SWITCH_MK":
            return TokenType.SWITCH
        if type_str == "CASE_MK":
            return TokenType.CASE
        if type_str == "DEFAULT_MK":
            return TokenType.DEFAULT
        if type_str == "SECTION_LABEL":
            return TokenType.SECTION_LABEL
        if type_str == "SECTION_GOTO":
            return TokenType.SECTION_GOTO
        if type_str == "FOR_MK":
            return TokenType.FOR
        if type_str == "ELSE_IF":
            return TokenType.ELSE_IF
        if type_str == "ELSE" and value == "?:":
            return TokenType.ELSE
        if type_str == "PLUSPLUS":
            return TokenType.PLUSPLUS
        if type_str == "MINUSMINUS":
            return TokenType.MINUSMINUS
        if type_str == "PLUSEQ":
            return TokenType.PLUSEQ
        if type_str == "MINUSEQ":
            return TokenType.MINUSEQ
        if type_str == "MULEQ":
            return TokenType.MULEQ
        if type_str == "DIVEQ":
            return TokenType.DIVEQ
        if type_str == "LTE":
            return TokenType.LTE
        if type_str == "GTE":
            return TokenType.GTE
        if type_str == "EQ":
            return TokenType.EQ
        if type_str == "NEQ":
            return TokenType.NEQ
        if type_str == "AND":
            return TokenType.AND
        if type_str == "OR":
            return TokenType.OR
        if type_str == "ARROW":
            return TokenType.ARROW
        elif value == "#":
            return TokenType.MAIN
        elif value == "$":
            return TokenType.VAR
        elif value == "@":
            return TokenType.CONST
        elif value == "%":
            return TokenType.FUNC
        elif value == "&":
            return TokenType.STRUCT
        elif value == "^":
            return TokenType.RETURN
        elif value == "!":
            return TokenType.NOT
        elif value == "?":
            return TokenType.QUESTION
        elif value == "◎O":
            return TokenType.PRINT
        elif value == "◎I":
            return TokenType.INPUT_INT
        elif value == "◎S":
            return TokenType.INPUT_STRING
        elif value == "->":
            return TokenType.ARROW
        elif value == "||":
            return TokenType.OR
        elif value == "&&":
            return TokenType.AND
        elif value == "==":
            return TokenType.EQ
        elif value == "!=":
            return TokenType.NEQ
        elif value == "<=":
            return TokenType.LTE
        elif value == ">=":
            return TokenType.GTE
        elif value == "+=":
            return TokenType.PLUSEQ
        elif value == "-=":
            return TokenType.MINUSEQ
        elif value == "*=":
            return TokenType.MULEQ
        elif value == "/=":
            return TokenType.DIVEQ
        elif value == "++":
            return TokenType.PLUSPLUS
        elif value == "--":
            return TokenType.MINUSMINUS
        elif value == "+":
            return TokenType.PLUS
        elif value == "-":
            return TokenType.MINUS
        elif value == "*":
            return TokenType.MUL
        elif value == "/":
            return TokenType.DIV
        elif value == "%":
            return TokenType.MOD
        elif value == "<":
            return TokenType.LT
        elif value == ">":
            return TokenType.GT
        elif value == "{":
            return TokenType.LBRACE
        elif value == "}":
            return TokenType.RBRACE
        elif value == "(":
            return TokenType.LPAREN
        elif value == ")":
            return TokenType.RPAREN
        elif value == "[":
            return TokenType.LBRACKET
        elif value == "]":
            return TokenType.RBRACKET
        elif value == ":":
            return TokenType.COLON
        elif value == ";":
            return TokenType.SEMICOLON
        elif value == ",":
            return TokenType.COMMA
        elif value == ".":
            return TokenType.DOT
        elif value == "=":
            return TokenType.ASSIGN
        elif value == "?":
            return TokenType.QUESTION
        elif type_str == "IDENT":
            if value in KEYWORDS:
                return KEYWORDS[value]
            return TokenType.IDENT
        elif type_str == "NUMBER":
            if "." in value:
                return TokenType.FLOAT
            return TokenType.NUMBER
        elif type_str == "STRING":
            return TokenType.STRING
        else:
            return TokenType.IDENT


class ASTNode:
    """AST 节点基类"""
    pass


@dataclass
class Program(ASTNode):
    """程序节点"""
    body: List[ASTNode]


@dataclass
class VarDecl(ASTNode):
    """变量声明"""
    name: str
    var_type: Optional[str]
    value: Optional[ASTNode]
    is_const: bool = False


@dataclass
class FuncDef(ASTNode):
    """函数定义"""
    name: str
    params: List[Tuple[str, str]]
    return_type: Optional[str]
    body: List[ASTNode]


@dataclass
class StructDef(ASTNode):
    """结构体定义；字段 (名, 类型串, 位宽或 None)"""
    name: str
    fields: List[Tuple[str, str, Optional[int]]]


@dataclass
class UnionDef(ASTNode):
    """联合体定义"""
    name: str
    fields: List[Tuple[str, str]]


@dataclass
class SwitchStmt(ASTNode):
    """switch：若干 case + 可选 default"""
    expr: ASTNode
    cases: List[Tuple[ASTNode, List[ASTNode]]]
    default_body: Optional[List[ASTNode]]


@dataclass
class LabelStmt(ASTNode):
    """标号 §l name 或 C 风格 name:"""
    name: str


@dataclass
class GotoStmt(ASTNode):
    """goto / §g"""
    target: str


@dataclass
class IfStmt(ASTNode):
    """if 语句"""
    condition: ASTNode
    then_body: List[ASTNode]
    else_body: Optional[List[ASTNode]] = None
    else_if: Optional['IfStmt'] = None


@dataclass
class WhileStmt(ASTNode):
    """while 循环"""
    condition: ASTNode
    body: List[ASTNode]


@dataclass
class ForStmt(ASTNode):
    """for 循环"""
    init: Optional[ASTNode]
    condition: Optional[ASTNode]
    update: Optional[ASTNode]
    body: List[ASTNode]


@dataclass
class BreakStmt(ASTNode):
    """break 语句"""
    pass


@dataclass
class ContinueStmt(ASTNode):
    """continue 语句"""
    pass


@dataclass
class ReturnStmt(ASTNode):
    """return 语句"""
    value: Optional[ASTNode]


@dataclass
class PrintStmt(ASTNode):
    """打印语句"""
    args: List[ASTNode]


@dataclass
class InputStmt(ASTNode):
    """输入语句"""
    var_name: str
    input_type: str


@dataclass
class BinaryOp(ASTNode):
    """二元运算"""
    op: str
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOp(ASTNode):
    """一元运算"""
    op: str
    operand: ASTNode


@dataclass
class Call(ASTNode):
    """函数调用"""
    name: str
    args: List[ASTNode]


@dataclass
class IndexAccess(ASTNode):
    """数组/索引访问"""
    array: ASTNode
    index: ASTNode


@dataclass
class MemberAccess(ASTNode):
    """成员访问"""
    obj: ASTNode
    member: str


@dataclass
class StructInit(ASTNode):
    """结构体初始化"""
    struct_name: str
    fields: Dict[str, ASTNode]


@dataclass
class Identifier(ASTNode):
    """标识符"""
    name: str


@dataclass
class NumberLiteral(ASTNode):
    """数字字面量"""
    value: float


@dataclass
class StringLiteral(ASTNode):
    """字符串字面量"""
    value: str


@dataclass
class BoolLiteral(ASTNode):
    """布尔字面量"""
    value: bool


@dataclass
class ArrayLiteral(ASTNode):
    """数组字面量"""
    elements: List[ASTNode]


@dataclass
class TypeCast(ASTNode):
    """类型转换"""
    expr: ASTNode
    target_type: str


class XCParser:
    """XC 语言语法分析器"""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current = tokens[0] if tokens else Token(TokenType.EOF, "", 0, 0)

    def parse(self) -> Program:
        """解析程序"""
        body = []
        while not self._is_end():
            if self._match(TokenType.MAIN):
                self._advance()
                block_body = self._parse_block()
                if block_body:
                    body.extend(block_body)
                self._expect(TokenType.RBRACE)
            elif self._match(TokenType.FUNC):
                body.append(self._parse_function())
            elif self._match(TokenType.STRUCT):
                body.append(self._parse_struct())
            elif self._match(TokenType.UNION):
                body.append(self._parse_union())
            else:
                stmt = self._parse_statement()
                if stmt:
                    body.append(stmt)
        return Program(body=body)

    def _advance(self) -> Token:
        """前进到下一个 token"""
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current = self.tokens[self.pos]
        return self.tokens[self.pos - 1]

    def _peek(self, offset: int = 1) -> Token:
        """查看未来的 token"""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(TokenType.EOF, "", 0, 0)

    def _is_end(self) -> bool:
        """是否到达末尾"""
        return self.current.type == TokenType.EOF

    def _match(self, *types: TokenType) -> bool:
        """检查当前 token 类型"""
        for t in types:
            if self.current.type == t:
                return True
        return False

    def _expect(self, token_type: TokenType) -> Token:
        """期望指定类型的 token"""
        if self.current.type != token_type:
            raise ParserError(
                f"期望 {token_type}, 实际 {self.current.type}",
                self.current.line,
                self.current.column
            )
        return self._advance()

    def _parse_block(self) -> List[ASTNode]:
        """解析代码块"""
        stmts = []
        while not self._match(TokenType.RBRACE, TokenType.EOF):
            stmt = self._parse_statement()
            if stmt:
                stmts.append(stmt)
        return stmts

    def _parse_statement(self) -> Optional[ASTNode]:
        """解析语句"""
        if self._match(TokenType.SWITCH):
            return self._parse_switch()
        if self._match(TokenType.SECTION_LABEL):
            self._advance()
            if not self._match(TokenType.IDENT):
                raise ParserError("§l 后期望标号名", self.current.line, self.current.column)
            nm = self._advance().value
            if self._match(TokenType.SEMICOLON):
                self._advance()
            return LabelStmt(name=nm)
        if self._match(TokenType.SECTION_GOTO):
            self._advance()
            if not self._match(TokenType.IDENT):
                raise ParserError("§g 后期望目标名", self.current.line, self.current.column)
            nm = self._advance().value
            if self._match(TokenType.SEMICOLON):
                self._advance()
            return GotoStmt(target=nm)
        if self._match(TokenType.GOTO):
            self._advance()
            if not self._match(TokenType.IDENT):
                raise ParserError("goto 后期望标号", self.current.line, self.current.column)
            nm = self._advance().value
            if self._match(TokenType.SEMICOLON):
                self._advance()
            return GotoStmt(target=nm)
        if self._match(TokenType.VAR):
            return self._parse_var_decl()
        elif self._match(TokenType.CONST):
            var_decl = self._parse_var_decl()
            if isinstance(var_decl, VarDecl):
                var_decl.is_const = True
            return var_decl
        elif self._match(TokenType.IF):
            return self._parse_if()
        elif self._match(TokenType.QUESTION):
            if self._peek().type != TokenType.LPAREN:
                raise ParserError("? 作为 if 时后接 ( 条件 )", self.current.line, self.current.column)
            return self._parse_if()
        elif self._match(TokenType.WHILE):
            return self._parse_while()
        elif self._match(TokenType.FOR):
            return self._parse_for()
        elif self._match(TokenType.BREAK):
            self._advance()
            if self._match(TokenType.SEMICOLON):
                self._advance()
            return BreakStmt()
        elif self._match(TokenType.CONTINUE):
            self._advance()
            if self._match(TokenType.SEMICOLON):
                self._advance()
            return ContinueStmt()
        elif self._match(TokenType.GT):
            self._advance()
            if self._match(TokenType.SEMICOLON):
                self._advance()
            return BreakStmt()
        elif self._match(TokenType.LT):
            self._advance()
            if self._match(TokenType.SEMICOLON):
                self._advance()
            return ContinueStmt()
        elif self._match(TokenType.RETURN):
            return self._parse_return()
        elif self._match(TokenType.PRINT):
            return self._parse_print()
        elif self._match(TokenType.NOT):
            return self._parse_print()
        elif self._match(TokenType.INPUT_INT, TokenType.INPUT_STRING):
            return self._parse_input()
        elif self._match(TokenType.FUNC):
            return self._parse_function()
        elif self._match(TokenType.STRUCT):
            return self._parse_struct()
        elif self._match(TokenType.UNION):
            return self._parse_union()
        elif self._match(TokenType.IDENT):
            return self._parse_ident_statement()
        elif self._match(TokenType.SEMICOLON):
            self._advance()
            return None
        else:
            expr = self._parse_expression()
            if expr:
                if self._match(TokenType.ASSIGN):
                    self._advance()
                    value = self._parse_expression()
                    if isinstance(expr, Identifier):
                        return VarDecl(name=expr.name, var_type=None, value=value)
                elif self._match(TokenType.PLUSEQ, TokenType.MINUSEQ, TokenType.MULEQ, TokenType.DIVEQ):
                    op = self.current.value
                    self._advance()
                    value = self._parse_expression()
                    return VarDecl(
                        name=expr.name if isinstance(expr, Identifier) else str(expr),
                        var_type=None,
                        value=BinaryOp(op[:-1], expr, value)
                    )
            return expr

    def _parse_type_string(self) -> str:
        """解析类型串：可选 const/volatile、* 前缀、基类型名。"""
        quals: List[str] = []
        while self._match(TokenType.IDENT) and self.current.value in ("const", "volatile"):
            quals.append(self._advance().value)
        stars = ""
        while self._match(TokenType.MUL):
            self._advance()
            stars += "*"
        base = "int"
        if self._match(TokenType.TYPE_INT, TokenType.TYPE_FLOAT, TokenType.TYPE_BOOL,
                       TokenType.TYPE_STRING, TokenType.TYPE_VOID):
            base = self._advance().value
        elif self._match(TokenType.IDENT):
            base = self._advance().value
        core = stars + base
        if quals:
            return " ".join(quals) + " " + core
        return core

    def _parse_var_decl(self) -> VarDecl:
        """解析变量声明"""
        self._advance()
        if not self._match(TokenType.IDENT):
            raise ParserError("期望变量名", self.current.line, self.current.column)
        name = self._advance().value

        var_type = None
        if self._match(TokenType.COLON):
            self._advance()
            var_type = self._parse_type_string()

        value = None
        if self._match(TokenType.ASSIGN):
            self._advance()
            value = self._parse_expression()

        if self._match(TokenType.SEMICOLON):
            self._advance()

        return VarDecl(name=name, var_type=var_type, value=value)

    def _parse_function(self) -> FuncDef:
        """解析函数定义"""
        self._advance()
        if not self._match(TokenType.IDENT):
            raise ParserError("期望函数名", self.current.line, self.current.column)
        name = self._advance().value

        self._expect(TokenType.LPAREN)
        params = []
        while not self._match(TokenType.RPAREN):
            if self._match(TokenType.IDENT):
                param_name = self._advance().value
                param_type = "int"
                if self._match(TokenType.COLON):
                    self._advance()
                    param_type = self._parse_type_string()
                params.append((param_name, param_type))
            if self._match(TokenType.COMMA):
                self._advance()
        self._expect(TokenType.RPAREN)

        return_type = None
        if self._match(TokenType.ARROW):
            self._advance()
            return_type = self._parse_type_string()

        self._expect(TokenType.LBRACE)
        body = []
        while not self._match(TokenType.RBRACE):
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
        self._expect(TokenType.RBRACE)

        return FuncDef(name=name, params=params, return_type=return_type, body=body)

    def _parse_struct(self) -> StructDef:
        """解析结构体定义"""
        self._advance()
        if not self._match(TokenType.IDENT):
            raise ParserError("期望结构体名", self.current.line, self.current.column)
        name = self._advance().value

        self._expect(TokenType.LBRACE)
        fields: List[Tuple[str, str, Optional[int]]] = []
        while not self._match(TokenType.RBRACE):
            if self._match(TokenType.IDENT):
                field_name = self._advance().value
                self._expect(TokenType.COLON)
                field_type = self._parse_type_string()
                bits: Optional[int] = None
                if self._match(TokenType.COLON):
                    self._advance()
                    if self._match(TokenType.NUMBER):
                        bits = int(float(self._advance().value))
                fields.append((field_name, field_type, bits))
            if self._match(TokenType.SEMICOLON):
                self._advance()
        self._expect(TokenType.RBRACE)

        return StructDef(name=name, fields=fields)

    def _parse_union(self) -> UnionDef:
        """union Name { ... }"""
        self._advance()
        if not self._match(TokenType.IDENT):
            raise ParserError("期望联合体名", self.current.line, self.current.column)
        name = self._advance().value
        self._expect(TokenType.LBRACE)
        fields: List[Tuple[str, str]] = []
        while not self._match(TokenType.RBRACE):
            if self._match(TokenType.IDENT):
                field_name = self._advance().value
                self._expect(TokenType.COLON)
                field_type = self._parse_type_string()
                fields.append((field_name, field_type))
            if self._match(TokenType.SEMICOLON):
                self._advance()
        self._expect(TokenType.RBRACE)
        return UnionDef(name=name, fields=fields)

    def _parse_switch_section(self) -> List[ASTNode]:
        """switch 内 case/default 体，直到下一个 case/default/}"""
        stmts: List[ASTNode] = []
        while (
            not self._match(TokenType.RBRACE, TokenType.EOF)
            and not self._match(TokenType.CASE, TokenType.DEFAULT)
        ):
            st = self._parse_statement()
            if st:
                stmts.append(st)
        return stmts

    def _parse_switch(self) -> SwitchStmt:
        """switch (expr) { case ... default ... } 或 ?▶ (expr) { #C ... #J ... }"""
        self._advance()
        self._expect(TokenType.LPAREN)
        expr = self._parse_expression()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        cases: List[Tuple[ASTNode, List[ASTNode]]] = []
        default_body: Optional[List[ASTNode]] = None
        while not self._match(TokenType.RBRACE, TokenType.EOF):
            if self._match(TokenType.CASE):
                self._advance()
                cv = self._parse_expression()
                self._expect(TokenType.COLON)
                body = self._parse_switch_section()
                cases.append((cv, body))
            elif self._match(TokenType.DEFAULT):
                self._advance()
                self._expect(TokenType.COLON)
                default_body = self._parse_switch_section()
            else:
                raise ParserError(
                    "switch 内期望 case / #C 或 default / #J",
                    self.current.line,
                    self.current.column,
                )
        self._expect(TokenType.RBRACE)
        return SwitchStmt(expr=expr, cases=cases, default_body=default_body)

    def _parse_if(self) -> IfStmt:
        """解析 if 语句（if / ? (…) / ?? (…) else-if 链）"""
        if not self._match(TokenType.IF, TokenType.QUESTION, TokenType.ELSE_IF):
            raise ParserError("期望 if、? 或 ??", self.current.line, self.current.column)
        self._advance()
        self._expect(TokenType.LPAREN)
        condition = self._parse_expression()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        then_body = []
        while not self._match(TokenType.RBRACE):
            stmt = self._parse_statement()
            if stmt:
                then_body.append(stmt)
        self._expect(TokenType.RBRACE)

        else_body = None
        else_if = None

        if self._match(TokenType.ELSE_IF):
            else_if = self._parse_if()
        elif self._match(TokenType.ELSE):
            self._advance()
            self._expect(TokenType.LBRACE)
            else_body = []
            while not self._match(TokenType.RBRACE):
                stmt = self._parse_statement()
                if stmt:
                    else_body.append(stmt)
            self._expect(TokenType.RBRACE)

        return IfStmt(condition=condition, then_body=then_body,
                     else_body=else_body, else_if=else_if)

    def _parse_while(self) -> WhileStmt:
        """解析 while 循环"""
        self._advance()
        self._expect(TokenType.LPAREN)
        condition = self._parse_expression()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        body = []
        while not self._match(TokenType.RBRACE):
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
        self._expect(TokenType.RBRACE)

        return WhileStmt(condition=condition, body=body)

    def _parse_for(self) -> ForStmt:
        """解析 for 循环（C 风格 for(;;) 或 XC：~ i: int = 0; i < n; i++ {）"""
        self._advance()
        if self._match(TokenType.LPAREN):
            self._advance()
            init = None
            if not self._match(TokenType.SEMICOLON):
                if self._match(TokenType.IDENT):
                    name = self._advance().value
                    if self._match(TokenType.ASSIGN):
                        self._advance()
                        value = self._parse_expression()
                    else:
                        value = None
                    init = VarDecl(name=name, var_type=None, value=value)
                elif self._match(TokenType.VAR):
                    init = self._parse_var_decl()
            self._expect(TokenType.SEMICOLON)

            condition = None
            if not self._match(TokenType.SEMICOLON):
                condition = self._parse_expression()
            self._expect(TokenType.SEMICOLON)

            update = None
            if not self._match(TokenType.RPAREN):
                if self._match(TokenType.IDENT):
                    name = self._advance().value
                    if self._match(TokenType.PLUSEQ):
                        self._advance()
                        value = self._parse_expression()
                        update = VarDecl(name=name, var_type=None,
                                       value=BinaryOp("+", Identifier(name), value))
                    elif self._match(TokenType.MINUSEQ):
                        self._advance()
                        value = self._parse_expression()
                        update = VarDecl(name=name, var_type=None,
                                       value=BinaryOp("-", Identifier(name), value))
                    elif self._match(TokenType.ASSIGN):
                        self._advance()
                        value = self._parse_expression()
                        update = VarDecl(name=name, var_type=None, value=value)
                    elif self._match(TokenType.PLUSPLUS):
                        self._advance()
                        update = VarDecl(name=name, var_type=None,
                                       value=BinaryOp("+", Identifier(name), NumberLiteral(1)))
                    elif self._match(TokenType.MINUSMINUS):
                        self._advance()
                        update = VarDecl(name=name, var_type=None,
                                       value=BinaryOp("-", Identifier(name), NumberLiteral(1)))
                elif self._match(TokenType.PLUSPLUS):
                    self._advance()
                    name = self._peek(-1).value if self._peek(-1).type == TokenType.IDENT else "i"
                    update = VarDecl(name=name, var_type=None,
                                   value=BinaryOp("+", Identifier(name), NumberLiteral(1)))
                elif self._match(TokenType.MINUSMINUS):
                    self._advance()
                    name = self._peek(-1).value if self._peek(-1).type == TokenType.IDENT else "i"
                    update = VarDecl(name=name, var_type=None,
                                   value=BinaryOp("-", Identifier(name), NumberLiteral(1)))
            self._expect(TokenType.RPAREN)
        else:
            init = None
            if self._match(TokenType.VAR):
                init = self._parse_var_decl()
            elif self._match(TokenType.IDENT):
                name = self._advance().value
                if self._match(TokenType.COLON):
                    self._advance()
                    vt = self._parse_type_string()
                    val = None
                    if self._match(TokenType.ASSIGN):
                        self._advance()
                        val = self._parse_expression()
                    init = VarDecl(name=name, var_type=vt, value=val)
                elif self._match(TokenType.ASSIGN):
                    self._advance()
                    val = self._parse_expression()
                    init = VarDecl(name=name, var_type=None, value=val)
                else:
                    raise ParserError("for 初始化期望 : 类型 或 =", self.current.line, self.current.column)
                if self._match(TokenType.SEMICOLON):
                    self._advance()
            else:
                if not self._match(TokenType.SEMICOLON):
                    raise ParserError("for 期望初始化或 ;", self.current.line, self.current.column)
                self._advance()

            condition = None
            if not self._match(TokenType.SEMICOLON):
                condition = self._parse_expression()
            self._expect(TokenType.SEMICOLON)

            update = None
            if not self._match(TokenType.LBRACE):
                upd_expr = self._parse_expression()
                if upd_expr is not None:
                    update = upd_expr

        self._expect(TokenType.LBRACE)
        body = []
        while not self._match(TokenType.RBRACE):
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
        self._expect(TokenType.RBRACE)

        return ForStmt(init=init, condition=condition, update=update, body=body)

    def _parse_return(self) -> ReturnStmt:
        """解析 return 语句"""
        self._advance()
        value = None
        if not self._match(TokenType.SEMICOLON, TokenType.RBRACE):
            value = self._parse_expression()
        return ReturnStmt(value=value)

    def _parse_print(self) -> PrintStmt:
        """解析打印语句"""
        self._advance()
        args = []
        while not self._match(TokenType.SEMICOLON, TokenType.RBRACE, TokenType.NEWLINE):
            arg = self._parse_expression()
            if not arg:
                break
            args.append(arg)
            if self._match(TokenType.COMMA):
                self._advance()
            else:
                break
        if self._match(TokenType.SEMICOLON):
            self._advance()
        return PrintStmt(args=args)

    def _parse_input(self) -> InputStmt:
        """解析输入语句"""
        input_type = "int"
        if self.current.type == TokenType.INPUT_INT:
            input_type = "int"
        elif self.current.type == TokenType.INPUT_STRING:
            input_type = "string"
        self._advance()

        self._expect(TokenType.LPAREN)
        if not self._match(TokenType.IDENT):
            raise ParserError("期望变量名", self.current.line, self.current.column)
        var_name = self._advance().value
        self._expect(TokenType.RPAREN)

        if self._match(TokenType.SEMICOLON):
            self._advance()

        return InputStmt(var_name=var_name, input_type=input_type)

    def _parse_ident_statement(self) -> Optional[ASTNode]:
        """解析标识符开头的语句"""
        name = self.current.value
        self._advance()

        if self._match(TokenType.LPAREN):
            call_args = []
            self._advance()
            while not self._match(TokenType.RPAREN):
                arg = self._parse_expression()
                if arg:
                    call_args.append(arg)
                if self._match(TokenType.COMMA):
                    self._advance()
            self._expect(TokenType.RPAREN)
            if self._match(TokenType.SEMICOLON):
                self._advance()
            return Call(name=name, args=call_args)
        elif self._match(TokenType.ASSIGN):
            self._advance()
            value = self._parse_expression()
            if self._match(TokenType.SEMICOLON):
                self._advance()
            return VarDecl(name=name, var_type=None, value=value)
        elif self._match(TokenType.PLUSEQ, TokenType.MINUSEQ, TokenType.MULEQ, TokenType.DIVEQ):
            op = self.current.value
            self._advance()
            value = self._parse_expression()
            if self._match(TokenType.SEMICOLON):
                self._advance()
            return VarDecl(name=name, var_type=None, value=BinaryOp(op[:-1], Identifier(name), value))
        elif self._match(TokenType.PLUSPLUS, TokenType.MINUSMINUS):
            op = self.current.value
            self._advance()
            if self._match(TokenType.SEMICOLON):
                self._advance()
            return VarDecl(name=name, var_type=None,
                          value=BinaryOp(op[0], Identifier(name), NumberLiteral(1)))
        elif self._match(TokenType.DOT):
            self._advance()
            if not self._match(TokenType.IDENT):
                raise ParserError("期望成员名", self.current.line, self.current.column)
            member = self._advance().value
            if self._match(TokenType.ASSIGN):
                self._advance()
                value = self._parse_expression()
                return VarDecl(name=f"{name}.{member}", var_type=None, value=value)
            return MemberAccess(obj=Identifier(name), member=member)
        elif self._match(TokenType.LBRACKET):
            self._advance()
            index = self._parse_expression()
            self._expect(TokenType.RBRACKET)
            if self._match(TokenType.ASSIGN):
                self._advance()
                value = self._parse_expression()
                return VarDecl(name=name, var_type=None,
                             value=BinaryOp("=", IndexAccess(Identifier(name), index), value))
            return IndexAccess(array=Identifier(name), index=index)

        if self._match(TokenType.SEMICOLON):
            self._advance()
        return None

    def _parse_expression(self) -> Optional[ASTNode]:
        """解析表达式"""
        return self._parse_or()

    def _parse_or(self) -> Optional[ASTNode]:
        """解析 || 运算"""
        left = self._parse_and()
        while self._match(TokenType.OR):
            self._advance()
            right = self._parse_and()
            left = BinaryOp("||", left, right)
        return left

    def _parse_and(self) -> Optional[ASTNode]:
        """解析 && 运算"""
        left = self._parse_equality()
        while self._match(TokenType.AND):
            self._advance()
            right = self._parse_equality()
            left = BinaryOp("&&", left, right)
        return left

    def _parse_equality(self) -> Optional[ASTNode]:
        """解析 == != 运算"""
        left = self._parse_comparison()
        while self._match(TokenType.EQ, TokenType.NEQ):
            op = self._advance().value
            right = self._parse_comparison()
            left = BinaryOp(op, left, right)
        return left

    def _parse_comparison(self) -> Optional[ASTNode]:
        """解析 < > <= >= 运算"""
        left = self._parse_bitwise()
        while self._match(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self._advance().value
            right = self._parse_bitwise()
            left = BinaryOp(op, left, right)
        return left

    def _parse_bitwise(self) -> Optional[ASTNode]:
        """∧ ∨ ⊕ 与 << >>（∧ 等映射为 C 的 & | ^）"""
        left = self._parse_bitshift()
        while self._match(TokenType.BITAND_U, TokenType.BITOR_U, TokenType.BITXOR_U):
            tt = self.current.type
            self._advance()
            op = {TokenType.BITAND_U: "&", TokenType.BITOR_U: "|", TokenType.BITXOR_U: "^"}[tt]
            right = self._parse_bitshift()
            left = BinaryOp(op, left, right)
        return left

    def _parse_bitshift(self) -> Optional[ASTNode]:
        """<< >>"""
        left = self._parse_addition()
        while self._match(TokenType.SHL, TokenType.SHR):
            op = self._advance().value
            right = self._parse_addition()
            left = BinaryOp(op, left, right)
        return left

    def _parse_addition(self) -> Optional[ASTNode]:
        """解析 + - 运算"""
        left = self._parse_multiplication()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._parse_multiplication()
            left = BinaryOp(op, left, right)
        return left

    def _parse_multiplication(self) -> Optional[ASTNode]:
        """解析 * / % 运算"""
        left = self._parse_unary()
        while self._match(TokenType.MUL, TokenType.DIV, TokenType.MOD):
            op = self._advance().value
            right = self._parse_unary()
            left = BinaryOp(op, left, right)
        return left

    def _parse_unary(self) -> Optional[ASTNode]:
        """解析一元运算"""
        if self._match(TokenType.NOT):
            self._advance()
            operand = self._parse_unary()
            return UnaryOp("!", operand)
        if self._match(TokenType.NOT_BIT):
            self._advance()
            operand = self._parse_unary()
            return UnaryOp("~", operand)
        if self._match(TokenType.ADDR_LPAREN):
            self._advance()
            inner = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return UnaryOp("&", inner)
        if self._match(TokenType.MUL):
            self._advance()
            operand = self._parse_unary()
            return UnaryOp("*", operand)
        if self._match(TokenType.MINUS):
            self._advance()
            operand = self._parse_unary()
            return UnaryOp("-", operand)
        if self._match(TokenType.PLUSPLUS):
            self._advance()
            operand = self._parse_unary()
            if isinstance(operand, Identifier):
                return BinaryOp("+", operand, NumberLiteral(1))
            return operand
        if self._match(TokenType.MINUSMINUS):
            self._advance()
            operand = self._parse_unary()
            if isinstance(operand, Identifier):
                return BinaryOp("-", operand, NumberLiteral(1))
            return operand
        return self._parse_postfix()

    def _parse_postfix(self) -> Optional[ASTNode]:
        """解析后缀运算"""
        expr = self._parse_primary()

        while True:
            if self._match(TokenType.DOT):
                self._advance()
                if not self._match(TokenType.IDENT):
                    raise ParserError("期望成员名", self.current.line, self.current.column)
                member = self._advance().value
                expr = MemberAccess(obj=expr, member=member)
            elif self._match(TokenType.LBRACKET):
                self._advance()
                index = self._parse_expression()
                self._expect(TokenType.RBRACKET)
                expr = IndexAccess(array=expr, index=index)
            elif self._match(TokenType.LPAREN):
                self._advance()
                args = []
                while not self._match(TokenType.RPAREN):
                    arg = self._parse_expression()
                    if arg:
                        args.append(arg)
                    if self._match(TokenType.COMMA):
                        self._advance()
                self._expect(TokenType.RPAREN)
                expr = Call(name=expr.name if isinstance(expr, Identifier) else str(expr), args=args)
            elif self._match(TokenType.PLUSPLUS):
                self._advance()
                expr = UnaryOp("++post", expr)
            elif self._match(TokenType.MINUSMINUS):
                self._advance()
                expr = UnaryOp("--post", expr)
            else:
                break

        return expr

    def _parse_primary(self) -> Optional[ASTNode]:
        """解析基本表达式"""
        if self._match(TokenType.OMEGA):
            omega_c = {
                "ΩM": "malloc",
                "ΩF": "free",
                "ΩC": "calloc",
                "ΩR": "realloc",
            }
            raw = self._advance().value
            cname = omega_c.get(raw, "malloc")
            self._expect(TokenType.LPAREN)
            args: List[ASTNode] = []
            while not self._match(TokenType.RPAREN):
                a = self._parse_expression()
                if a:
                    args.append(a)
                if self._match(TokenType.COMMA):
                    self._advance()
            self._expect(TokenType.RPAREN)
            return Call(name=cname, args=args)

        if self._match(TokenType.NUMBER):
            value = self._advance().value
            return NumberLiteral(float(value))

        if self._match(TokenType.FLOAT):
            value = self._advance().value
            return NumberLiteral(float(value))

        if self._match(TokenType.STRING):
            value = self._advance().value
            return StringLiteral(value[1:-1])

        if self._match(TokenType.TRUE):
            self._advance()
            return BoolLiteral(True)

        if self._match(TokenType.FALSE):
            self._advance()
            return BoolLiteral(False)

        if self._match(TokenType.IDENT):
            name = self._advance().value
            return Identifier(name=name)

        if self._match(TokenType.LBRACKET):
            self._advance()
            elements = []
            while not self._match(TokenType.RBRACKET):
                elem = self._parse_expression()
                if elem:
                    elements.append(elem)
                if self._match(TokenType.COMMA):
                    self._advance()
            self._expect(TokenType.RBRACKET)
            return ArrayLiteral(elements=elements)

        if self._match(TokenType.LPAREN):
            self._advance()
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr

        if self._match(TokenType.AS):
            self._advance()
            if self._match(TokenType.IDENT, TokenType.TYPE_INT, TokenType.TYPE_FLOAT,
                          TokenType.TYPE_BOOL, TokenType.TYPE_STRING):
                target_type = self._advance().value
                operand = self._parse_unary()
                return TypeCast(expr=operand, target_type=target_type)

        return None


class CodeGenerator:
    """代码生成器"""

    def __init__(self, target: str = "c"):
        self.target = target

    def generate(self, ast: Program) -> str:
        """生成目标语言代码"""
        if self.target == "c":
            return self._generate_c(ast)
        elif self.target == "rust":
            return self._generate_rust(ast)
        elif self.target == "mojo":
            return self._generate_mojo(ast)
        return ""

    def _generate_c(self, ast: Program) -> str:
        """生成 C 代码"""
        lines = ["#include <stdio.h>", ""]

        has_main_func = any(isinstance(n, FuncDef) and n.name == "main" for n in ast.body)

        top_level_items = []
        main_body_items = []

        for node in ast.body:
            if isinstance(node, FuncDef):
                if has_main_func:
                    top_level_items.append(self._c_func_def(node))
                else:
                    top_level_items.append(self._c_func_def(node))
            elif isinstance(node, StructDef):
                top_level_items.append(self._c_struct_def(node))
            elif isinstance(node, UnionDef):
                top_level_items.append(self._c_union_def(node))
            elif isinstance(node, VarDecl):
                main_body_items.append(self._c_var_decl(node))
            elif isinstance(node, Call):
                main_body_items.append(self._c_expr(node) + ";")
            elif isinstance(node, PrintStmt):
                main_body_items.append(self._c_print(node))
            elif isinstance(node, InputStmt):
                main_body_items.append(self._c_input(node))
            elif isinstance(node, IfStmt):
                main_body_items.append(self._c_if(node))
            elif isinstance(node, WhileStmt):
                main_body_items.append(self._c_while(node))
            elif isinstance(node, ForStmt):
                main_body_items.append(self._c_for(node))
            elif isinstance(node, SwitchStmt):
                main_body_items.append(self._c_switch(node))
            elif isinstance(node, LabelStmt):
                main_body_items.append(self._c_stmt(node))
            elif isinstance(node, GotoStmt):
                main_body_items.append(self._c_stmt(node))
            elif isinstance(node, BreakStmt):
                main_body_items.append("break;")
            elif isinstance(node, ContinueStmt):
                main_body_items.append("continue;")
            elif isinstance(node, ReturnStmt):
                main_body_items.append(self._c_return(node))

        for item in top_level_items:
            lines.append(item)

        if not has_main_func:
            lines.append("")
            lines.append("int main() {")
            for item in main_body_items:
                if "\n" in item:
                    for ln in item.split("\n"):
                        lines.append("    " + ln)
                else:
                    lines.append("    " + item)
            lines.append("    return 0;")
            lines.append("}")

        return "\n".join(lines)

    def _generate_rust(self, ast: Program) -> str:
        """生成 Rust 代码"""
        lines = ["fn main() {"]

        for node in ast.body:
            if isinstance(node, FuncDef):
                continue
            elif isinstance(node, StructDef):
                lines.append("    " + self._rust_struct_def(node))
            elif isinstance(node, VarDecl):
                lines.append("    " + self._rust_var_decl(node))
            elif isinstance(node, PrintStmt):
                lines.append("    " + self._rust_print(node))
            elif isinstance(node, InputStmt):
                lines.append("    " + self._rust_input(node))
            elif isinstance(node, IfStmt):
                lines.append("    " + self._rust_if(node))
            elif isinstance(node, WhileStmt):
                lines.append("    " + self._rust_while(node))
            elif isinstance(node, ForStmt):
                lines.append("    " + self._rust_for(node))
            elif isinstance(node, BreakStmt):
                lines.append("    break;")
            elif isinstance(node, ContinueStmt):
                lines.append("    continue;")
            elif isinstance(node, ReturnStmt):
                lines.append("    " + self._rust_return(node))

        for node in ast.body:
            if isinstance(node, FuncDef):
                lines.append("")
                lines.append(self._rust_func_def(node))

        lines.append("}")
        return "\n".join(lines)

    def _generate_mojo(self, ast: Program) -> str:
        """生成 Mojo 代码"""
        lines = ["fn main():"]

        for node in ast.body:
            if isinstance(node, FuncDef):
                continue
            elif isinstance(node, StructDef):
                lines.append("    " + self._mojo_struct_def(node))
            elif isinstance(node, VarDecl):
                lines.append("    " + self._mojo_var_decl(node))
            elif isinstance(node, PrintStmt):
                lines.append("    " + self._mojo_print(node))
            elif isinstance(node, InputStmt):
                lines.append("    " + self._mojo_input(node))
            elif isinstance(node, IfStmt):
                lines.append("    " + self._mojo_if(node))
            elif isinstance(node, WhileStmt):
                lines.append("    " + self._mojo_while(node))
            elif isinstance(node, ForStmt):
                lines.append("    " + self._mojo_for(node))
            elif isinstance(node, BreakStmt):
                lines.append("    break")
            elif isinstance(node, ContinueStmt):
                lines.append("    continue")
            elif isinstance(node, ReturnStmt):
                lines.append("    " + self._mojo_return(node))

        for node in ast.body:
            if isinstance(node, FuncDef):
                lines.append("")
                lines.append(self._mojo_func_def(node))

        return "\n".join(lines)

    def _c_type(self, var_type: Optional[str]) -> str:
        """C 类型映射：支持 const/volatile、* 前缀指针。"""
        if not var_type:
            return "int"
        s = var_type.strip()
        if s.startswith("const "):
            return "const " + self._c_type(s[6:].strip())
        if s.startswith("volatile "):
            return "volatile " + self._c_type(s[9:].strip())
        n_star = 0
        while s.startswith("*"):
            n_star += 1
            s = s[1:].strip()
        type_map = {
            "int": "int",
            "float": "double",
            "bool": "int",
            "string": "char*",
            "void": "void",
        }
        base = type_map.get(s, s)
        return base + ("*" * n_star) if n_star else base

    def _rust_type(self, var_type: Optional[str]) -> str:
        """Rust 类型映射"""
        type_map = {
            "int": "i32",
            "float": "f64",
            "bool": "bool",
            "string": "String",
            "void": "()",
        }
        return type_map.get(var_type, "i32")

    def _mojo_type(self, var_type: Optional[str]) -> str:
        """Mojo 类型映射"""
        type_map = {
            "int": "Int",
            "float": "Float64",
            "bool": "Bool",
            "string": "String",
            "void": "None",
        }
        return type_map.get(var_type, "Int")

    def _c_expr(self, node: ASTNode) -> str:
        """C 表达式"""
        if isinstance(node, NumberLiteral):
            return str(int(node.value)) if node.value == int(node.value) else str(node.value)
        elif isinstance(node, StringLiteral):
            return f'"{node.value}"'
        elif isinstance(node, BoolLiteral):
            return "1" if node.value else "0"
        elif isinstance(node, Identifier):
            return node.name
        elif isinstance(node, BinaryOp):
            left = self._c_expr(node.left)
            right = self._c_expr(node.right)
            return f"({left} {node.op} {right})"
        elif isinstance(node, UnaryOp):
            operand = self._c_expr(node.operand)
            if node.op == "!":
                return f"(!{operand})"
            elif node.op == "-":
                return f"(-{operand})"
            elif node.op == "~":
                return f"(~{operand})"
            elif node.op == "*":
                return f"(*{operand})"
            elif node.op == "&":
                return f"(&{operand})"
            elif node.op == "++post":
                return f"{operand}++"
            elif node.op == "--post":
                return f"{operand}--"
            return operand
        elif isinstance(node, Call):
            args = ", ".join(self._c_expr(arg) for arg in node.args)
            return f"{node.name}({args})"
        elif isinstance(node, IndexAccess):
            return f"{self._c_expr(node.array)}[{self._c_expr(node.index)}]"
        elif isinstance(node, MemberAccess):
            return f"{self._c_expr(node.obj)}.{node.member}"
        elif isinstance(node, ArrayLiteral):
            return "{" + ", ".join(self._c_expr(e) for e in node.elements) + "}"
        elif isinstance(node, TypeCast):
            return f"(({self._c_type(node.target_type)}){self._c_expr(node.expr)})"
        return ""

    def _c_func_def(self, node: FuncDef) -> str:
        """C 函数定义"""
        params = ", ".join(f"{self._c_type(t)} {n}" for n, t in node.params)
        ret_type = self._c_type(node.return_type) if node.return_type else "void"
        body_lines: List[str] = []
        for stmt in node.body:
            if isinstance(stmt, VarDecl):
                body_lines.append(self._c_var_decl(stmt))
            elif isinstance(stmt, Call):
                body_lines.append(self._c_expr(stmt) + ";")
            elif isinstance(stmt, ReturnStmt):
                body_lines.append(self._c_return(stmt))
            elif isinstance(stmt, IfStmt):
                body_lines.append(self._c_if(stmt))
            elif isinstance(stmt, WhileStmt):
                body_lines.append(self._c_while(stmt))
            elif isinstance(stmt, ForStmt):
                body_lines.append(self._c_for(stmt))
            elif isinstance(stmt, PrintStmt):
                body_lines.append(self._c_print(stmt))
            elif isinstance(stmt, InputStmt):
                body_lines.append(self._c_input(stmt))
            elif isinstance(stmt, SwitchStmt):
                body_lines.append(self._c_switch(stmt))
            elif isinstance(stmt, LabelStmt):
                body_lines.append(self._c_stmt(stmt))
            elif isinstance(stmt, GotoStmt):
                body_lines.append(self._c_stmt(stmt))
            elif isinstance(stmt, BreakStmt):
                body_lines.append("break;")
            elif isinstance(stmt, ContinueStmt):
                body_lines.append("continue;")
        body = []
        for b in body_lines:
            if not b:
                continue
            if "\n" in b:
                for ln in b.split("\n"):
                    body.append(f"    {ln}")
            else:
                body.append(f"    {b}")
        if body and body[-1] and "return" not in body[-1]:
            body.append("    return 0;")
        return f"{ret_type} {node.name}({params}) {{\n" + "\n".join(body) + "\n}"

    def _c_struct_def(self, node: StructDef) -> str:
        """C 结构体定义（含可选位域）"""
        parts: List[str] = []
        for n, t, bits in node.fields:
            ct = self._c_type(t)
            if bits is not None:
                parts.append(f"{ct} {n} : {bits}")
            else:
                parts.append(f"{ct} {n}")
        fields = "; ".join(parts) + ";"
        return f"typedef struct {{ {fields} }} {node.name};"

    def _c_union_def(self, node: UnionDef) -> str:
        """C 联合体"""
        fields = "; ".join(f"{self._c_type(t)} {n}" for n, t in node.fields) + ";"
        return f"typedef union {{ {fields} }} {node.name};"

    def _c_switch(self, node: SwitchStmt) -> str:
        """C switch（case / #C；default / #J）"""
        lines = [f"switch ({self._c_expr(node.expr)}) {{"]
        for val, body in node.cases:
            lines.append(f"    case {self._c_expr(val)}:")
            for s in body:
                lines.append("        " + self._c_stmt(s))
            lines.append("        break;")
        if node.default_body:
            lines.append("    default:")
            for s in node.default_body:
                lines.append("        " + self._c_stmt(s))
        lines.append("}")
        return "\n".join(lines)

    def _c_var_decl(self, node: VarDecl) -> str:
        """C 变量声明"""
        var_type = self._c_type(node.var_type) if node.var_type else "int"
        value = self._c_expr(node.value) if node.value else "0"
        return f"{var_type} {node.name} = {value};"

    def _c_print(self, node: PrintStmt) -> str:
        """C 打印"""
        if not node.args:
            return 'printf("\\n");'
        formats = []
        args = []
        for arg in node.args:
            if isinstance(arg, StringLiteral) and "%" not in arg.value:
                formats.append("%s")
                args.append(f'"{arg.value}"')
            elif isinstance(arg, StringLiteral):
                formats.append(arg.value)
            else:
                formats.append("%d")
                args.append(self._c_expr(arg))
        fmt = " ".join(formats)
        args_str = ", ".join(args) if args else '""'
        if fmt.endswith("\\n"):
            return f'printf("{fmt}", {args_str});'.replace("\\\\n", "\\n")
        return f'printf("{fmt}\\n", {args_str});'

    def _c_input(self, node: InputStmt) -> str:
        """C 输入"""
        var_type = "int" if node.input_type == "int" else "s"
        fmt = "%d" if node.input_type == "int" else "%s"
        return f'scanf("{fmt}", &{node.var_name});'

    def _c_if(self, node: IfStmt) -> str:
        """C if 语句"""
        condition = self._c_expr(node.condition)
        then_body = "\n".join(f"    {self._c_stmt(s)}" for s in node.then_body)
        result = f"if ({condition}) {{\n{then_body}\n}}"
        if node.else_body:
            else_body = "\n".join(f"    {self._c_stmt(s)}" for s in node.else_body)
            result += f" else {{\n{else_body}\n}}"
        elif node.else_if:
            result += " else " + self._c_if(node.else_if)
        return result

    def _c_while(self, node: WhileStmt) -> str:
        """C while 循环"""
        condition = self._c_expr(node.condition)
        body = "\n".join(f"    {self._c_stmt(s)}" for s in node.body)
        return f"while ({condition}) {{\n{body}\n}}"

    def _c_for(self, node: ForStmt) -> str:
        """C for 循环"""
        if node.init is None:
            init = ";"
        elif isinstance(node.init, VarDecl):
            init = self._c_var_decl(node.init)
        else:
            init = self._c_expr(node.init) + ";"
        condition = (self._c_expr(node.condition) + ";") if node.condition else ";"
        if node.update is None:
            update = ""
        elif isinstance(node.update, VarDecl) and node.update.value:
            update = f"{node.update.name} = {self._c_expr(node.update.value)}"
        elif isinstance(node.update, VarDecl):
            update = node.update.name
        else:
            update = self._c_expr(node.update)
        body = "\n".join(f"    {self._c_stmt(s)}" for s in node.body)
        return f"for ({init} {condition} {update}) {{\n{body}\n}}"

    def _c_return(self, node: ReturnStmt) -> str:
        """C return"""
        if node.value:
            return f"return {self._c_expr(node.value)};"
        return "return 0;"

    def _c_stmt(self, node: ASTNode) -> str:
        """C 语句"""
        if isinstance(node, VarDecl):
            return self._c_var_decl(node)
        elif isinstance(node, Call):
            return self._c_expr(node) + ";"
        elif isinstance(node, PrintStmt):
            return self._c_print(node)
        elif isinstance(node, IfStmt):
            return self._c_if(node)
        elif isinstance(node, WhileStmt):
            return self._c_while(node)
        elif isinstance(node, ForStmt):
            return self._c_for(node)
        elif isinstance(node, BreakStmt):
            return "break;"
        elif isinstance(node, ContinueStmt):
            return "continue;"
        elif isinstance(node, ReturnStmt):
            return self._c_return(node)
        elif isinstance(node, SwitchStmt):
            return self._c_switch(node)
        elif isinstance(node, LabelStmt):
            return f"{node.name}:"
        elif isinstance(node, GotoStmt):
            return f"goto {node.target};"
        return ""

    def _rust_expr(self, node: ASTNode) -> str:
        """Rust 表达式"""
        if isinstance(node, NumberLiteral):
            val = int(node.value) if node.value == int(node.value) else node.value
            return str(val)
        elif isinstance(node, StringLiteral):
            return f'"{node.value}"'
        elif isinstance(node, BoolLiteral):
            return "true" if node.value else "false"
        elif isinstance(node, Identifier):
            return node.name
        elif isinstance(node, BinaryOp):
            left = self._rust_expr(node.left)
            right = self._rust_expr(node.right)
            return f"({left} {node.op} {right})"
        elif isinstance(node, UnaryOp):
            operand = self._rust_expr(node.operand)
            if node.op == "!":
                return f"(!{operand})"
            elif node.op == "-":
                return f"(-{operand})"
            elif node.op == "++post":
                return f"({operand} + 1)"
            elif node.op == "--post":
                return f"({operand} - 1)"
            return operand
        elif isinstance(node, Call):
            args = ", ".join(self._rust_expr(arg) for arg in node.args)
            return f"{node.name}({args})"
        elif isinstance(node, IndexAccess):
            return f"{self._rust_expr(node.array)}[{self._rust_expr(node.index)}]"
        elif isinstance(node, MemberAccess):
            return f"{self._rust_expr(node.obj)}.{node.member}"
        elif isinstance(node, ArrayLiteral):
            return "vec![" + ", ".join(self._rust_expr(e) for e in node.elements) + "]"
        elif isinstance(node, TypeCast):
            return f"{self._rust_expr(node.expr)} as {self._rust_type(node.target_type)}"
        return ""

    def _rust_func_def(self, node: FuncDef) -> str:
        """Rust 函数定义"""
        params = ", ".join(f"{n}: {self._rust_type(t)}" for n, t in node.params)
        ret = f" -> {self._rust_type(node.return_type)}" if node.return_type else ""
        body = []
        for stmt in node.body:
            if isinstance(stmt, VarDecl):
                body.append(f"let {stmt.name} = {self._rust_expr(stmt.value)};")
            elif isinstance(stmt, Call):
                body.append(f"{self._rust_expr(stmt)};")
            elif isinstance(stmt, ReturnStmt):
                body.append(f"return {self._rust_expr(stmt.value)};" if stmt.value else "return;")
            elif isinstance(stmt, IfStmt):
                body.append(self._rust_if(stmt))
        return f"fn {node.name}({params}){ret} {{\n    " + "\n    ".join(body) + "\n}"

    def _rust_struct_def(self, node: StructDef) -> str:
        """Rust 结构体定义"""
        fields = ", ".join(f"{n}: {self._rust_type(t)}" for n, t, _ in node.fields)
        return f"struct {node.name} {{ {fields} }}"

    def _rust_var_decl(self, node: VarDecl) -> str:
        """Rust 变量声明"""
        var_type = f": {self._rust_type(node.var_type)}" if node.var_type else ""
        value = self._rust_expr(node.value) if node.value else "()"
        return f"let {node.name}{var_type} = {value};"

    def _rust_print(self, node: PrintStmt) -> str:
        """Rust 打印"""
        if not node.args:
            return 'println!("");'
        args = []
        fmt_parts = []
        for arg in node.args:
            if isinstance(arg, StringLiteral):
                fmt_parts.append(arg.value)
                args.append(f'"{arg.value}"')
            else:
                fmt_parts.append("{}")
                args.append(self._rust_expr(arg))
        fmt = " ".join(fmt_parts)
        args_str = ", ".join(args) if args else ""
        return f'println!("{fmt}", {args_str});'

    def _rust_input(self, node: InputStmt) -> str:
        """Rust 输入"""
        return f'let mut input = String::new(); io::stdin().read_line(&mut input).unwrap();'

    def _rust_if(self, node: IfStmt) -> str:
        """Rust if 语句"""
        condition = self._rust_expr(node.condition)
        then_body = "\n    ".join(self._rust_stmt(s) for s in node.then_body)
        result = f"if {condition} {{\n    {then_body}\n}}"
        if node.else_body:
            else_body = "\n    ".join(self._rust_stmt(s) for s in node.else_body)
            result += f" else {{\n    {else_body}\n}}"
        elif node.else_if:
            result += " else " + self._rust_if(node.else_if)
        return result

    def _rust_while(self, node: WhileStmt) -> str:
        """Rust while 循环"""
        condition = self._rust_expr(node.condition)
        body = "\n    ".join(self._rust_stmt(s) for s in node.body)
        return f"while {condition} {{\n    {body}\n}}"

    def _rust_for(self, node: ForStmt) -> str:
        """Rust for 循环"""
        if node.init and isinstance(node.init, VarDecl):
            var_name = node.init.name
            start = self._rust_expr(node.init.value) if node.init.value else "0"
            end = self._rust_expr(node.condition) if node.condition else "10"
            update = self._rust_expr(node.update) if node.update else ""
            if isinstance(node.update, VarDecl) and isinstance(node.update.value, BinaryOp):
                if node.update.value.op == "+":
                    end = f"{int(float(end))+1}.."
                elif node.update.value.op == "-":
                    end = f"0..={end}"
            body = "\n    ".join(self._rust_stmt(s) for s in node.body)
            return f"for {var_name} in {start}..={end} {{\n    {body}\n}}"
        body = "\n    ".join(self._rust_stmt(s) for s in node.body)
        init = self._rust_expr(node.init) + ";" if node.init else ""
        condition = self._rust_expr(node.condition) + ";" if node.condition else ";"
        update = self._rust_expr(node.update) if node.update else ""
        return f"for {init} {condition} {update} {{\n    {body}\n}}"

    def _rust_return(self, node: ReturnStmt) -> str:
        """Rust return"""
        if node.value:
            return f"return {self._rust_expr(node.value)};"
        return "return;"

    def _rust_stmt(self, node: ASTNode) -> str:
        """Rust 语句"""
        if isinstance(node, VarDecl):
            return self._rust_var_decl(node)
        elif isinstance(node, Call):
            return self._rust_expr(node) + ";"
        elif isinstance(node, PrintStmt):
            return self._rust_print(node)
        elif isinstance(node, IfStmt):
            return self._rust_if(node)
        elif isinstance(node, WhileStmt):
            return self._rust_while(node)
        elif isinstance(node, ForStmt):
            return self._rust_for(node)
        elif isinstance(node, BreakStmt):
            return "break;"
        elif isinstance(node, ContinueStmt):
            return "continue;"
        elif isinstance(node, ReturnStmt):
            return self._rust_return(node)
        return ""

    def _mojo_expr(self, node: ASTNode) -> str:
        """Mojo 表达式"""
        if isinstance(node, NumberLiteral):
            val = int(node.value) if node.value == int(node.value) else node.value
            return str(val)
        elif isinstance(node, StringLiteral):
            return f'"{node.value}"'
        elif isinstance(node, BoolLiteral):
            return "True" if node.value else "False"
        elif isinstance(node, Identifier):
            return node.name
        elif isinstance(node, BinaryOp):
            left = self._mojo_expr(node.left)
            right = self._mojo_expr(node.right)
            op = node.op
            if op == "&&":
                op = "and"
            elif op == "||":
                op = "or"
            elif op == "==":
                op = "=="
            elif op == "!=":
                op = "!="
            return f"({left} {op} {right})"
        elif isinstance(node, UnaryOp):
            operand = self._mojo_expr(node.operand)
            if node.op == "!":
                return f"not {operand}"
            elif node.op == "-":
                return f"(-{operand})"
            elif node.op == "++post":
                return f"({operand} + 1)"
            elif node.op == "--post":
                return f"({operand} - 1)"
            return operand
        elif isinstance(node, Call):
            args = ", ".join(self._mojo_expr(arg) for arg in node.args)
            return f"{node.name}({args})"
        elif isinstance(node, IndexAccess):
            return f"{self._mojo_expr(node.array)}[{self._mojo_expr(node.index)}]"
        elif isinstance(node, MemberAccess):
            return f"{self._mojo_expr(node.obj)}.{node.member}"
        elif isinstance(node, ArrayLiteral):
            return "[" + ", ".join(self._mojo_expr(e) for e in node.elements) + "]"
        elif isinstance(node, TypeCast):
            return f"int({self._mojo_expr(node.expr)})"
        return ""

    def _mojo_func_def(self, node: FuncDef) -> str:
        """Mojo 函数定义"""
        params = ", ".join(f"{n}: {self._mojo_type(t)}" for n, t in node.params)
        ret = f" -> {self._mojo_type(node.return_type)}" if node.return_type else ""
        body = []
        for stmt in node.body:
            if isinstance(stmt, VarDecl):
                body.append(f"var {stmt.name} = {self._mojo_expr(stmt.value)}")
            elif isinstance(stmt, Call):
                body.append(self._mojo_expr(stmt))
            elif isinstance(stmt, ReturnStmt):
                body.append(f"return {self._mojo_expr(stmt.value)}" if stmt.value else "return")
            elif isinstance(stmt, IfStmt):
                body.append(self._mojo_if(stmt))
            elif isinstance(stmt, WhileStmt):
                body.append(self._mojo_while(stmt))
            elif isinstance(stmt, ForStmt):
                body.append(self._mojo_for(stmt))
        return f"fn {node.name}({params}){ret}:\n    " + "\n    ".join(body)

    def _mojo_struct_def(self, node: StructDef) -> str:
        """Mojo 结构体定义"""
        fields = "\n    ".join(f"var {n}: {self._mojo_type(t)}" for n, t, _ in node.fields)
        return f"struct {node.name}:\n    {fields}"

    def _mojo_var_decl(self, node: VarDecl) -> str:
        """Mojo 变量声明"""
        var_type = f": {self._mojo_type(node.var_type)}" if node.var_type else ""
        value = self._mojo_expr(node.value) if node.value else "0"
        return f"var {node.name}{var_type} = {value}"

    def _mojo_print(self, node: PrintStmt) -> str:
        """Mojo 打印"""
        if not node.args:
            return 'print("")'
        args = []
        for arg in node.args:
            args.append(self._mojo_expr(arg))
        return f"print({', '.join(args)})"

    def _mojo_input(self, node: InputStmt) -> str:
        """Mojo 输入"""
        return f'let {node.var_name} = input()'

    def _mojo_if(self, node: IfStmt) -> str:
        """Mojo if 语句"""
        condition = self._mojo_expr(node.condition)
        then_body = "\n    ".join(self._mojo_stmt(s) for s in node.then_body)
        result = f"if {condition}:\n    {then_body}"
        if node.else_body:
            else_body = "\n    ".join(self._mojo_stmt(s) for s in node.else_body)
            result += f"\nelse:\n    {else_body}"
        elif node.else_if:
            result += "\n" + self._mojo_if(node.else_if)
        return result

    def _mojo_while(self, node: WhileStmt) -> str:
        """Mojo while 循环"""
        condition = self._mojo_expr(node.condition)
        body = "\n    ".join(self._mojo_stmt(s) for s in node.body)
        return f"while {condition}:\n    {body}"

    def _mojo_for(self, node: ForStmt) -> str:
        """Mojo for 循环"""
        if node.init and isinstance(node.init, VarDecl):
            var_name = node.init.name
            start = self._mojo_expr(node.init.value) if node.init.value else "0"
            end = self._mojo_expr(node.condition) if node.condition else "10"
            body = "\n    ".join(self._mojo_stmt(s) for s in node.body)
            return f"for {var_name} in range({start}, {end}):\n    {body}"
        body = "\n    ".join(self._mojo_stmt(s) for s in node.body)
        init = self._mojo_expr(node.init) if node.init else ""
        condition = self._mojo_expr(node.condition) if node.condition else ""
        update = self._mojo_expr(node.update) if node.update else ""
        return f"for {init}; {condition}; {update}:\n    {body}"

    def _mojo_return(self, node: ReturnStmt) -> str:
        """Mojo return"""
        if node.value:
            return f"return {self._mojo_expr(node.value)}"
        return "return"

    def _mojo_stmt(self, node: ASTNode) -> str:
        """Mojo 语句"""
        if isinstance(node, VarDecl):
            return self._mojo_var_decl(node)
        elif isinstance(node, Call):
            return self._mojo_expr(node)
        elif isinstance(node, PrintStmt):
            return self._mojo_print(node)
        elif isinstance(node, IfStmt):
            return self._mojo_if(node)
        elif isinstance(node, WhileStmt):
            return self._mojo_while(node)
        elif isinstance(node, ForStmt):
            return self._mojo_for(node)
        elif isinstance(node, BreakStmt):
            return "break"
        elif isinstance(node, ContinueStmt):
            return "continue"
        elif isinstance(node, ReturnStmt):
            return self._mojo_return(node)
        return ""


class XCCompiler:
    """XC 语言编译器主类"""

    def __init__(self, target: str = "c"):
        self.target = target

    def _finalize_c_output(self, prep_lines: List[str], c_out: str) -> str:
        """在 C 输出前拼接预处理行，并按需插入 stdlib/string 头文件。"""
        heads = "\n".join(prep_lines)
        blob = heads + "\n" + c_out
        extras: List[str] = []
        if needs_stdlib_h(blob) and "stdlib.h" not in heads and "stdlib.h" not in c_out[:1200]:
            extras.append("#include <stdlib.h>")
        if needs_string_h(blob) and "string.h" not in heads:
            extras.append("#include <string.h>")
        front = extras + prep_lines
        if not front:
            return c_out
        return "\n".join(front) + "\n\n" + c_out

    def _prepend_prep_as_comments(self, prep_lines: List[str], out: str) -> str:
        if not prep_lines:
            return out
        cmt = "\n".join("// [prep] " + p.strip() for p in prep_lines if p.strip())
        return cmt + "\n" + out

    def compile(self, xc_code: str) -> str:
        """编译 XC 代码"""
        if self.target in ("asm_riscv64", "asm", "riscv64"):
            from xc_asm_oracle import compile_xc_to_asm_riscv64

            return compile_xc_to_asm_riscv64(xc_code)
        prep_lines, body = split_preprocessor_and_body(xc_code)
        lexer = XCLexer(body)
        tokens = lexer.tokenize()
        parser = XCParser(tokens)
        ast = parser.parse()
        generator = CodeGenerator(self.target)
        out = generator.generate(ast)
        if self.target == "c":
            return self._finalize_c_output(prep_lines, out)
        return self._prepend_prep_as_comments(prep_lines, out)

    def compile_file(self, input_path: str, output_path: str = None) -> str:
        """编译文件"""
        with open(input_path, "r", encoding="utf-8") as f:
            xc_code = f.read()

        result = self.compile(xc_code)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)

        return result


def compile_xc(xc_code: str, target: str = "c") -> str:
    """快捷编译函数。target 含 asm_riscv64 / riscv64 时走 RISC-V64 Oracle（无 C 中间层）。"""
    compiler = XCCompiler(target)
    return compiler.compile(xc_code)


def demo():
    """演示"""
    print("=" * 60)
    print("XC 语言编译器 V4 演示")
    print("=" * 60)

    xc_code = """# {
    $x: int = 10
    $y: int = 20
    $sum: int = x + y
    ! "x + y = ", sum

    % add(a: int, b: int) -> int {
        ^ a + b
    }

    ! add(3, 5)

    ? (x > y) {
        ! "x > y"
    } ?: {
        ! "x <= y"
    }

    ~i: int = 0; i < 5; i++ {
        ! i
    }
}"""

    print("\n原始 XC 代码:")
    print(xc_code)

    print("\n" + "-" * 40)
    print("编译为 C:")
    print("-" * 40)
    print(compile_xc(xc_code, "c"))

    print("\n" + "-" * 40)
    print("编译为 Rust:")
    print("-" * 40)
    print(compile_xc(xc_code, "rust"))

    print("\n" + "-" * 40)
    print("编译为 Mojo:")
    print("-" * 40)
    print(compile_xc(xc_code, "mojo"))


if __name__ == "__main__":
    demo()
