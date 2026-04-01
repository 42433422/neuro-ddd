"""
XC 语言 V2 纯符号化数据集生成器
生成 XC ↔ C ↔ Rust ↔ Mojo 四语配对数据
"""

import json
import random
from typing import List, Dict
from pathlib import Path


X_CODE_SAMPLES = [
    {
        "name": "Hello World",
        "x": """▶MAIN{◎>"Hello World"}""",
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
        "x": """▶MAIN{◈F add(a,b)∈→∈{◀a+b}◎>◈F add(3,5)}""",
        "c": '''#include <stdio.h>
int add(int a, int b) {
    return a + b;
}
int main() {
    printf("%d\\n", add(3, 5));
    return 0;
}''',
        "rust": '''fn add(a: i32, b: i32) -> i32 { a + b }
fn main() {
    println!("{}", add(3, 5));
}''',
        "mojo": '''fn add(a: Int, b: Int) -> Int: a + b
fn main():
    print(add(3, 5))''',
    },
    {
        "name": "条件判断",
        "x": """▶MAIN{◈ x=10?x>5{◎>"big"}?/{◎>"small"}}""",
        "c": '''#include <stdio.h>
int main() {
    int x = 10;
    if (x > 5) {
        printf("big\\n");
    } else {
        printf("small\\n");
    }
    return 0;
}''',
        "rust": '''fn main() {
    let x = 10;
    if x > 5 {
        println!("big");
    } else {
        println!("small");
    }
}''',
        "mojo": '''fn main():
    let x = 10
    if x > 5:
        print("big")
    else:
        print("small")''',
    },
    {
        "name": "for循环",
        "x": """▶MAIN{▶i∈[0,5]{◎>i}}""",
        "c": '''#include <stdio.h>
int main() {
    for (int i = 0; i < 5; i++) {
        printf("%d\\n", i);
    }
    return 0;
}''',
        "rust": '''fn main() {
    for i in 0..5 {
        println!("{}", i);
    }
}''',
        "mojo": '''fn main():
    for i in range(5):
        print(i)''',
    },
    {
        "name": "while循环",
        "x": """▶MAIN{◈ i=0?i<5{◎>i◈i=i+1}}""",
        "c": '''#include <stdio.h>
int main() {
    int i = 0;
    while (i < 5) {
        printf("%d\\n", i);
        i++;
    }
    return 0;
}''',
        "rust": '''fn main() {
    let mut i = 0;
    while i < 5 {
        println!("{}", i);
        i += 1;
    }
}''',
        "mojo": '''fn main():
    var i = 0
    while i < 5:
        print(i)
        i += 1''',
    },
    {
        "name": "阶乘函数",
        "x": """▶MAIN{◈F fac(n)∈→∈{?n<2{◀1}◀n*◈F fac(n-1)}◎>◈F fac(5)}""",
        "c": '''#include <stdio.h>
int fac(int n) {
    if (n < 2) return 1;
    return n * fac(n - 1);
}
int main() {
    printf("%d\\n", fac(5));
    return 0;
}''',
        "rust": '''fn fac(n: i32) -> i32 {
    if n < 2 { 1 } else { n * fac(n - 1) }
}
fn main() {
    println!("{}", fac(5));
}''',
        "mojo": '''fn fac(n: Int) -> Int:
    if n < 2:
        return 1
    return n * fac(n - 1)
fn main():
    print(fac(5))''',
    },
    {
        "name": "斐波那契",
        "x": """▶MAIN{◈F fib(n)∈→∈{?n==0{◀0}?n==1{◀1}◀◈F fib(n-1)+◈F fib(n-2)}◎>◈F fib(10)}""",
        "c": '''#include <stdio.h>
int fib(int n) {
    if (n == 0) return 0;
    if (n == 1) return 1;
    return fib(n - 1) + fib(n - 2);
}
int main() {
    printf("%d\\n", fib(10));
    return 0;
}''',
        "rust": '''fn fib(n: i32) -> i32 {
    match n {
        0 => 0,
        1 => 1,
        _ => fib(n - 1) + fib(n - 2),
    }
}
fn main() {
    println!("{}", fib(10));
}''',
        "mojo": '''fn fib(n: Int) -> Int:
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fib(n - 1) + fib(n - 2)
fn main():
    print(fib(10))''',
    },
    {
        "name": "最大值",
        "x": """▶MAIN{◈F max(a,b)∈→∈{?a>b{◀a}◀b}◎>◈F max(7,3)}""",
        "c": '''#include <stdio.h>
int max(int a, int b) {
    if (a > b) return a;
    return b;
}
int main() {
    printf("%d\\n", max(7, 3));
    return 0;
}''',
        "rust": '''fn max(a: i32, b: i32) -> i32 {
    if a > b { a } else { b }
}
fn main() {
    println!("{}", max(7, 3));
}''',
        "mojo": '''fn max(a: Int, b: Int) -> Int:
    if a > b:
        return a
    return b
fn main():
    print(max(7, 3))''',
    },
    {
        "name": "数组遍历",
        "x": """▶MAIN{◈ arr∈a[1,2,3]∑i∈arr{◎>i}}""",
        "c": '''#include <stdio.h>
int main() {
    int arr[] = {1, 2, 3};
    for (int i = 0; i < 3; i++) {
        printf("%d\\n", arr[i]);
    }
    return 0;
}''',
        "rust": '''fn main() {
    let arr = vec![1, 2, 3];
    for i in &arr {
        println!("{}", i);
    }
}''',
        "mojo": '''fn main():
    let arr = [1, 2, 3]
    for i in arr:
        print(i)''',
    },
    {
        "name": "字符串长度",
        "x": """▶MAIN{◈F len(s)∈s→∈{◀s.length}◎>◈F len("hello")}""",
        "c": '''#include <stdio.h>
#include <string.h>
int len(char* s) {
    return strlen(s);
}
int main() {
    printf("%d\\n", len("hello"));
    return 0;
}''',
        "rust": '''fn len(s: &str) -> usize {
    s.len()
}
fn main() {
    println!("{}", len("hello"));
}''',
        "mojo": '''fn len(s: String) -> Int:
    return s.length
fn main():
    print(len("hello"))''',
    },
    {
        "name": "素数判断",
        "x": """▶MAIN{◈F isPrime(n)∈b→∈b{?n<2{◀×}▶i∈[2,n]?n%i==0{◀×}◀√}◎>◈F isPrime(17)}""",
        "c": '''#include <stdio.h>
int isPrime(int n) {
    if (n < 2) return 0;
    for (int i = 2; i < n; i++) {
        if (n % i == 0) return 0;
    }
    return 1;
}
int main() {
    printf("%d\\n", isPrime(17));
    return 0;
}''',
        "rust": '''fn isPrime(n: i32) -> bool {
    if n < 2 { return false; }
    for i in 2..n {
        if n % i == 0 { return false; }
    }
    true
}
fn main() {
    println!("{}", isPrime(17));
}''',
        "mojo": '''fn isPrime(n: Int) -> Bool:
    if n < 2:
        return False
    for i in range(2, n):
        if n % i == 0:
            return False
    return True
fn main():
    print(isPrime(17))''',
    },
    {
        "name": "结构体",
        "x": """▶MAIN{◈S Point{x∈,y∈,}◈ p◈S Point{1,2}◎>p.x}""",
        "c": '''#include <stdio.h>
typedef struct { int x; int y; } Point;
int main() {
    Point p = {1, 2};
    printf("%d\\n", p.x);
    return 0;
}''',
        "rust": '''struct Point { x: i32, y: i32 }
fn main() {
    let p = Point { x: 1, y: 2 };
    println!("{}", p.x);
}''',
        "mojo": '''struct Point:
    var x: Int
    var y: Int
fn main():
    let p = Point { x: 1, y: 2 }
    print(p.x)''',
    },
    {
        "name": "交换变量",
        "x": """▶MAIN{◈a=5◈b=10◈tmp=a◈a=b◈b=tmp◎>a◎>b}""",
        "c": '''#include <stdio.h>
int main() {
    int a = 5, b = 10;
    int tmp = a; a = b; b = tmp;
    printf("%d %d\\n", a, b);
    return 0;
}''',
        "rust": '''fn main() {
    let mut a = 5;
    let mut b = 10;
    let tmp = a; a = b; b = tmp;
    println!("{} {}", a, b);
}''',
        "mojo": '''fn main():
    var a = 5
    var b = 10
    let tmp = a
    a = b
    b = tmp
    print(a)
    print(b)''',
    },
    {
        "name": "累加求和",
        "x": """▶MAIN{◈ sum=0▶i∈[1,101]{◈ sum=sum+i}◎>sum}""",
        "c": '''#include <stdio.h>
int main() {
    int sum = 0;
    for (int i = 1; i <= 100; i++) {
        sum += i;
    }
    printf("%d\\n", sum);
    return 0;
}''',
        "rust": '''fn main() {
    let sum: i32 = (1..=100).sum();
    println!("{}", sum);
}''',
        "mojo": '''fn main():
    var sum = 0
    for i in range(1, 101):
        sum += i
    print(sum)''',
    },
    {
        "name": "水仙花数",
        "x": """▶MAIN{▶i∈[100,1000]{◈a=i/100◈b=i%100/10◈c=i%10?a*a*a+b*b*b+c*c*c==i{◎>i}}}""",
        "c": '''#include <stdio.h>
int main() {
    for (int i = 100; i < 1000; i++) {
        int a = i / 100, b = (i / 10) % 10, c = i % 10;
        if (a*a*a + b*b*b + c*c*c == i)
            printf("%d\\n", i);
    }
    return 0;
}''',
        "rust": '''fn main() {
    for i in 100..1000 {
        let a = i / 100;
        let b = (i / 10) % 10;
        let c = i % 10;
        if a*a*a + b*b*b + c*c*c == i {
            println!("{}", i);
        }
    }
}''',
        "mojo": '''fn main():
    for i in range(100, 1000):
        let a = i // 100
        let b = (i // 10) % 10
        let c = i % 10
        if a*a*a + b*b*b + c*c*c == i:
            print(i)''',
    },
]


def generate_x_language_dataset(count: int = 1000) -> List[Dict]:
    """生成 XC 语言四语配对数据集"""
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

    for _ in range(count - len(X_CODE_SAMPLES) * 6):
        sample = random.choice(X_CODE_SAMPLES)
        direction = random.choice([
            ("x", "c"), ("x", "rust"), ("x", "mojo"),
            ("c", "x"), ("rust", "x"), ("mojo", "x"),
            ("c", "rust"), ("rust", "c"),
            ("rust", "mojo"), ("mojo", "rust"),
            ("c", "mojo"), ("mojo", "c"),
        ])
        source, target = direction
        source_code = sample[source]
        target_code = sample[target]

        pairs.append({
            "id": f"aug_{random.randint(10000, 99999)}",
            "source_lang": source,
            "target_lang": target,
            "source_code": source_code,
            "target_code": target_code,
            "augmented": True,
        })

    return pairs


def format_for_training(pairs: List[Dict]) -> List[Dict]:
    """格式化训练数据"""
    lang_names = {"x": "XC语言", "c": "C", "rust": "Rust", "mojo": "Mojo"}

    formatted = []
    for pair in pairs:
        template = random.choice([
            "将以下{l1}代码翻译为{l2}代码，只输出翻译结果:",
            "Translate this {l1} code to {l2}:",
            "{l1} → {l2}:",
        ])

        formatted.append({
            "instruction": template.format(l1=lang_names[pair["source_lang"]], l2=lang_names[pair["target_lang"]]),
            "input": pair["source_code"],
            "output": pair["target_code"],
            "source_lang": pair["source_lang"],
            "target_lang": pair["target_lang"],
        })

    return formatted


def generate_and_save(output_dir: str = "e:/X语音/dataset"):
    """生成并保存数据集"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("XC 语言四语配对数据集生成器")
    print("=" * 60)

    print("\n[1] 生成基础配对...")
    pairs = generate_x_language_dataset(1000)
    with open(output_path / "x_language_pairs.json", "w", encoding="utf-8") as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    print(f"  生成了 {len(pairs)} 条配对")

    print("\n[2] 格式化训练数据...")
    formatted = format_for_training(pairs)
    with open(output_path / "x_language_training.json", "w", encoding="utf-8") as f:
        json.dump(formatted, f, ensure_ascii=False, indent=2)
    print(f"  格式化了 {len(formatted)} 条训练数据")

    print("\n[3] 导出纯文本格式...")
    with open(output_path / "x_language_pairs.txt", "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(f"=== {pair['source_lang']} → {pair['target_lang']} ===\n")
            f.write(pair["source_code"] + "\n")
            f.write("---\n")
            f.write(pair["target_code"] + "\n")
            f.write("\n")

    print("\n" + "=" * 60)
    print(f"数据集已保存到: {output_path}")
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
