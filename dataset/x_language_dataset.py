"""
XC ↔ C ↔ Rust ↔ Mojo 四语配对数据集生成器

生成用于训练三语互译模型的数据集
"""

import json
import random
from typing import List, Dict, Optional
from pathlib import Path


X_TEMPLATE_SAMPLES = [
    {
        "x": """!FUNC add !LPAREN a ^INT !COMMA b ^INT !RPAREN !ARROW ^INT
!LBRACE
    !RETURN a !ADD b
!RBRACE""",
        "c": """int add(int a, int b) {
    return a + b;
}""",
        "rust": """fn add(a: i32, b: i32) -> i32 {
    a + b
}""",
        "mojo": """fn add(a: Int, b: Int) -> Int:
    return a + b""",
    },
    {
        "x": """!VAR x ^INT !ASSIGN !NUMBER 10
!VAR y ^INT !ASSIGN !NUMBER 20
!VAR sum ^INT !ASSIGN x !ADD y
!PRINT sum""",
        "c": """int x = 10;
int y = 20;
int sum = x + y;
printf("%d\\n", sum);""",
        "rust": """let x: i32 = 10;
let y: i32 = 20;
let sum: i32 = x + y;
println!("{}", sum);""",
        "mojo": """var x: Int = 10
var y: Int = 20
var sum: Int = x + y
print(sum)""",
    },
    {
        "x": """!FUNC factorial !LPAREN n ^INT !RPAREN !ARROW ^INT
!LBRACE
    !IF n !LESS !NUMBER 2
    !LBRACE
        !RETURN !NUMBER 1
    !RBRACE
    !RETURN n !MUL !FUNC factorial !LPAREN n !SUB !NUMBER 1 !RPAREN
!RBRACE""",
        "c": """int factorial(int n) {
    if (n < 2) {
        return 1;
    }
    return n * factorial(n - 1);
}""",
        "rust": """fn factorial(n: i32) -> i32 {
    if n < 2 {
        return 1;
    }
    n * factorial(n - 1)
}""",
        "mojo": """fn factorial(n: Int) -> Int:
    if n < 2:
        return 1
    return n * factorial(n - 1)""",
    },
    {
        "x": """!STRUCT Point
!LBRACE
    x ^INT SEMICOLON
    y ^INT SEMICOLON
!RBRACE""",
        "c": """typedef struct {
    int x;
    int y;
} Point;""",
        "rust": """struct Point {
    x: i32,
    y: i32,
}""",
        "mojo": """struct Point:
    var x: Int
    var y: Int""",
    },
    {
        "x": """!FUNC is_prime !LPAREN n ^INT !RPAREN !ARROW ^BOOL
!LBRACE
    !IF n !LESS !NUMBER 2
    !LBRACE
        !RETURN !FALSE
    !RBRACE
    !VAR i ^INT !ASSIGN !NUMBER 2
    !LOOP i !LBRACKET n !RBRACKET
    !LBRACE
        !IF n !MOD i !EQUAL !NUMBER 0
        !LBRACE
            !RETURN !FALSE
        !RBRACE
        !RETURN !TRUE
    !RBRACE
!RBRACE""",
        "c": """int is_prime(int n) {
    if (n < 2) {
        return 0;
    }
    for (int i = 2; i < n; i++) {
        if (n % i == 0) {
            return 0;
        }
    }
    return 1;
}""",
        "rust": """fn is_prime(n: i32) -> bool {
    if n < 2 {
        return false;
    }
    for i in 2..n {
        if n % i == 0 {
            return false;
        }
    }
    true
}""",
        "mojo": """fn is_prime(n: Int) -> Bool:
    if n < 2:
        return False
    for i in range(2, n):
        if n % i == 0:
            return False
    return True""",
    },
]


ALGORITHM_TEMPLATES = [
    {
        "name": "冒泡排序",
        "x": """!FUNC bubble_sort !LPAREN arr !LBRACKET !RBRACKET !COMMA n ^INT !RPAREN
!LBRACE
    !VAR i ^INT !ASSIGN !NUMBER 0
    !LOOP i !LESS n !SUB !NUMBER 1
    !LBRACE
        !VAR j ^INT !ASSIGN !NUMBER 0
        !LOOP j !LESS n !SUB i !SUB !NUMBER 1
        !LBRACE
            !IF arr !LBRACKET j !RBRACKET !GREATER arr !LBRACKET j !ADD !NUMBER 1 !RBRACKET
            !LBRACE
                !VAR temp ^INT !ASSIGN arr !LBRACKET j !RBRACKET
                arr !LBRACKET j !RBRACKET !ASSIGN arr !LBRACKET j !ADD !NUMBER 1 !RBRACKET
                arr !LBRACKET j !ADD !NUMBER 1 !RBRACKET !ASSIGN temp
            !RBRACE
        !RBRACE
    !RBRACE
!RBRACE""",
        "c": """void bubble_sort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}""",
        "rust": """fn bubble_sort(arr: &mut [i32]) {
    let n = arr.len();
    for i in 0..n {
        for j in 0..n - i - 1 {
            if arr[j] > arr[j + 1] {
                arr.swap(j, j + 1);
            }
        }
    }
}""",
        "mojo": """fn bubble_sort(arr: List[Int], n: Int):
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                let temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp""",
    },
    {
        "name": "二分查找",
        "x": """!FUNC binary_search !LPAREN arr !LBRACKET !RBRACKET !COMMA target ^INT !COMMA left ^INT !COMMA right ^INT !RPAREN !ARROW ^INT
!LBRACE
    !IF left !GREATER right
    !LBRACE
        !RETURN !NUMBER !SUB !NUMBER 1
    !RBRACE
    !VAR mid ^INT !ASSIGN left !ADD right !DIV !NUMBER 2
    !IF arr !LBRACKET mid !RBRACKET !EQUAL target
    !LBRACE
        !RETURN mid
    !RBRACE
    !IF arr !LBRACKET mid !RBRACKET !GREATER target
    !LBRACE
        !RETURN !FUNC binary_search !LPAREN arr !COMMA target !COMMA left !COMMA mid !SUB !NUMBER 1 !RPAREN
    !RBRACE
    !RETURN !FUNC binary_search !LPAREN arr !COMMA target !COMMA mid !ADD !NUMBER 1 !COMMA right !RPAREN
!RBRACE""",
        "c": """int binary_search(int arr[], int target, int left, int right) {
    if (left > right) {
        return -1;
    }
    int mid = left + (right - left) / 2;
    if (arr[mid] == target) {
        return mid;
    }
    if (arr[mid] > target) {
        return binary_search(arr, target, left, mid - 1);
    }
    return binary_search(arr, target, mid + 1, right);
}""",
        "rust": """fn binary_search(arr: &[i32], target: i32, left: usize, right: usize) -> i32 {
    if left > right {
        return -1;
    }
    let mid = left + (right - left) / 2;
    if arr[mid] == target {
        return mid as i32;
    }
    if arr[mid] > target {
        return binary_search(arr, target, left, mid - 1);
    }
    binary_search(arr, target, mid + 1, right)
}""",
        "mojo": """fn binary_search(arr: List[Int], target: Int, left: Int, right: Int) -> Int:
    if left > right:
        return -1
    let mid = (left + right) // 2
    if arr[mid] == target:
        return mid
    if arr[mid] > target:
        return binary_search(arr, target, left, mid - 1)
    return binary_search(arr, target, mid + 1, right)""",
    },
    {
        "name": "斐波那契数列",
        "x": """!FUNC fibonacci !LPAREN n ^INT !RPAREN !ARROW ^INT
!LBRACE
    !IF n !EQUAL !NUMBER 0
    !LBRACE
        !RETURN !NUMBER 0
    !RBRACE
    !IF n !EQUAL !NUMBER 1
    !LBRACE
        !RETURN !NUMBER 1
    !RBRACE
    !RETURN !FUNC fibonacci !LPAREN n !SUB !NUMBER 1 !RPAREN !ADD !FUNC fibonacci !LPAREN n !SUB !NUMBER 2 !RPAREN
!RBRACE""",
        "c": """int fibonacci(int n) {
    if (n == 0) return 0;
    if (n == 1) return 1;
    return fibonacci(n - 1) + fibonacci(n - 2);
}""",
        "rust": """fn fibonacci(n: i32) -> i32 {
    match n {
        0 => 0,
        1 => 1,
        _ => fibonacci(n - 1) + fibonacci(n - 2),
    }
}""",
        "mojo": """fn fibonacci(n: Int) -> Int:
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)""",
    },
    {
        "name": "最大公约数",
        "x": """!FUNC gcd !LPAREN a ^INT !COMMA b ^INT !RPAREN !ARROW ^INT
!LBRACE
    !IF b !EQUAL !NUMBER 0
    !LBRACE
        !RETURN a
    !RBRACE
    !RETURN !FUNC gcd !LPAREN b !COMMA a !MOD b !RPAREN
!RBRACE""",
        "c": """int gcd(int a, int b) {
    if (b == 0) return a;
    return gcd(b, a % b);
}""",
        "rust": """fn gcd(a: i32, b: i32) -> i32 {
    if b == 0 { a } else { gcd(b, a % b) }
}""",
        "mojo": """fn gcd(a: Int, b: Int) -> Int:
    if b == 0:
        return a
    return gcd(b, a % b)""",
    },
    {
        "name": "阶乘",
        "x": """!FUNC factorial !LPAREN n ^INT !RPAREN !ARROW ^INT
!LBRACE
    !IF n !LESS !NUMBER 2
    !LBRACE
        !RETURN !NUMBER 1
    !RBRACE
    !RETURN n !MUL !FUNC factorial !LPAREN n !SUB !NUMBER 1 !RPAREN
!RBRACE""",
        "c": """int factorial(int n) {
    if (n < 2) return 1;
    return n * factorial(n - 1);
}""",
        "rust": """fn factorial(n: i32) -> i32 {
    if n < 2 { 1 } else { n * factorial(n - 1) }
}""",
        "mojo": """fn factorial(n: Int) -> Int:
    if n < 2:
        return 1
    return n * factorial(n - 1)""",
    },
]


DATA_STRUCTURE_TEMPLATES = [
    {
        "name": "链表节点",
        "x": """!STRUCT Node
!LBRACE
    value ^INT SEMICOLON
    next ^INT SEMICOLON
!RBRACE""",
        "c": """struct Node {
    int value;
    struct Node* next;
};""",
        "rust": """struct Node {
    value: i32,
    next: Option<Box<Node>>,
}""",
        "mojo": """struct Node:
    var value: Int
    var next: Optional[Node]""",
    },
    {
        "name": "栈",
        "x": """!STRUCT Stack
!LBRACE
    items !LBRACKET !NUMBER 100 !RBRACKET ^INT SEMICOLON
    top ^INT SEMICOLON
!RBRACE""",
        "c": """struct Stack {
    int items[100];
    int top;
};""",
        "rust": """struct Stack {
    items: [i32; 100],
    top: usize,
}""",
        "mojo": """struct Stack:
    var items: List[Int]
    var top: Int""",
    },
]


def generate_quad_training_pairs(count: int = 500) -> List[Dict]:
    """生成四语配对训练数据"""
    pairs = []

    for template in X_TEMPLATE_SAMPLES:
        pairs.append({
            "id": f"x_tmpl_{len(pairs)}",
            "source_lang": "x",
            "target_lang": "c",
            "source_code": template["x"],
            "target_code": template["c"],
        })
        pairs.append({
            "id": f"x_tmpl_{len(pairs)}",
            "source_lang": "x",
            "target_lang": "rust",
            "source_code": template["x"],
            "target_code": template["rust"],
        })
        pairs.append({
            "id": f"x_tmpl_{len(pairs)}",
            "source_lang": "x",
            "target_lang": "mojo",
            "source_code": template["x"],
            "target_code": template["mojo"],
        })

    for template in ALGORITHM_TEMPLATES:
        pairs.append({
            "id": f"algo_{template['name']}_x_c",
            "source_lang": "x",
            "target_lang": "c",
            "source_code": template["x"],
            "target_code": template["c"],
        })
        pairs.append({
            "id": f"algo_{template['name']}_x_rust",
            "source_lang": "x",
            "target_lang": "rust",
            "source_code": template["x"],
            "target_code": template["rust"],
        })
        pairs.append({
            "id": f"algo_{template['name']}_x_mojo",
            "source_lang": "x",
            "target_lang": "mojo",
            "source_code": template["x"],
            "target_code": template["mojo"],
        })

    for template in DATA_STRUCTURE_TEMPLATES:
        pairs.append({
            "id": f"ds_{template['name']}_x_c",
            "source_lang": "x",
            "target_lang": "c",
            "source_code": template["x"],
            "target_code": template["c"],
        })
        pairs.append({
            "id": f"ds_{template['name']}_x_rust",
            "source_lang": "x",
            "target_lang": "rust",
            "source_code": template["x"],
            "target_code": template["rust"],
        })
        pairs.append({
            "id": f"ds_{template['name']}_x_mojo",
            "source_lang": "x",
            "target_lang": "mojo",
            "source_code": template["x"],
            "target_code": template["mojo"],
        })

    for _ in range(count):
        base = random.choice(X_TEMPLATE_SAMPLES + ALGORITHM_TEMPLATES)
        lang = random.choice(["c", "rust", "mojo"])
        pairs.append({
            "id": f"aug_{random.randint(10000, 99999)}",
            "source_lang": "x",
            "target_lang": lang,
            "source_code": base["x"],
            "target_code": base[lang],
            "augmented": True,
        })

    return pairs


def generate_c_rust_pairs(count: int = 200) -> List[Dict]:
    """生成 C ↔ Rust 配对数据"""
    pairs = []

    c_rust_correspondences = [
        {
            "c": """int add(int a, int b) { return a + b; }""",
            "rust": """fn add(a: i32, b: i32) -> i32 { a + b }""",
        },
        {
            "c": """void swap(int* x, int* y) { int t = *x; *x = *y; *y = t; }""",
            "rust": """fn swap(x: &mut i32, y: &mut i32) { let t = *x; *x = *y; *y = t; }""",
        },
        {
            "c": """int factorial(int n) { return n <= 1 ? 1 : n * factorial(n - 1); }""",
            "rust": """fn factorial(n: i32) -> i32 { if n <= 1 { 1 } else { n * factorial(n - 1) } }""",
        },
    ]

    for i in range(count):
        sample = random.choice(c_rust_correspondences)
        pairs.append({
            "id": f"cr_{i}",
            "source_lang": "c",
            "target_lang": "rust",
            "source_code": sample["c"],
            "target_code": sample["rust"],
        })
        pairs.append({
            "id": f"rc_{i}",
            "source_lang": "rust",
            "target_lang": "c",
            "source_code": sample["rust"],
            "target_code": sample["c"],
        })

    return pairs


def generate_rust_mojo_pairs(count: int = 100) -> List[Dict]:
    """生成 Rust ↔ Mojo 配对数据"""
    pairs = []

    rust_mojo_correspondences = [
        {
            "rust": """fn add(a: i32, b: i32) -> i32 { a + b }""",
            "mojo": """fn add(a: Int, b: Int) -> Int: a + b""",
        },
        {
            "rust": """let x: Vec<i32> = vec![1, 2, 3];""",
            "mojo": """var x: List[Int] = [1, 2, 3]""",
        },
        {
            "rust": """for i in 0..10 { println!("{}", i); }""",
            "mojo": """for i in range(10): print(i)""",
        },
    ]

    for i in range(count):
        sample = random.choice(rust_mojo_correspondences)
        pairs.append({
            "id": f"rm_{i}",
            "source_lang": "rust",
            "target_lang": "mojo",
            "source_code": sample["rust"],
            "target_code": sample["mojo"],
        })
        pairs.append({
            "id": f"mr_{i}",
            "source_lang": "mojo",
            "target_lang": "rust",
            "source_code": sample["mojo"],
            "target_code": sample["rust"],
        })

    return pairs


def generate_complete_dataset(output_dir: str) -> Dict[str, int]:
    """生成完整数据集"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("生成 XC ↔ C ↔ Rust ↔ Mojo 四语配对数据集")
    print("=" * 60)

    print("\n[1/4] 生成 XC 语言四语配对...")
    x_pairs = generate_quad_training_pairs(500)
    with open(output_path / "x_quad_pairs.json", "w", encoding="utf-8") as f:
        json.dump(x_pairs, f, ensure_ascii=False, indent=2)
    print(f"  生成了 {len(x_pairs)} 条 XC 语系配对")

    print("\n[2/4] 生成 C ↔ Rust 配对...")
    c_rust_pairs = generate_c_rust_pairs(200)
    with open(output_path / "c_rust_pairs.json", "w", encoding="utf-8") as f:
        json.dump(c_rust_pairs, f, ensure_ascii=False, indent=2)
    print(f"  生成了 {len(c_rust_pairs)} 条 C↔Rust 配对")

    print("\n[3/4] 生成 Rust ↔ Mojo 配对...")
    rust_mojo_pairs = generate_rust_mojo_pairs(100)
    with open(output_path / "rust_mojo_pairs.json", "w", encoding="utf-8") as f:
        json.dump(rust_mojo_pairs, f, ensure_ascii=False, indent=2)
    print(f"  生成了 {len(rust_mojo_pairs)} 条 Rust↔Mojo 配对")

    print("\n[4/4] 合并所有配对为统一格式...")
    all_pairs = x_pairs + c_rust_pairs + rust_mojo_pairs

    instruction_templates = [
        "将以下 {source} 代码翻译为 {target} 代码:",
        "Translate the following {source} code to {target}:",
        "作为 {target} 专家,请将这段 {source} 代码翻译:",
    ]

    formatted_data = []
    for pair in all_pairs:
        template = random.choice(instruction_templates)
        source_lang_name = {"x": "X", "c": "C", "rust": "Rust", "mojo": "Mojo"}[pair["source_lang"]]
        target_lang_name = {"x": "X", "c": "C", "rust": "Rust", "mojo": "Mojo"}[pair["target_lang"]]

        formatted_data.append({
            "instruction": template.format(source=source_lang_name, target=target_lang_name),
            "input": pair["source_code"],
            "output": pair["target_code"],
            "source_lang": pair["source_lang"],
            "target_lang": pair["target_lang"],
            "id": pair.get("id", ""),
        })

    with open(output_path / "complete_training_data.json", "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=2)

    print(f"  总计 {len(formatted_data)} 条训练数据")

    print("\n" + "=" * 60)
    print("数据集生成完成!")
    print(f"保存位置: {output_path}")
    print("=" * 60)

    return {
        "x_quad": len(x_pairs),
        "c_rust": len(c_rust_pairs),
        "rust_mojo": len(rust_mojo_pairs),
        "total": len(all_pairs),
        "formatted": len(formatted_data),
    }


if __name__ == "__main__":
    import sys
    output = sys.argv[1] if len(sys.argv) > 1 else "e:/X语音/dataset"
    generate_complete_dataset(output)
