"""
C ↔ Rust ↔ Mojo 三语语法映射表
C/Rust/Mojo 之间的语法对应关系定义
"""

GRAMMAR_MAPPING = {
    "variable_declaration": {
        "c": {"pattern": r"(\w+)\s+(\w+)\s*=", "example": "int x = 5;"},
        "rust": {"pattern": r"let\s+(?:mut\s+)?(\w+)\s*:\s*(\w+)\s*=", "example": "let x: i32 = 5;"},
        "mojo": {"pattern": r"var\s+(\w+)\s*:\s*(\w+)\s*=", "example": "var x: Int = 5"},
    },
    "function_definition": {
        "c": {"pattern": r"(\w+)\s+(\w+)\s*\(([^)]*)\)\s*{", "example": "int add(int a, int b) {"},
        "rust": {"pattern": r"fn\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\w+))?\s*{", "example": "fn add(a: i32, b: i32) -> i32 {"},
        "mojo": {"pattern": r"fn\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\w+))?\s*:", "example": "fn add(a: Int, b: Int) -> Int:"},
    },
    "struct_definition": {
        "c": {"pattern": r"typedef\s+struct\s+{([^}]*)}\s*(\w+);", "example": "typedef struct { int x; int y; } Point;"},
        "rust": {"pattern": r"struct\s+(\w+)\s*{([^}]*)}", "example": "struct Point { x: i32, y: i32 }"},
        "mojo": {"pattern": r"struct\s+(\w+)\s*:", "example": "struct Point:"},
    },
    "loop_for": {
        "c": {"pattern": r"for\s*\(\s*(\w+)\s+(\w+)\s*=\s*([^;]+);\s*([^;]+);\s*([^)]+)\)", "example": "for (int i = 0; i < 10; i++)"},
        "rust": {"pattern": r"for\s+(\w+)\s+in\s+([^;]+)\.\.(\??)([^)]+)", "example": "for i in 0..10"},
        "mojo": {"pattern": r"for\s+(\w+)\s+in\s+range\(([^)]+)\)", "example": "for i in range(10)"},
    },
    "loop_while": {
        "c": {"pattern": r"while\s*\(([^)]+)\)", "example": "while (x > 0)"},
        "rust": {"pattern": r"while\s+([^)]+)", "example": "while x > 0"},
        "mojo": {"pattern": r"while\s+([^:]+):", "example": "while x > 0:"},
    },
    "if_statement": {
        "c": {"pattern": r"if\s*\(([^)]+)\)", "example": "if (x > 0)"},
        "rust": {"pattern": r"if\s+([^)]+)", "example": "if x > 0"},
        "mojo": {"pattern": r"if\s+([^:]+):", "example": "if x > 0:"},
    },
    "pointer_reference": {
        "c": {"pattern": r"(\w+)\s*\*\s*(\w+)", "example": "int* ptr;"},
        "rust": {"pattern": r"(&mut\s+|&\s+)?(\w+)", "example": "&mut x or &x"},
        "mojo": {"pattern": r"(ref\s+)?(\w+)", "example": "ref x"},
    },
    "println": {
        "c": {"pattern": r'printf\s*\("([^"]*)"', "example": 'printf("%d\\n", x);'},
        "rust": {"pattern": r'println!\s*\("([^"]*)"', "example": 'println!("{}")'},
        "mojo": {"pattern": r'print\(', "example": 'print(x)'},
    },
}

TRANSLATION_RULES = {
    "c_to_rust": [
        ("int", "i32"),
        ("long", "i64"),
        ("short", "i16"),
        ("char", "i8"),
        ("unsigned int", "u32"),
        ("unsigned long", "u64"),
        ("float", "f32"),
        ("double", "f64"),
        ("bool", "bool"),
        ("void", "()"),
        ("NULL", "None"),
        ("malloc", "Box::new"),
        ("free", "drop"),
        ("struct", "struct"),
        ("typedef", ""),
        ("printf", "println!"),
        ("scanf", "readline"),
        ("for", "for"),
        ("while", "while"),
        ("if", "if"),
        ("else", "else"),
        ("return", "return"),
        ("switch", "match"),
        ("case", "_"),
    ],
    "rust_to_mojo": [
        ("i32", "Int"),
        ("i64", "Int"),
        ("f32", "Float32"),
        ("f64", "Float64"),
        ("bool", "Bool"),
        ("String", "String"),
        ("Vec", "List"),
        ("Option", "Optional"),
        ("Result", "raises"),
        ("Some", "Some"),
        ("None", "None"),
        ("let mut", "var"),
        ("let", "let"),
        ("fn", "fn"),
        ("->", "->"),
        ("impl", "struct"),
        ("pub fn", "fn"),
        ("&str", "String"),
        ("Box<T>", "Pointer[T]"),
        ("println!", "print"),
        ("vec!", "[]"),
        ("match", "match"),
        ("_", "_"),
    ],
    "c_to_mojo": [
        ("int", "Int"),
        ("float", "Float32"),
        ("double", "Float64"),
        ("char", "Int8"),
        ("long", "Int"),
        ("printf", "print"),
        ("scanf", "input"),
        ("struct", "struct"),
        ("typedef", ""),
        ("malloc", "alloc"),
        ("free", "free"),
    ],
    "mojo_to_c": [
        ("Int", "int"),
        ("Float64", "double"),
        ("Float32", "float"),
        ("String", "char*"),
        ("Bool", "int"),
        ("List", "T*"),
        ("struct", "struct"),
        ("fn", "void"),
        ("ref", "*"),
    ],
}

LANGUAGE_PATTERNS = {
    "c": {
        "comment_single": r"//.*?$",
        "comment_multi": r"/\*[\s\S]*?\*/",
        "string_literal": r'"(?:[^"\\]|\\.)*"',
        "preprocessor": r"#\s*\w+",
    },
    "rust": {
        "comment_single": r"//.*?$",
        "comment_multi": r"/\*[\s\S]*?\*/",
        "string_literal": r'"(?:[^"\\]|\\.)*"',
        "attribute": r"#\[.*?\]",
    },
    "mojo": {
        "comment_single": r"##.*?$",
        "comment_multi": r'"""[\s\S]*?"""',
        "string_literal": r'"(?:[^"\\]|\\.)*"',
        "decorator": r"@",
    },
}


def get_example_code_snippet(lang: str, category: str) -> str:
    """获取指定语言和类别的示例代码片段"""
    if category in GRAMMAR_MAPPING:
        return GRAMMAR_MAPPING[category].get(lang, {}).get("example", "")
    return ""


def get_type_mapping(from_lang: str, to_lang: str, c_type: str) -> str:
    """获取类型映射"""
    key = f"{from_lang}_to_{to_lang}"
    if key in TRANSLATION_RULES:
        for old, new in TRANSLATION_RULES[key]:
            if old == c_type:
                return new
    return c_type


def detect_language(code: str) -> str:
    """简单检测代码语言"""
    if "fn " in code and "let " in code and "->" in code:
        return "rust"
    if "def " in code or "fn " in code and ":" in code:
        return "mojo"
    if "#include" in code or "printf" in code:
        return "c"
    if "{" in code and "}" in code and ";" in code:
        return "c"
    return "unknown"
