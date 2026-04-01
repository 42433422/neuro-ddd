"""
XC 语言 V3 专属原创符号数据集生成器
完全原创符号系统
"""

import json
import random
from typing import List, Dict
from pathlib import Path


X_CODE_SAMPLES = [
    {
        "name": "HelloWorld",
        "x": """⌘Main{�打印机"Hello World"}""",
        "c": '''#include <stdio.h>
int main() {
    printf("Hello World\\n");
    return 0;
}''',
        "rust": '''fn main() {
    println!("Hello World");
}''',
        "mojo": '''fn main():
    print("Hello World")''',
    },
    {
        "name": "两数相加",
        "x": """⌘Main{▽Func add(a◈Int,b◈Int)◈Int⌬a⊕b⌦add(3,5)}""",
        "c": '''#include <stdio.h>
int add(int a, int b) { return a + b; }
int main() { printf("%d\\n", add(3, 5)); return 0; }''',
        "rust": '''fn add(a: i32, b: i32) -> i32 { a + b }
fn main() { println!("{}", add(3, 5)); }''',
        "mojo": '''fn add(a: Int, b: Int) -> Int: a + b
fn main(): print(add(3, 5))''',
    },
    {
        "name": "条件判断",
        "x": """⌘Main{▽x◈Int≔10▷x⊳5{�打印机"big"}▷Else{�打印机"small"}}""",
        "c": '''#include <stdio.h>
int main() {
    int x = 10;
    if (x > 5) { printf("big\\n"); }
    else { printf("small\\n"); }
    return 0;
}''',
        "rust": '''fn main() {
    let x: i32 = 10;
    if x > 5 { println!("big"); }
    else { println!("small"); }
}''',
        "mojo": '''fn main():
    let x: Int = 10
    if x > 5:
        print("big")
    else:
        print("small")''',
    },
    {
        "name": "for循环",
        "x": """⌘Main{⟲i◈Int∈[0,5]{�打印机i}}""",
        "c": '''#include <stdio.h>
int main() {
    for (int i = 0; i < 5; i++) { printf("%d\\n", i); }
    return 0;
}''',
        "rust": '''fn main() {
    for i in 0..5 { println!("{}", i); }
}''',
        "mojo": '''fn main():
    for i in range(5): print(i)''',
    },
    {
        "name": "while循环",
        "x": """⌘Main{▽i◈Int≔0⟲Whilei⊲5{�打印机i◉Refi⊕≔1}}""",
        "c": '''#include <stdio.h>
int main() {
    int i = 0;
    while (i < 5) { printf("%d\\n", i); i++; }
    return 0;
}''',
        "rust": '''fn main() {
    let mut i: i32 = 0;
    while i < 5 { println!("{}", i); i += 1; }
}''',
        "mojo": '''fn main():
    var i: Int = 0
    while i < 5:
        print(i)
        i += 1''',
    },
    {
        "name": "阶乘",
        "x": """⌘Main{▽Func fac(n◈Int)◈Int⌬▷n⊲2{⌀1}n⊗⌦fac(n⊖1)⌦fac(5)}""",
        "c": '''#include <stdio.h>
int fac(int n) { if (n < 2) return 1; return n * fac(n - 1); }
int main() { printf("%d\\n", fac(5)); return 0; }''',
        "rust": '''fn fac(n: i32) -> i32 { if n < 2 { 1 } else { n * fac(n - 1) } }
fn main() { println!("{}", fac(5)); }''',
        "mojo": '''fn fac(n: Int) -> Int: if n < 2: 1 else: n * fac(n - 1)
fn main(): print(fac(5))''',
    },
    {
        "name": "斐波那契",
        "x": """⌘Main{▽Func fib(n◈Int)◈Int⌬▷n≡0{⌀0}▷n≡1{⌀1}⌦fib(n⊖1)⊕⌦fib(n⊖2)⌦fib(10)}""",
        "c": '''#include <stdio.h>
int fib(int n) { if (n==0) return 0; if (n==1) return 1; return fib(n-1)+fib(n-2); }
int main() { printf("%d\\n", fib(10)); return 0; }''',
        "rust": '''fn fib(n: i32) -> i32 { match n { 0=>0, 1=>1, _=>fib(n-1)+fib(n-2) } }
fn main() { println!("{}", fib(10)); }''',
        "mojo": '''fn fib(n: Int) -> Int: if n==0: 0 elif n==1: 1 else: fib(n-1)+fib(n-2)
fn main(): print(fib(10))''',
    },
    {
        "name": "最大值",
        "x": """⌘Main{▽Func max(a◈Int,b◈Int)◈Int⌬▷a⊳b{⌀a}⌀b⌦max(7,3)}""",
        "c": '''#include <stdio.h>
int max(int a, int b) { return a > b ? a : b; }
int main() { printf("%d\\n", max(7, 3)); return 0; }''',
        "rust": '''fn max(a: i32, b: i32) -> i32 { if a > b { a } else { b } }
fn main() { println!("{}", max(7, 3)); }''',
        "mojo": '''fn max(a: Int, b: Int) -> Int: a if a > b else b
fn main(): print(max(7, 3))''',
    },
    {
        "name": "素数判断",
        "x": """⌘Main{▽Func isPrime(n◈Int)◉Bool⌬▷n⊲2{✗}⟲i◈Int∈[2,n]▷n⊙i≡0{✗}✓⌦isPrime(17)}""",
        "c": '''#include <stdio.h>
int isPrime(int n) { if (n < 2) return 0; for (int i = 2; i < n; i++) if (n % i == 0) return 0; return 1; }
int main() { printf("%d\\n", isPrime(17)); return 0; }''',
        "rust": '''fn isPrime(n: i32) -> bool { if n < 2 { false } else { for i in 2..n { if n % i == 0 { return false; } } true } }
fn main() { println!("{}", isPrime(17)); }''',
        "mojo": '''fn isPrime(n: Int) -> Bool: if n < 2: False else: for i in range(2, n): if n % i == 0: return False; True
fn main(): print(isPrime(17))''',
    },
    {
        "name": "累加求和",
        "x": """⌘Main{▽sum◈Int≔0⟲i◈Int∈[1,101]{sum⊕≔sum⊕i}�打印机sum}""",
        "c": '''#include <stdio.h>
int main() { int sum = 0; for (int i = 1; i <= 100; i++) sum += i; printf("%d\\n", sum); return 0; }''',
        "rust": '''fn main() { let sum: i32 = (1..=100).sum(); println!("{}", sum); }''',
        "mojo": '''fn main(): var sum = 0; for i in range(1, 101): sum += i; print(sum)''',
    },
    {
        "name": "水仙花数",
        "x": """⌘Main{⟲i◈Int∈[100,1000]{▽a◈Int≔i⊘100▽b◈Int≔(i⊙100)⊘10▽c◈Int≔i⊙10▷a⊗a⊗a⊕b⊗b⊗b⊕c⊗c⊗c≡i{�打印机i}}}""",
        "c": '''#include <stdio.h>
int main() { for (int i = 100; i < 1000; i++) { int a=i/100, b=(i/10)%10, c=i%10; if (a*a*a+b*b*b+c*c*c==i) printf("%d\\n", i); } return 0; }''',
        "rust": '''fn main() { for i in 100..1000 { let a=i/100; let b=(i/10)%10; let c=i%10; if a*a*a+b*b*b+c*c*c==i { println!("{}", i); } } }''',
        "mojo": '''fn main(): for i in range(100, 1000): let a=i//100; let b=(i//10)%10; let c=i%10; if a*a*a+b*b*b+c*c*c==i: print(i)''',
    },
    {
        "name": "交换变量",
        "x": """⌘Main{▽a◈Int≔5▽b◈Int≔10▽tmp◈Int≔a◉Refa≔b◉Refb≔tmp�打印机a�打印机b}""",
        "c": '''#include <stdio.h>
int main() { int a=5, b=10; int tmp=a; a=b; b=tmp; printf("%d %d\\n", a, b); return 0; }''',
        "rust": '''fn main() { let mut a=5; let mut b=10; let tmp=a; a=b; b=tmp; println!("{} {}", a, b); }''',
        "mojo": '''fn main(): var a=5; var b=10; let tmp=a; a=b; b=tmp; print(a); print(b)''',
    },
    {
        "name": "结构体",
        "x": """⌘Main{▽Struct Point{x◈Int,y◈Int}▽p◐Point≔▯NewPoint{1,2}�打印机p◉x}""",
        "c": '''#include <stdio.h>
typedef struct { int x; int y; } Point;
int main() { Point p = {1, 2}; printf("%d\\n", p.x); return 0; }''',
        "rust": '''struct Point { x: i32, y: i32 }
fn main() { let p = Point { x: 1, y: 2 }; println!("{}", p.x); }''',
        "mojo": '''struct Point: var x: Int; var y: Int
fn main(): let p = Point { x: 1, y: 2 }; print(p.x)''',
    },
    {
        "name": "字符串长度",
        "x": """⌘Main{▽Func len(s◆String)◈Int⌬s◉length⌦len("hello")}""",
        "c": '''#include <stdio.h>
#include <string.h>
int len(char* s) { return strlen(s); }
int main() { printf("%d\\n", len("hello")); return 0; }''',
        "rust": '''fn len(s: &str) -> usize { s.len() }
fn main() { println!("{}", len("hello")); }''',
        "mojo": '''fn len(s: String) -> Int: s.length
fn main(): print(len("hello"))''',
    },
    {
        "name": "数组遍历",
        "x": """⌘Main{▽arr◇Array◈Int≔[1,2,3]⟲i◈Int∈[0,3]{�打印机arr◉i}}""",
        "c": '''#include <stdio.h>
int main() { int arr[] = {1, 2, 3}; for (int i = 0; i < 3; i++) printf("%d\\n", arr[i]); return 0; }''',
        "rust": '''fn main() { let arr = vec![1, 2, 3]; for i in 0..3 { println!("{}", arr[i]); } }''',
        "mojo": '''fn main(): let arr = [1, 2, 3]; for i in range(3): print(arr[i])''',
    },
]


def generate_x_v3_dataset(count: int = 1000) -> List[Dict]:
    """生成 XC 语言 V3 配对数据集"""
    pairs = []

    for sample in X_CODE_SAMPLES:
        pairs.append({
            "id": f"x2c_{sample['name']}",
            "source_lang": "x",
            "target_lang": "c",
            "source_code": sample["x"],
            "target_code": sample["c"],
        })
        pairs.append({
            "id": f"x2rust_{sample['name']}",
            "source_lang": "x",
            "target_lang": "rust",
            "source_code": sample["x"],
            "target_code": sample["rust"],
        })
        pairs.append({
            "id": f"x2mojo_{sample['name']}",
            "source_lang": "x",
            "target_lang": "mojo",
            "source_code": sample["x"],
            "target_code": sample["mojo"],
        })
        pairs.append({
            "id": f"c2x_{sample['name']}",
            "source_lang": "c",
            "target_lang": "x",
            "source_code": sample["c"],
            "target_code": sample["x"],
        })
        pairs.append({
            "id": f"rust2x_{sample['name']}",
            "source_lang": "rust",
            "target_lang": "x",
            "source_code": sample["rust"],
            "target_code": sample["x"],
        })
        pairs.append({
            "id": f"mojo2x_{sample['name']}",
            "source_lang": "mojo",
            "target_lang": "x",
            "source_code": sample["mojo"],
            "target_code": sample["x"],
        })

    for _ in range(count):
        sample = random.choice(X_CODE_SAMPLES)
        direction = random.choice([
            ("x", "c"), ("x", "rust"), ("x", "mojo"),
            ("c", "x"), ("rust", "x"), ("mojo", "x"),
        ])
        source, target = direction

        pairs.append({
            "id": f"aug_{random.randint(10000, 99999)}",
            "source_lang": source,
            "target_lang": target,
            "source_code": sample[source],
            "target_code": sample[target],
            "augmented": True,
        })

    return pairs


def format_for_training(pairs: List[Dict]) -> List[Dict]:
    """格式化训练数据"""
    lang_names = {"x": "XC语言", "c": "C", "rust": "Rust", "mojo": "Mojo"}

    formatted = []
    templates = [
        "将{l1}代码翻译为{l2}，只输出{l2}代码:",
        "{l1} → {l2}:",
    ]

    for pair in pairs:
        template = random.choice(templates)
        source_name = lang_names[pair["source_lang"]]
        target_name = lang_names[pair["target_lang"]]

        instruction = template.format(l1=source_name, l2=target_name)

        formatted.append({
            "instruction": instruction,
            "input": pair["source_code"],
            "output": pair["target_code"],
            "source_lang": pair["source_lang"],
            "target_lang": pair["target_lang"],
        })

    return formatted


def generate_and_save(output_dir: str = "e:/X语音/dataset"):
    """生成并保存"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("XC 语言 V3 专属符号数据集生成器")
    print("=" * 60)

    print("\n[1] 生成 XC 语言 V3 配对...")
    pairs = generate_x_v3_dataset(1000)
    with open(output_path / "x_v3_pairs.json", "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    print(f"  生成了 {len(pairs)} 条配对")

    print("\n[2] 格式化训练数据...")
    formatted = format_for_training(pairs)
    with open(output_path / "x_v3_training.json", "w", encoding="utf-8") as f:
        json.dump(formatted, f, ensure_ascii=False, indent=2)
    print(f"  格式化了 {len(formatted)} 条训练数据")

    print("\n" + "=" * 60)
    print("数据集生成完成!")
    print(f"保存位置: {output_path}")
    print("=" * 60)

    print("\n数据集统计:")
    lang_counts = {}
    for pair in pairs:
        lang_counts[pair["source_lang"]] = lang_counts.get(pair["source_lang"], 0) + 1
    for lang, count in sorted(lang_counts.items()):
        print(f"  {lang}: {count} 条")

    return pairs


if __name__ == "__main__":
    generate_and_save()
