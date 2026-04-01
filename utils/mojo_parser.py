"""
Mojo 代码语法分析工具
用于理解 Mojo 代码结构以便生成 Rust 对应代码
"""

import re
from typing import Dict, List, Optional, Tuple


class MojoParser:
    """Mojo 代码解析器"""

    KEYWORDS = {
        "fn", "struct", "var", "let", "if", "else", "elif", "for", "while",
        "return", "break", "continue", "pass", "True", "False", "None",
        "inout", "owned", "borrowed", "ref", "import", "from", "as",
    }

    TYPES = {
        "Int", "UInt", "Float32", "Float64", "Bool", "String", "List",
        "Dict", "Set", "Tuple", "Optional", "Pointer", "SIMD", "DType",
    }

    def __init__(self, code: str):
        self.code = code
        self.tokens = []
        self.ast = {}

    def tokenize(self) -> List[str]:
        """简单分词"""
        token_specification = [
            ("COMMENT", r"##.*?$"),
            ("MULTILINE_STRING", r'"""[\s\S]*?"""'),
            ("STRING", r'"(?:[^"\\]|\\.)*"'),
            ("NUMBER", r"\d+\.?\d*"),
            ("IDENTIFIER", r"[a-zA-Z_]\w*"),
            ("OPERATOR", r"[+\-*/%=<>!&|^~]+"),
            ("PUNCTUATION", r"[()\[\]{}:;,.]"),
            ("NEWLINE", r"\n"),
            ("SKIP", r"[ \t]+"),
        ]

        token_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in token_specification)
        token_pattern = re.compile(token_regex, re.MULTILINE)

        tokens = []
        for match in token_pattern.finditer(self.code):
            kind = match.lastgroup
            value = match.group()
            if kind not in ("SKIP", "NEWLINE"):
                tokens.append((kind, value))

        self.tokens = tokens
        return tokens

    def parse_struct(self) -> Dict:
        """解析 struct 定义"""
        struct_pattern = r"struct\s+(\w+)\s*(:.*?)?\n(.*?)(?=\n(?:struct|fn|@|\Z))"
        matches = re.finditer(struct_pattern, self.code, re.DOTALL)

        structs = []
        for match in matches:
            name = match.group(1)
            body = match.group(3)
            structs.append({
                "type": "struct",
                "name": name,
                "body": body.strip(),
                "raw": match.group(0),
            })

        return {"structs": structs}

    def parse_functions(self) -> List[Dict]:
        """解析函数定义"""
        fn_pattern = r"fn\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\w+))?\s*:(.*?)(?=\n(?:fn|struct|@|\Z))"
        matches = re.finditer(fn_pattern, self.code, re.DOTALL)

        functions = []
        for match in matches:
            name = match.group(1)
            params = match.group(2)
            return_type = match.group(3)
            body = match.group(4)

            functions.append({
                "type": "function",
                "name": name,
                "params": params.strip(),
                "return_type": return_type,
                "body": body.strip(),
                "raw": match.group(0),
            })

        return functions

    def extract_imports(self) -> List[str]:
        """提取 import 语句"""
        import_pattern = r"(?:from\s+(\w+)\s+)?import\s+(.+?)$"
        matches = re.finditer(import_pattern, self.code, re.MULTILINE)

        imports = []
        for match in matches:
            module = match.group(1) or ""
            items = match.group(2).strip()
            imports.append({
                "module": module,
                "items": items,
                "raw": match.group(0),
            })

        return imports

    def get_type_hints(self) -> Dict[str, str]:
        """提取所有类型提示"""
        type_pattern = r":\s*([A-Z]\w*)\s*(?=[,)=])"
        matches = re.finditer(type_pattern, self.code)

        types = {}
        for match in matches:
            type_name = match.group(1)
            if type_name in self.TYPES:
                types[match.start()] = type_name

        return types

    def analyze(self) -> Dict:
        """完整分析 Mojo 代码"""
        return {
            "imports": self.extract_imports(),
            "structs": self.parse_struct(),
            "functions": self.parse_functions(),
            "types": self.get_type_hints(),
        }


def mojo_to_rust_type(mojo_type: str) -> str:
    """Mojo 类型到 Rust 类型的映射"""
    type_map = {
        "Int": "i32",
        "UInt": "u32",
        "Float32": "f32",
        "Float64": "f64",
        "Bool": "bool",
        "String": "String",
        "List": "Vec",
        "Dict": "HashMap",
        "Set": "HashSet",
        "Optional": "Option",
        "Pointer": "Box",
    }
    return type_map.get(mojo_type, mojo_type.lower())


def mojo_to_rust_param(param: str) -> str:
    """转换 Mojo 参数为 Rust 格式"""
    param = param.strip()

    ownership = ""
    if "inout" in param:
        ownership = "&mut "
        param = param.replace("inout", "").strip()
    elif "borrowed" in param:
        ownership = "&"
        param = param.replace("borrowed", "").strip()
    elif "owned" in param:
        param = param.replace("owned", "").strip()

    if ":" in param:
        name, type_str = param.split(":", 1)
        type_str = type_str.strip()
        rust_type = mojo_to_rust_type(type_str)
        return f"{ownership}{name.strip()}: {rust_type}"

    return param


def convert_mojo_to_rust(mojo_code: str) -> str:
    """将 Mojo 代码转换为 Rust 代码"""
    parser = MojoParser(mojo_code)
    analysis = parser.analyze()

    rust_code = []

    if analysis["imports"]:
        for imp in analysis["imports"]:
            if "mojo" in imp.get("module", "").lower():
                continue

    for struct in analysis["structs"].get("structs", []):
        rust_code.append(f"struct {struct['name']} {{")
        for line in struct["body"].split("\n"):
            line = line.strip()
            if not line:
                continue
            if "var" in line or "let" in line:
                parts = line.replace("var", "").replace("let", "").strip().split(":")
                if len(parts) == 2:
                    name = parts[0].strip()
                    type_str = parts[1].replace("=", "").strip()
                    rust_type = mojo_to_rust_type(type_str)
                    rust_code.append(f"    {name}: {rust_type},")
        rust_code.append("}\n")

    for fn in analysis["functions"]:
        params = [mojo_to_rust_param(p) for p in fn["params"].split(",") if p.strip()]
        params_str = ", ".join(params)

        return_type = ""
        if fn["return_type"]:
            return_type = f" -> {mojo_to_rust_type(fn['return_type'])}"

        rust_code.append(f"fn {fn['name']}({params_str}){return_type} {{")
        for line in fn["body"].split("\n"):
            line = line.strip()
            if line:
                rust_code.append(f"    {line}")
        rust_code.append("}\n")

    return "\n".join(rust_code)


def validate_mojo_syntax(mojo_code: str) -> Tuple[bool, Optional[str]]:
    """验证 Mojo 代码语法"""
    errors = []

    fn_count = mojo_code.count("fn ")
    end_count = mojo_code.count(":")

    if fn_count > 0 and end_count < fn_count:
        errors.append("函数定义缺少 ':' 结尾")

    paren_open = mojo_code.count("(")
    paren_close = mojo_code.count(")")
    if paren_open != paren_close:
        errors.append("括号不匹配")

    if errors:
        return False, "; ".join(errors)
    return True, None
