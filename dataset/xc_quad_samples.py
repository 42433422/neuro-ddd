"""
XC 语言 - 四语对照样本数据集
C 底层 | Rust 安全 | Mojo 计算 | XC 主语言

每组样本包含完整可运行的代码示例
"""

X_CODE_SAMPLES = [
    # ============ 基础程序 ============
    {
        "name": "HelloWorld",
        "desc": "最基础的输出程序",
        "x": """# {
    ! "Hello World"
}""",
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
        "name": "变量声明",
        "desc": "基本变量声明和赋值",
        "x": """# {
    $x = 10
    $y = 20
    ! x + y = 
    ! x + y
}""",
        "c": '''#include <stdio.h>
int main() {
    int x = 10;
    int y = 20;
    printf("x + y = %d\\n", x + y);
    return 0;
}''',
        "rust": '''fn main() {
    let x = 10;
    let y = 20;
    println!("x + y = {}", x + y);
}''',
        "mojo": '''fn main():
    let x = 10
    let y = 20
    print("x + y = ", x + y)''',
    },
    {
        "name": "常量声明",
        "desc": "常量定义",
        "x": """# {
    @PI = 3.14159
    @MAX = 100
    ! PI = 
    ! @PI
}""",
        "c": '''#include <stdio.h>
#define PI 3.14159
#define MAX 100
int main() {
    printf("PI = %f\\n", PI);
    return 0;
}''',
        "rust": '''const PI: f64 = 3.14159;
const MAX: i32 = 100;
fn main() {
    println!("PI = {}", PI);
}''',
        "mojo": '''let PI: Float64 = 3.14159
let MAX: Int = 100
fn main():
    print("PI = ", PI)''',
    },
    {
        "name": "字符串变量",
        "desc": "字符串类型",
        "x": """# {
    $name = "XC Language"
    ! name
}""",
        "c": '''#include <stdio.h>
int main() {
    char* name = "XC Language";
    printf("%s\\n", name);
    return 0;
}''',
        "rust": '''fn main() {
    let name = "XC Language";
    println!("{}", name);
}''',
        "mojo": '''fn main():
    let name = "XC Language"
    print(name)''',
    },

    # ============ 算术运算 ============
    {
        "name": "加减乘除",
        "desc": "基本算术运算",
        "x": """# {
    $a = 15
    $b = 4
    ! a + b = 
    ! a + b
    ! a - b = 
    ! a - b
    ! a * b = 
    ! a * b
    ! a / b = 
    ! a / b
}""",
        "c": '''#include <stdio.h>
int main() {
    int a = 15, b = 4;
    printf("a + b = %d\\n", a + b);
    printf("a - b = %d\\n", a - b);
    printf("a * b = %d\\n", a * b);
    printf("a / b = %d\\n", a / b);
    return 0;
}''',
        "rust": '''fn main() {
    let a = 15;
    let b = 4;
    println!("a + b = {}", a + b);
    println!("a - b = {}", a - b);
    println!("a * b = {}", a * b);
    println!("a / b = {}", a / b);
}''',
        "mojo": '''fn main():
    let a = 15
    let b = 4
    print("a + b = ", a + b)
    print("a - b = ", a - b)
    print("a * b = ", a * b)
    print("a / b = ", a // b)''',
    },
    {
        "name": "取模运算",
        "desc": "取模/求余",
        "x": """# {
    $n = 17
    ! 17 % 5 = 
    ! n % 5
}""",
        "c": '''#include <stdio.h>
int main() {
    int n = 17;
    printf("17 %% 5 = %d\\n", 17 % 5);
    printf("n %% 5 = %d\\n", n % 5);
    return 0;
}''',
        "rust": '''fn main() {
    let n = 17;
    println!("17 % 5 = {}", 17 % 5);
    println!("n % 5 = {}", n % 5);
}''',
        "mojo": '''fn main():
    let n = 17
    print("17 % 5 = ", 17 % 5)
    print("n % 5 = ", n % 5)''',
    },
    {
        "name": "自增自减",
        "desc": "++ 和 -- 运算",
        "x": """# {
    $i = 0
    i = i + 1
    ! ++i = 
    ! i
    i = i - 1
    ! --i = 
    ! i
}""",
        "c": '''#include <stdio.h>
int main() {
    int i = 0;
    i++;
    printf("++i = %d\\n", i);
    i--;
    printf("--i = %d\\n", i);
    return 0;
}''',
        "rust": '''fn main() {
    let mut i = 0;
    i += 1;
    println!("++i = {}", i);
    i -= 1;
    println!("--i = {}", i);
}''',
        "mojo": '''fn main():
    var i = 0
    i += 1
    print("++i = ", i)
    i -= 1
    print("--i = ", i)''',
    },

    # ============ 比较和逻辑 ============
    {
        "name": "比较运算",
        "desc": "大于小于等于",
        "x": """# {
    $a = 10
    $b = 20
    ? a > b {
        ! "a > b"
    }
    ? a < b {
        ! "a < b"
    }
    ? a == b {
        ! "a == b"
    }
}""",
        "c": '''#include <stdio.h>
int main() {
    int a = 10, b = 20;
    if (a > b) printf("a > b\\n");
    if (a < b) printf("a < b\\n");
    if (a == b) printf("a == b\\n");
    return 0;
}''',
        "rust": '''fn main() {
    let a = 10;
    let b = 20;
    if a > b { println!("a > b"); }
    if a < b { println!("a < b"); }
    if a == b { println!("a == b"); }
}''',
        "mojo": '''fn main():
    let a = 10
    let b = 20
    if a > b: print("a > b")
    if a < b: print("a < b")
    if a == b: print("a == b")''',
    },
    {
        "name": "逻辑运算",
        "desc": "与或非",
        "x": """# {
    $x = 5
    ? x > 0 && x < 10 {
        ! "x in (0, 10)"
    }
    ? x < 0 || x > 100 {
        ! "x out of range"
    }
    ? !(x == 5) {
        ! "x != 5"
    }
}""",
        "c": '''#include <stdio.h>
int main() {
    int x = 5;
    if (x > 0 && x < 10) printf("x in (0, 10)\\n");
    if (x < 0 || x > 100) printf("x out of range\\n");
    if (!(x == 5)) printf("x != 5\\n");
    return 0;
}''',
        "rust": '''fn main() {
    let x = 5;
    if x > 0 && x < 10 { println!("x in (0, 10)"); }
    if x < 0 || x > 100 { println!("x out of range"); }
    if !(x == 5) { println!("x != 5"); }
}''',
        "mojo": '''fn main():
    let x = 5
    if x > 0 and x < 10: print("x in (0, 10)")
    if x < 0 or x > 100: print("x out of range")
    if not (x == 5): print("x != 5")''',
    },

    # ============ 条件语句 ============
    {
        "name": "if语句",
        "desc": "基本条件判断",
        "x": """# {
    $score = 85
    ? score >= 60 {
        ! "Pass"
    }
}""",
        "c": '''#include <stdio.h>
int main() {
    int score = 85;
    if (score >= 60) {
        printf("Pass\\n");
    }
    return 0;
}''',
        "rust": '''fn main() {
    let score = 85;
    if score >= 60 {
        println!("Pass");
    }
}''',
        "mojo": '''fn main():
    let score = 85
    if score >= 60:
        print("Pass")''',
    },
    {
        "name": "ifelse语句",
        "desc": "if-else条件分支",
        "x": """# {
    $x = 10
    ? x > 0 {
        ! "positive"
    } ?: {
        ! "non-positive"
    }
}""",
        "c": '''#include <stdio.h>
int main() {
    int x = 10;
    if (x > 0) {
        printf("positive\\n");
    } else {
        printf("non-positive\\n");
    }
    return 0;
}''',
        "rust": '''fn main() {
    let x = 10;
    if x > 0 {
        println!("positive");
    } else {
        println!("non-positive");
    }
}''',
        "mojo": '''fn main():
    let x = 10
    if x > 0:
        print("positive")
    else:
        print("non-positive")''',
    },
    {
        "name": "多条件分支",
        "desc": "if-elif-else",
        "x": """# {
    $grade = 85
    ? grade >= 90 {
        ! "A"
    } ?? grade >= 80 {
        ! "B"
    } ?? grade >= 70 {
        ! "C"
    } ?: {
        ! "D"
    }
}""",
        "c": '''#include <stdio.h>
int main() {
    int grade = 85;
    if (grade >= 90) {
        printf("A\\n");
    } else if (grade >= 80) {
        printf("B\\n");
    } else if (grade >= 70) {
        printf("C\\n");
    } else {
        printf("D\\n");
    }
    return 0;
}''',
        "rust": '''fn main() {
    let grade = 85;
    if grade >= 90 {
        println!("A");
    } else if grade >= 80 {
        println!("B");
    } else if grade >= 70 {
        println!("C");
    } else {
        println!("D");
    }
}''',
        "mojo": '''fn main():
    let grade = 85
    if grade >= 90:
        print("A")
    elif grade >= 80:
        print("B")
    elif grade >= 70:
        print("C")
    else:
        print("D")''',
    },

    # ============ 循环语句 ============
    {
        "name": "for循环",
        "desc": "基本for循环",
        "x": """# {
    ~i = 0; i < 5; i = i + 1 {
        ! i
    }
}""",
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
        "desc": "基本while循环",
        "x": """# {
    $i = 0
    @i < 5 {
        ! i
        i = i + 1
    }
}""",
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
        "name": "累加求和",
        "desc": "循环累加",
        "x": """# {
    $sum = 0
    ~i = 1; i <= 100; i = i + 1 {
        sum = sum + i
    }
    ! sum
}""",
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
        "name": "break语句",
        "desc": "循环中break跳出",
        "x": """# {
    ~i = 0; i < 10; i = i + 1 {
        ? i == 5 {
            >
        }
        ! i
    }
}""",
        "c": '''#include <stdio.h>
int main() {
    for (int i = 0; i < 10; i++) {
        if (i == 5) break;
        printf("%d\\n", i);
    }
    return 0;
}''',
        "rust": '''fn main() {
    for i in 0..10 {
        if i == 5 { break; }
        println!("{}", i);
    }
}''',
        "mojo": '''fn main():
    for i in range(10):
        if i == 5: break
        print(i)''',
    },
    {
        "name": "continue语句",
        "desc": "循环中跳过当前迭代",
        "x": """# {
    ~i = 0; i < 5; i = i + 1 {
        ? i == 2 {
            <
        }
        ! i
    }
}""",
        "c": '''#include <stdio.h>
int main() {
    for (int i = 0; i < 5; i++) {
        if (i == 2) continue;
        printf("%d\\n", i);
    }
    return 0;
}''',
        "rust": '''fn main() {
    for i in 0..5 {
        if i == 2 { continue; }
        println!("{}", i);
    }
}''',
        "mojo": '''fn main():
    for i in range(5):
        if i == 2: continue
        print(i)''',
    },

    # ============ 函数 ============
    {
        "name": "函数定义",
        "desc": "基本函数定义和调用",
        "x": """% add(a, b) {
    ^ a + b
}
# {
    $result = add(3, 5)
    ! result
}""",
        "c": '''#include <stdio.h>
int add(int a, int b) {
    return a + b;
}
int main() {
    int result = add(3, 5);
    printf("%d\\n", result);
    return 0;
}''',
        "rust": '''fn add(a: i32, b: i32) -> i32 {
    a + b
}
fn main() {
    let result = add(3, 5);
    println!("{}", result);
}''',
        "mojo": '''fn add(a: Int, b: Int) -> Int:
    return a + b
fn main():
    let result = add(3, 5)
    print(result)''',
    },
    {
        "name": "函数重载",
        "desc": "多参数函数",
        "x": """% max(a, b) {
    ? a > b {
        ^ a
    } ?: {
        ^ b
    }
}
# {
    ! max(10, 20)
}""",
        "c": '''#include <stdio.h>
int max(int a, int b) {
    return a > b ? a : b;
}
int main() {
    printf("%d\\n", max(10, 20));
    return 0;
}''',
        "rust": '''fn max(a: i32, b: i32) -> i32 {
    if a > b { a } else { b }
}
fn main() {
    println!("{}", max(10, 20));
}''',
        "mojo": '''fn max(a: Int, b: Int) -> Int:
    return a if a > b else b
fn main():
    print(max(10, 20))''',
    },
    {
        "name": "递归函数",
        "desc": "阶乘递归",
        "x": """% fac(n) {
    ? n <= 1 {
        ^ 1
    }
    ^ n * fac(n - 1)
}
# {
    ! fac(5)
}""",
        "c": '''#include <stdio.h>
int fac(int n) {
    if (n <= 1) return 1;
    return n * fac(n - 1);
}
int main() {
    printf("%d\\n", fac(5));
    return 0;
}''',
        "rust": '''fn fac(n: i32) -> i32 {
    if n <= 1 { 1 } else { n * fac(n - 1) }
}
fn main() {
    println!("{}", fac(5));
}''',
        "mojo": '''fn fac(n: Int) -> Int:
    if n <= 1: return 1
    return n * fac(n - 1)
fn main():
    print(fac(5))''',
    },
    {
        "name": "斐波那契",
        "desc": "斐波那契数列",
        "x": """% fib(n) {
    ? n == 0 {
        ^ 0
    }
    ? n == 1 {
        ^ 1
    }
    ^ fib(n - 1) + fib(n - 2)
}
# {
    ! fib(10)
}""",
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
    if n == 0: return 0
    if n == 1: return 1
    return fib(n - 1) + fib(n - 2)
fn main():
    print(fib(10))''',
    },

    # ============ 数组 ============
    {
        "name": "数组遍历",
        "desc": "遍历数组元素",
        "x": """% sum(arr, len) {
    $s = 0
    ~i = 0; i < len; i = i + 1 {
        s = s + arr[i]
    }
    ^ s
}
# {
    $arr = [1, 2, 3, 4, 5]
    ! sum(arr, 5)
}""",
        "c": '''#include <stdio.h>
int sum(int arr[], int len) {
    int s = 0;
    for (int i = 0; i < len; i++) {
        s += arr[i];
    }
    return s;
}
int main() {
    int arr[] = {1, 2, 3, 4, 5};
    printf("%d\\n", sum(arr, 5));
    return 0;
}''',
        "rust": '''fn sum(arr: &[i32]) -> i32 {
    arr.iter().sum()
}
fn main() {
    let arr = vec![1, 2, 3, 4, 5];
    println!("{}", sum(&arr));
}''',
        "mojo": '''fn sum(arr: List[Int]) -> Int:
    var s = 0
    for i in range(len(arr)):
        s += arr[i]
    return s
fn main():
    let arr = [1, 2, 3, 4, 5]
    print(sum(arr))''',
    },
    {
        "name": "数组最大值",
        "desc": "查找数组最大元素",
        "x": """% max(arr, len) {
    $m = arr[0]
    ~i = 1; i < len; i = i + 1 {
        ? arr[i] > m {
            m = arr[i]
        }
    }
    ^ m
}
# {
    $arr = [3, 7, 2, 9, 4]
    ! max(arr, 5)
}""",
        "c": '''#include <stdio.h>
int max(int arr[], int len) {
    int m = arr[0];
    for (int i = 1; i < len; i++) {
        if (arr[i] > m) m = arr[i];
    }
    return m;
}
int main() {
    int arr[] = {3, 7, 2, 9, 4};
    printf("%d\\n", max(arr, 5));
    return 0;
}''',
        "rust": '''fn max(arr: &[i32]) -> i32 {
    *arr.iter().max().unwrap()
}
fn main() {
    let arr = vec![3, 7, 2, 9, 4];
    println!("{}", max(&arr));
}''',
        "mojo": '''fn max(arr: List[Int]) -> Int:
    var m = arr[0]
    for i in range(1, len(arr)):
        if arr[i] > m: m = arr[i]
    return m
fn main():
    let arr = [3, 7, 2, 9, 4]
    print(max(arr))''',
    },

    # ============ 字符串 ============
    {
        "name": "字符串长度",
        "desc": "获取字符串长度",
        "x": """% len(s) {
    ^ s.length
}
# {
    ! len("Hello XC")
}""",
        "c": '''#include <stdio.h>
#include <string.h>
int main() {
    printf("%lu\\n", strlen("Hello XC"));
    return 0;
}''',
        "rust": '''fn main() {
    println!("{}", "Hello XC".len());
}''',
        "mojo": '''fn len(s: String) -> Int:
    return len(s)
fn main():
    print(len("Hello XC"))''',
    },
    {
        "name": "字符串连接",
        "desc": "连接两个字符串",
        "x": """% concat(a, b) {
    ^ a + b
}
# {
    ! concat("Hello", " XC")
}""",
        "c": '''#include <stdio.h>
#include <string.h>
int main() {
    char a[] = "Hello";
    char b[] = " XC";
    printf("%s%s\\n", a, b);
    return 0;
}''',
        "rust": '''fn main() {
    let s = String::from("Hello") + " XC";
    println!("{}", s);
}''',
        "mojo": '''fn concat(a: String, b: String) -> String:
    return a + b
fn main():
    print(concat("Hello", " XC"))''',
    },

    # ============ 结构体 ============
    {
        "name": "结构体定义",
        "desc": "定义和使用结构体",
        "x": """& Point {
    x: Int
    y: Int
}
% distance(p1, p2) {
    $dx = p2.x - p1.x
    $dy = p2.y - p1.y
    ^ (dx*dx + dy*dy) ** 0.5
}
# {
    $p1 = Point { x: 0, y: 0 }
    $p2 = Point { x: 3, y: 4 }
    ! distance(p1, p2)
}""",
        "c": '''#include <stdio.h>
#include <math.h>
typedef struct { int x; int y; } Point;
double distance(Point p1, Point p2) {
    int dx = p2.x - p1.x;
    int dy = p2.y - p1.y;
    return sqrt(dx*dx + dy*dy);
}
int main() {
    Point p1 = {0, 0};
    Point p2 = {3, 4};
    printf("%f\\n", distance(p1, p2));
    return 0;
}''',
        "rust": '''struct Point { x: i32, y: i32 }
fn distance(p1: Point, p2: Point) -> f64 {
    let dx = p2.x - p1.x;
    let dy = p2.y - p1.y;
    ((dx*dx + dy*dy) as f64).sqrt()
}
fn main() {
    let p1 = Point { x: 0, y: 0 };
    let p2 = Point { x: 3, y: 4 };
    println!("{}", distance(p1, p2));
}''',
        "mojo": '''struct Point:
    var x: Int
    var y: Int
fn distance(p1: Point, p2: Point) -> Float64:
    let dx = p2.x - p1.x
    let dy = p2.y - p1.y
    return (dx*dx + dy*dy) ** 0.5
fn main():
    let p1 = Point { x: 0, y: 0 }
    let p2 = Point { x: 3, y: 4 }
    print(distance(p1, p2))''',
    },

    # ============ 指针 ============
    {
        "name": "指针操作",
        "desc": "指针基本操作",
        "x": """# {
    $x = 42
    *ptr = &x
    ! *ptr
}""",
        "c": '''#include <stdio.h>
int main() {
    int x = 42;
    int *ptr = &x;
    printf("%d\\n", *ptr);
    return 0;
}''',
        "rust": '''fn main() {
    let x = 42;
    let ptr = &x;
    println!("{}", *ptr);
}''',
        "mojo": '''fn main():
    let x = 42
    let ptr = x
    print(ptr)''',
    },
    {
        "name": "指针运算",
        "desc": "指针算术运算",
        "x": """# {
    $arr = [10, 20, 30]
    *p = &arr[0]
    ! *p
    p = p + 1
    ! *p
}""",
        "c": '''#include <stdio.h>
int main() {
    int arr[] = {10, 20, 30};
    int *p = arr;
    printf("%d\\n", *p);
    p++;
    printf("%d\\n", *p);
    return 0;
}''',
        "rust": '''fn main() {
    let arr = [10, 20, 30];
    let p = &arr[0];
    println!("{}", *p);
    let p2 = unsafe { p.offset(1) };
    println!("{}", *p2);
}''',
        "mojo": '''fn main():
    let arr = [10, 20, 30]
    print(arr[0])
    print(arr[1])''',
    },

    # ============ 高级特性 ============
    {
        "name": "闭包",
        "desc": "匿名函数/闭包",
        "x": """# {
    $add = @(a, b) { ^ a + b }
    ! add(3, 4)
}""",
        "c": '''#include <stdio.h>
int main() {
    int (*add)(int, int) = NULL;
    add = NULL;
    return 0;
}''',
        "rust": '''fn main() {
    let add = |a: i32, b: i32| a + b;
    println!("{}", add(3, 4));
}''',
        "mojo": '''fn main():
    let add = fn(a: Int, b: Int) -> Int: a + b
    print(add(3, 4))''',
    },
    {
        "name": "Option类型",
        "desc": "可选值处理",
        "x": """% find(arr, len, target) {
    ~i = 0; i < len; i = i + 1 {
        ? arr[i] == target {
            ^ Some(i)
        }
    }
    ^ None
}
# {
    $arr = [1, 3, 5, 7]
    $result = find(arr, 4, 5)
    ? result != None {
        ! "Found"
    } ?: {
        ! "Not Found"
    }
}""",
        "c": '''#include <stdio.h>
#include <stdbool.h>
int* find(int arr[], int len, int target) {
    for (int i = 0; i < len; i++) {
        if (arr[i] == target) return &arr[i];
    }
    return NULL;
}
int main() {
    int arr[] = {1, 3, 5, 7};
    int *result = find(arr, 4, 5);
    if (result != NULL) printf("Found\\n");
    else printf("Not Found\\n");
    return 0;
}''',
        "rust": '''fn find(arr: &[i32], target: i32) -> Option<usize> {
    arr.iter().position(|&x| x == target)
}
fn main() {
    let arr = vec![1, 3, 5, 7];
    match find(&arr, 5) {
        Some(i) => println!("Found at {}", i),
        None => println!("Not Found"),
    }
}''',
        "mojo": '''fn find(arr: List[Int], target: Int) -> Optional[Int]:
    for i in range(len(arr)):
        if arr[i] == target: return Optional(i)
    return None
fn main():
    let arr = [1, 3, 5, 7]
    let result = find(arr, 5)
    print(result)''',
    },
    {
        "name": "迭代器链式",
        "desc": "链式函数调用",
        "x": """# {
    $arr = [1, 2, 3, 4, 5]
    $result = arr.filter(@(x) { ^ x % 2 == 1 }).map(@(x) { ^ x * 2 }).sum()
    ! result
}""",
        "c": '''#include <stdio.h>
int main() {
    int arr[] = {1, 2, 3, 4, 5};
    int result = 0;
    for (int i = 0; i < 5; i++) {
        if (arr[i] % 2 == 1) {
            result += arr[i] * 2;
        }
    }
    printf("%d\\n", result);
    return 0;
}''',
        "rust": '''fn main() {
    let arr = vec![1, 2, 3, 4, 5];
    let result: i32 = arr.iter()
        .filter(|&&x| x % 2 == 1)
        .map(|&x| x * 2)
        .sum();
    println!("{}", result);
}''',
        "mojo": '''fn main():
    let arr = [1, 2, 3, 4, 5]
    var result = 0
    for x in arr:
        if x % 2 == 1:
            result += x * 2
    print(result)''',
    },

    # ============ 算法实现 ============
    {
        "name": "冒泡排序",
        "desc": "基础排序算法",
        "x": """% bubble_sort(arr, n) {
    ~i = 0; i < n - 1; i = i + 1 {
        ~j = 0; j < n - i - 1; j = j + 1 {
            ? arr[j] > arr[j + 1] {
                $tmp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = tmp
            }
        }
    }
}
# {
    $arr = [64, 34, 25, 12, 22]
    bubble_sort(arr, 5)
    ! arr
}""",
        "c": '''#include <stdio.h>
void bubble_sort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int tmp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = tmp;
            }
        }
    }
}
int main() {
    int arr[] = {64, 34, 25, 12, 22};
    bubble_sort(arr, 5);
    for (int i = 0; i < 5; i++) printf("%d ", arr[i]);
    return 0;
}''',
        "rust": '''fn bubble_sort(arr: &mut [i32]) {
    let n = arr.len();
    for i in 0..n {
        for j in 0..n - i - 1 {
            if arr[j] > arr[j + 1] {
                arr.swap(j, j + 1);
            }
        }
    }
}
fn main() {
    let mut arr = vec![64, 34, 25, 12, 22];
    bubble_sort(&mut arr);
    println!("{:?}", arr);
}''',
        "mojo": '''fn bubble_sort(arr: List[Int]):
    for i in range(len(arr) - 1):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j + 1]:
                let tmp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = tmp
fn main():
    let arr = [64, 34, 25, 12, 22]
    bubble_sort(arr)
    print(arr)''',
    },
    {
        "name": "二分查找",
        "desc": "折半搜索算法",
        "x": """% binary_search(arr, n, target) {
    $left = 0
    $right = n - 1
    @left <= right {
        $mid = (left + right) / 2
        ? arr[mid] == target {
            ^ Some(mid)
        } ?? arr[mid] < target {
            left = mid + 1
        } ?: {
            right = mid - 1
        }
    }
    ^ None
}
# {
    $arr = [1, 3, 5, 7, 9, 11]
    ! binary_search(arr, 6, 7)
}""",
        "c": '''#include <stdio.h>
int binary_search(int arr[], int n, int target) {
    int left = 0, right = n - 1;
    while (left <= right) {
        int mid = (left + right) / 2;
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
int main() {
    int arr[] = {1, 3, 5, 7, 9, 11};
    printf("%d\\n", binary_search(arr, 6, 7));
    return 0;
}''',
        "rust": '''fn binary_search(arr: &[i32], target: i32) -> Option<usize> {
    let mut left = 0;
    let mut right = arr.len();
    while left < right {
        let mid = (left + right) / 2;
        if arr[mid] == target { return Some(mid); }
        else if arr[mid] < target { left = mid + 1; }
        else { right = mid; }
    }
    None
}
fn main() {
    let arr = vec![1, 3, 5, 7, 9, 11];
    println!("{:?}", binary_search(&arr, 7));
}''',
        "mojo": '''fn binary_search(arr: List[Int], target: Int) -> Optional[Int]:
    var left = 0
    var right = len(arr) - 1
    while left <= right:
        let mid = (left + right) // 2
        if arr[mid] == target: return Optional(mid)
        elif arr[mid] < target: left = mid + 1
        else: right = mid - 1
    return None
fn main():
    let arr = [1, 3, 5, 7, 9, 11]
    print(binary_search(arr, 7))''',
    },
    {
        "name": "素数判定",
        "desc": "判断是否为素数",
        "x": """% is_prime(n) {
    ? n < 2 {
        ^ false
    }
    ~i = 2; i * i <= n; i = i + 1 {
        ? n % i == 0 {
            ^ false
        }
    }
    ^ true
}
# {
    ~n = 2; n <= 20; n = n + 1 {
        ? is_prime(n) {
            ! n
        }
    }
}""",
        "c": '''#include <stdio.h>
int is_prime(int n) {
    if (n < 2) return 0;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return 0;
    }
    return 1;
}
int main() {
    for (int n = 2; n <= 20; n++) {
        if (is_prime(n)) printf("%d ", n);
    }
    return 0;
}''',
        "rust": '''fn is_prime(n: i32) -> bool {
    if n < 2 { return false; }
    for i in 2.. {
        if i * i > n { break; }
        if n % i == 0 { return false; }
    }
    true
}
fn main() {
    for n in 2..=20 {
        if is_prime(n) { print!("{} ", n); }
    }
}''',
        "mojo": '''fn is_prime(n: Int) -> Bool:
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True
fn main():
    for n in range(2, 21):
        if is_prime(n): print(n, " ")''',
    },
    {
        "name": "水仙花数",
        "desc": "三位自幂数",
        "x": """# {
    ~n = 100; n < 1000; n = n + 1 {
        $a = n / 100
        $b = (n % 100) / 10
        $c = n % 10
        ? a*a*a + b*b*b + c*c*c == n {
            ! n
        }
    }
}""",
        "c": '''#include <stdio.h>
int main() {
    for (int n = 100; n < 1000; n++) {
        int a = n / 100, b = (n / 10) % 10, c = n % 10;
        if (a*a*a + b*b*b + c*c*c == n) {
            printf("%d\\n", n);
        }
    }
    return 0;
}''',
        "rust": '''fn main() {
    for n in 100..1000 {
        let a = n / 100;
        let b = (n / 10) % 10;
        let c = n % 10;
        if a*a*a + b*b*b + c*c*c == n {
            println!("{}", n);
        }
    }
}''',
        "mojo": '''fn main():
    for n in range(100, 1000):
        let a = n // 100
        let b = (n // 10) % 10
        let c = n % 10
        if a*a*a + b*b*b + c*c*c == n:
            print(n)''',
    },

    # ============ 内存管理 ============
    {
        "name": "动态内存分配",
        "desc": "堆内存分配",
        "x": """# {
    *p = malloc(4)
    *p = 42
    ! *p
    free(p)
}""",
        "c": '''#include <stdio.h>
#include <stdlib.h>
int main() {
    int *p = malloc(sizeof(int));
    *p = 42;
    printf("%d\\n", *p);
    free(p);
    return 0;
}''',
        "rust": '''fn main() {
    let p = Box::new(42);
    println!("{}", *p);
}''',
        "mojo": '''fn main():
    let p = alloc(1)
    p[0] = 42
    print(p[0])
    free(p)''',
    },

    # ============ 错误处理 ============
    {
        "name": "错误处理",
        "desc": "Result类型错误处理",
        "x": """% divide(a, b) {
    ? b == 0 {
        ^ Err("division by zero")
    }
    ^ Ok(a / b)
}
# {
    $result = divide(10, 0)
    ? result.kind == Ok {
        ! result.value
    } ?: {
        ! result.error
    }
}""",
        "c": '''#include <stdio.h>
#include <errno.h>
double divide(int a, int b, int *err) {
    if (b == 0) { *err = 1; return 0; }
    *err = 0;
    return (double)a / b;
}
int main() {
    int err = 0;
    double result = divide(10, 0, &err);
    if (err) printf("division by zero\\n");
    else printf("%f\\n", result);
    return 0;
}''',
        "rust": '''fn divide(a: i32, b: i32) -> Result<i32, &'static str> {
    if b == 0 { Err("division by zero") }
    else { Ok(a / b) }
}
fn main() {
    match divide(10, 0) {
        Ok(v) => println!("{}", v),
        Err(e) => println!("{}", e),
    }
}''',
        "mojo": '''fn divide(a: Int, b: Int) raises -> Int:
    if b == 0: raise Error("division by zero")
    return a // b
fn main():
    try:
        print(divide(10, 0))
    except e:
        print(e)''',
    },

    # ============ 并发 ============
    {
        "name": "并发编程",
        "desc": "线程创建",
        "x": """# {
    thread {
        ! "Thread 1"
    }
    thread {
        ! "Thread 2"
    }
    sleep(100)
}""",
        "c": '''#include <stdio.h>
#include <pthread.h>
void* thread1(void* arg) {
    printf("Thread 1\\n");
    return NULL;
}
void* thread2(void* arg) {
    printf("Thread 2\\n");
    return NULL;
}
int main() {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, thread1, NULL);
    pthread_create(&t2, NULL, thread2, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    return 0;
}''',
        "rust": '''use std::thread;
use std::time::Duration;
fn main() {
    let t1 = thread::spawn(|| { println!("Thread 1"); });
    let t2 = thread::spawn(|| { println!("Thread 2"); });
    thread::sleep(Duration::from_millis(100));
    t1.join().unwrap();
    t2.join().unwrap();
}''',
        "mojo": '''fn main():
    @spawn:
        print("Thread 1")
    @spawn:
        print("Thread 2")
    sleep(100)''',
    },
]

try:
    from dataset.xc_fusion_handbook_samples import HANDBOOK_FUSION_SAMPLES
    X_CODE_SAMPLES.extend(HANDBOOK_FUSION_SAMPLES)
except ImportError:
    pass


def get_all_samples():
    """获取所有样本"""
    return X_CODE_SAMPLES


def generate_pairs():
    """生成所有语言对"""
    pairs = []
    for sample in X_CODE_SAMPLES:
        langs = ["x", "c", "rust", "mojo"]
        for src in langs:
            for tgt in langs:
                if src != tgt:
                    pairs.append({
                        "id": f"{src}2{tgt}_{sample['name']}",
                        "source_lang": src,
                        "target_lang": tgt,
                        "source_code": sample[src],
                        "target_code": sample[tgt],
                        "name": sample["name"],
                        "desc": sample["desc"],
                    })
    return pairs


if __name__ == "__main__":
    samples = get_all_samples()
    print(f"共 {len(samples)} 个四语对照样本")
    for s in samples[:3]:
        print(f"  - {s['name']}: {s['desc']}")
