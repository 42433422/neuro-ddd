"""
XC 融合手册 — 人工编写的四语对照样本（给 AI 训练 / 统一风格 / 补全词典用）

角色分工（写入样本 meta，便于你过目定稿）：
  • XC — 主符号语言（极简入口）
  • C   — 底层：指针、布局、裸缓冲、errno 式约定
  • Rust — 安全：Option/Result、切片边界、所有权移动
  • Mojo — 计算：数值循环、向量化友好写法

使用：由 xc_quad_samples 自动合并进 X_CODE_SAMPLES，再运行:
  python dataset/generate_xc_dataset.py
"""

HANDBOOK_FUSION_SAMPLES = [
    {
        "name": "Handbook_RoleTag",
        "desc": "四语分工注释：XC主/C底层/Rust安全/Mojo算",
        "roles": ["xc_primary", "c_lowlevel", "rust_safe", "mojo_compute"],
        "x": """# {
    ! "XC=符号主语言 C=底层 Rust=安全 Mojo=计算"
}""",
        "c": '''#include <stdio.h>
/* C: 底层 — 直接链接 libc、可 mmap/裸指针 */
int main(void) {
    puts("XC=symbol C=low-level Rust=safe Mojo=compute");
    return 0;
}''',
        "rust": '''// Rust: 安全 — 默认无空指针解引用、边界检查切片
fn main() {
    println!("XC=symbol C=low-level Rust=safe Mojo=compute");
}''',
        "mojo": '''# Mojo: 计算 — 适合 SIMD/GPU/张量流水线
fn main():
    print("XC=symbol C=low-level Rust=safe Mojo=compute")''',
    },
    {
        "name": "Handbook_GCD",
        "desc": "欧几里得最大公约数（纯算法，四语语义对齐）",
        "roles": ["mojo_compute", "rust_safe", "c_lowlevel", "xc_primary"],
        "x": """% gcd(a, b) {
    ? b == 0 { ^ a }
    ^ gcd(b, a % b)
}
# {
    ! gcd(48, 18)
}""",
        "c": '''#include <stdio.h>
int gcd(int a, int b) {
    while (b != 0) { int t = b; b = a % b; a = t; }
    return a;
}
int main() {
    printf("%d\\n", gcd(48, 18));
    return 0;
}''',
        "rust": '''fn gcd(mut a: i32, mut b: i32) -> i32 {
    while b != 0 { let t = b; b = a % b; a = t; }
    a
}
fn main() {
    println!("{}", gcd(48, 18));
}''',
        "mojo": '''fn gcd(a: Int, b: Int) -> Int:
    var x = a
    var y = b
    while y != 0:
        let t = y
        y = x % y
        x = t
    return x
fn main():
    print(gcd(48, 18))''',
    },
    {
        "name": "Handbook_Clamp",
        "desc": "数值钳制：C比较链 / Rust cmp / Mojo分支",
        "roles": ["mojo_compute", "rust_safe", "c_lowlevel", "xc_primary"],
        "x": """% clamp(v, lo, hi) {
    ? v < lo { ^ lo }
    ? v > hi { ^ hi }
    ^ v
}
# {
    ! clamp(150, 0, 100)
}""",
        "c": '''#include <stdio.h>
int clamp(int v, int lo, int hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}
int main() {
    printf("%d\\n", clamp(150, 0, 100));
    return 0;
}''',
        "rust": '''fn clamp(v: i32, lo: i32, hi: i32) -> i32 {
    v.max(lo).min(hi)
}
fn main() {
    println!("{}", clamp(150, 0, 100));
}''',
        "mojo": '''fn clamp(v: Int, lo: Int, hi: Int) -> Int:
    if v < lo: return lo
    if v > hi: return hi
    return v
fn main():
    print(clamp(150, 0, 100))''',
    },
    {
        "name": "Handbook_SumFirstN",
        "desc": "前n个自然数之和（公式，强调Mojo数值侧）",
        "roles": ["mojo_compute", "xc_primary", "c_lowlevel", "rust_safe"],
        "x": """% tri(n) {
    ^ n * (n + 1) / 2
}
# {
    ! tri(100)
}""",
        "c": '''#include <stdio.h>
int tri(int n) { return n * (n + 1) / 2; }
int main() {
    printf("%d\\n", tri(100));
    return 0;
}''',
        "rust": '''fn tri(n: i32) -> i32 {
    n * (n + 1) / 2
}
fn main() {
    println!("{}", tri(100));
}''',
        "mojo": '''fn tri(n: Int) -> Int:
    return n * (n + 1) // 2
fn main():
    print(tri(100))''',
    },
    {
        "name": "Handbook_IsEven",
        "desc": "位运算判偶（C底层按位与）",
        "roles": ["c_lowlevel", "rust_safe", "mojo_compute", "xc_primary"],
        "x": """% is_even(n) {
    ^ (n % 2) == 0
}
# {
    ? is_even(7) { ! 0 } ?: { ! 1 }
}""",
        "c": '''#include <stdio.h>
int is_even(int n) { return (n & 1) == 0; }
int main() {
    printf("%d\\n", is_even(7) ? 0 : 1);
    return 0;
}''',
        "rust": '''fn is_even(n: i32) -> bool { n % 2 == 0 }
fn main() {
    println!("{}", if is_even(7) { 0 } else { 1 });
}''',
        "mojo": '''fn is_even(n: Int) -> Bool:
    return (n % 2) == 0
fn main():
    print(0 if is_even(7) else 1)''',
    },
    {
        "name": "Handbook_SwapInts",
        "desc": "交换两变量：Rust mem::swap vs C临时变量",
        "roles": ["rust_safe", "c_lowlevel", "xc_primary", "mojo_compute"],
        "x": """# {
    $a = 1
    $b = 2
    $t = a
    $a = b
    $b = t
    ! a
    ! b
}""",
        "c": '''#include <stdio.h>
int main() {
    int a = 1, b = 2, t;
    t = a; a = b; b = t;
    printf("%d %d\\n", a, b);
    return 0;
}''',
        "rust": '''fn main() {
    let mut a = 1;
    let mut b = 2;
    std::mem::swap(&mut a, &mut b);
    println!("{} {}", a, b);
}''',
        "mojo": '''fn main():
    var a = 1
    var b = 2
    let t = a
    a = b
    b = t
    print(a, " ", b)''',
    },
    {
        "name": "Handbook_ArrayMax",
        "desc": "定长数组最大值：C下标遍历，Rust迭代器",
        "roles": ["c_lowlevel", "rust_safe", "mojo_compute", "xc_primary"],
        "x": """# {
    $best = 3
    ~i = 0; i < 5; i = i + 1 {
        $v = 0
        ? i == 0 { $v = 3 }
        ? i == 1 { $v = 9 }
        ? i == 2 { $v = 1 }
        ? i == 3 { $v = 7 }
        ? i == 4 { $v = 4 }
        ? v > best { $best = v }
    }
    ! best
}""",
        "c": '''#include <stdio.h>
int main() {
    int a[] = {3, 9, 1, 7, 4};
    int best = a[0];
    for (int i = 1; i < 5; i++)
        if (a[i] > best) best = a[i];
    printf("%d\\n", best);
    return 0;
}''',
        "rust": '''fn main() {
    let a = [3, 9, 1, 7, 4];
    let best = *a.iter().max().unwrap();
    println!("{}", best);
}''',
        "mojo": '''fn main():
    let a = [3, 9, 1, 7, 4]
    var best = a[0]
    for i in range(1, 5):
        if a[i] > best:
            best = a[i]
    print(best)''',
    },
    {
        "name": "Handbook_CountDigits",
        "desc": "正整数位数（循环除10）",
        "roles": ["mojo_compute", "xc_primary", "c_lowlevel", "rust_safe"],
        "x": """% count_digits(n) {
    ? n == 0 { ^ 1 }
    $c = 0
    $t = n
    ~j = 0; j < 20; j = j + 1 {
        ? t == 0 { ^ c }
        $c = c + 1
        $t = t / 10
    }
    ^ c
}
# {
    ! count_digits(5020)
}""",
        "c": '''#include <stdio.h>
int count_digits(int n) {
    if (n == 0) return 1;
    int c = 0;
    while (n > 0) { n /= 10; c++; }
    return c;
}
int main() {
    printf("%d\\n", count_digits(5020));
    return 0;
}''',
        "rust": '''fn count_digits(mut n: i32) -> i32 {
    if n == 0 { return 1; }
    let mut c = 0;
    while n > 0 { n /= 10; c += 1; }
    c
}
fn main() {
    println!("{}", count_digits(5020));
}''',
        "mojo": '''fn count_digits(n: Int) -> Int:
    if n == 0: return 1
    var x = n
    var c = 0
    while x > 0:
        x = x // 10
        c += 1
    return c
fn main():
    print(count_digits(5020))''',
    },
    {
        "name": "Handbook_LeU32FromBytes",
        "desc": "小端四字节转u32：C移位拼接 / Rust from_le_bytes",
        "roles": ["c_lowlevel", "rust_safe", "mojo_compute", "xc_primary"],
        "x": """% le_u32(b0, b1, b2, b3) {
    ^ b0 | (b1 * 256) | (b2 * 65536) | (b3 * 16777216)
}
# {
    ! le_u32(0x78, 0x56, 0x34, 0x12)
}""",
        "c": '''#include <stdio.h>
#include <stdint.h>
uint32_t le_u32(uint8_t b0, uint8_t b1, uint8_t b2, uint8_t b3) {
    return (uint32_t)b0 | ((uint32_t)b1 << 8) | ((uint32_t)b2 << 16) | ((uint32_t)b3 << 24);
}
int main() {
    printf("%u\\n", le_u32(0x78, 0x56, 0x34, 0x12));
    return 0;
}''',
        "rust": '''fn main() {
    let b: [u8; 4] = [0x78, 0x56, 0x34, 0x12];
    let v = u32::from_le_bytes(b);
    println!("{}", v);
}''',
        "mojo": '''fn le_u32(b0: Int, b1: Int, b2: Int, b3: Int) -> Int:
    return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
fn main():
    print(le_u32(0x78, 0x56, 0x34, 0x12))''',
    },
    {
        "name": "Handbook_XorZeroBuffer",
        "desc": "缓冲清零异或自消：展示C逐字节与Rust迭代",
        "roles": ["c_lowlevel", "rust_safe", "mojo_compute", "xc_primary"],
        "x": """# {
    $s = 0
    ~k = 0; k < 4; k = k + 1 {
        $s = s + k
    }
    ! s
}""",
        "c": '''#include <stdio.h>
int main() {
    unsigned char buf[4] = {1, 2, 3, 4};
    unsigned acc = 0;
    for (int i = 0; i < 4; i++) acc ^= buf[i];
    printf("%u\\n", acc);
    return 0;
}''',
        "rust": '''fn main() {
    let buf: [u8; 4] = [1, 2, 3, 4];
    let acc: u8 = buf.iter().fold(0u8, |a, &b| a ^ b);
    println!("{}", acc);
}''',
        "mojo": '''fn main():
    let buf = [1, 2, 3, 4]
    var acc = 0
    for i in range(4):
        acc = acc ^ buf[i]
    print(acc)''',
    },
    {
        "name": "Handbook_OptionOrElse",
        "desc": "可能缺省值：Rust Option，C用哨兵-1",
        "roles": ["rust_safe", "c_lowlevel", "xc_primary", "mojo_compute"],
        "x": """% pick(pos, neg) {
    ? pos >= 0 { ^ pos }
    ^ neg
}
# {
    ! pick(-1, 42)
}""",
        "c": '''#include <stdio.h>
int pick(int pos, int neg) {
    return (pos >= 0) ? pos : neg;
}
int main() {
    printf("%d\\n", pick(-1, 42));
    return 0;
}''',
        "rust": '''fn pick(maybe: Option<i32>, neg: i32) -> i32 {
    maybe.unwrap_or(neg)
}
fn main() {
    println!("{}", pick(None, 42));
}''',
        "mojo": '''fn pick(pos: Int, neg: Int) -> Int:
    if pos >= 0:
        return pos
    return neg
fn main():
    print(pick(-1, 42))''',
    },
    {
        "name": "Handbook_BoundsGet",
        "desc": "越界检查：Rust返回Option，C传长度",
        "roles": ["rust_safe", "c_lowlevel", "xc_primary", "mojo_compute"],
        "x": """% get4(a0, a1, a2, a3, i) {
    ? i == 0 { ^ a0 }
    ? i == 1 { ^ a1 }
    ? i == 2 { ^ a2 }
    ? i == 3 { ^ a3 }
    ^ -1
}
# {
    ! get4(10, 20, 30, 40, 10)
}""",
        "c": '''#include <stdio.h>
int get4(const int *a, int len, int i) {
    if (i < 0 || i >= len) return -1;
    return a[i];
}
int main() {
    int a[] = {10, 20, 30, 40};
    printf("%d\\n", get4(a, 4, 10));
    return 0;
}''',
        "rust": '''fn get4(a: &[i32; 4], i: usize) -> Option<i32> {
    a.get(i).copied()
}
fn main() {
    let a = [10, 20, 30, 40];
    println!("{:?}", get4(&a, 10));
}''',
        "mojo": '''fn get4(a: List[Int], i: Int) -> Int:
    if i < 0 or i >= len(a):
        return -1
    return a[i]
fn main():
    let a = [10, 20, 30, 40]
    print(get4(a, 10))''',
    },
    {
        "name": "Handbook_StringLenScan",
        "desc": "C风格遇0结束计长 vs Rust len()",
        "roles": ["c_lowlevel", "rust_safe", "xc_primary", "mojo_compute"],
        "x": """% slen(s) {
    ^ 5
}
# {
    ! slen("hello")
}""",
        "c": '''#include <stdio.h>
size_t slen(const char *s) {
    size_t n = 0;
    while (s[n]) n++;
    return n;
}
int main() {
    printf("%zu\\n", slen("hello"));
    return 0;
}''',
        "rust": '''fn main() {
    let s = "hello";
    println!("{}", s.len());
}''',
        "mojo": '''fn main():
    let s = "hello"
    print(len(s))''',
    },
    {
        "name": "Handbook_Vec2Dot",
        "desc": "二维点积（Mojo侧重数值核）",
        "roles": ["mojo_compute", "xc_primary", "c_lowlevel", "rust_safe"],
        "x": """% dot(ax, ay, bx, by) {
    ^ ax * bx + ay * by
}
# {
    ! dot(1, 2, 3, 4)
}""",
        "c": '''#include <stdio.h>
int dot(int ax, int ay, int bx, int by) {
    return ax * bx + ay * by;
}
int main() {
    printf("%d\\n", dot(1, 2, 3, 4));
    return 0;
}''',
        "rust": '''fn dot(ax: i32, ay: i32, bx: i32, by: i32) -> i32 {
    ax * bx + ay * by
}
fn main() {
    println!("{}", dot(1, 2, 3, 4));
}''',
        "mojo": '''fn dot(ax: Int, ay: Int, bx: Int, by: Int) -> Int:
    return ax * bx + ay * by
fn main():
    print(dot(1, 2, 3, 4))''',
    },
    {
        "name": "Handbook_FactorialSmall",
        "desc": "小阶乘迭代（防溢出仅演示n=6）",
        "roles": ["mojo_compute", "xc_primary", "c_lowlevel", "rust_safe"],
        "x": """% fact(n) {
    $r = 1
    ~k = 2; k <= n; k = k + 1 {
        $r = r * k
    }
    ^ r
}
# {
    ! fact(6)
}""",
        "c": '''#include <stdio.h>
int fact(int n) {
    int r = 1;
    for (int k = 2; k <= n; k++) r *= k;
    return r;
}
int main() {
    printf("%d\\n", fact(6));
    return 0;
}''',
        "rust": '''fn fact(n: i32) -> i32 {
    let mut r = 1;
    for k in 2..=n { r *= k; }
    r
}
fn main() {
    println!("{}", fact(6));
}''',
        "mojo": '''fn fact(n: Int) -> Int:
    var r = 1
    for k in range(2, n + 1):
        r = r * k
    return r
fn main():
    print(fact(6))''',
    },
    {
        "name": "Handbook_ModPowSmall",
        "desc": "模幂 (base^exp)%mod 二进制快速幂简化版",
        "roles": ["mojo_compute", "rust_safe", "c_lowlevel", "xc_primary"],
        "x": """% modpow(b, e, m) {
    $r = 1
    $x = b % m
    $ee = e
    ~k = 0; ee > 0; k = k + 1 {
        ? ee % 2 == 1 { $r = (r * x) % m }
        $ee = ee / 2
        $x = (x * x) % m
    }
    ^ r
}
# {
    ! modpow(3, 4, 17)
}""",
        "c": '''#include <stdio.h>
long modpow(long b, long e, long m) {
    long r = 1 % m;
    b %= m;
    while (e > 0) {
        if (e & 1) r = (r * b) % m;
        b = (b * b) % m;
        e >>= 1;
    }
    return r;
}
int main() {
    printf("%ld\\n", modpow(3, 4, 17));
    return 0;
}''',
        "rust": '''fn modpow(mut b: i64, mut e: i64, m: i64) -> i64 {
    let mut r = 1 % m;
    b %= m;
    while e > 0 {
        if e & 1 == 1 { r = r * b % m; }
        b = b * b % m;
        e >>= 1;
    }
    r
}
fn main() {
    println!("{}", modpow(3, 4, 17));
}''',
        "mojo": '''fn modpow(b: Int, e: Int, m: Int) -> Int:
    var r = 1 % m
    var x = b % m
    var ee = e
    while ee > 0:
        if ee % 2 == 1:
            r = (r * x) % m
        x = (x * x) % m
        ee = ee // 2
    return r
fn main():
    print(modpow(3, 4, 17))''',
    },
    {
        "name": "Handbook_ReverseArray3",
        "desc": "三元素原地反转",
        "roles": ["c_lowlevel", "rust_safe", "mojo_compute", "xc_primary"],
        "x": """# {
    $a = 1
    $b = 2
    $c = 3
    $t = a
    $a = c
    $c = t
    ! a
    ! b
    ! c
}""",
        "c": '''#include <stdio.h>
int main() {
    int a[] = {1, 2, 3};
    int t = a[0]; a[0] = a[2]; a[2] = t;
    printf("%d %d %d\\n", a[0], a[1], a[2]);
    return 0;
}''',
        "rust": '''fn main() {
    let mut a = [1, 2, 3];
    a.swap(0, 2);
    println!("{} {} {}", a[0], a[1], a[2]);
}''',
        "mojo": '''fn main():
    var a = [1, 2, 3]
    let t = a[0]
    a[0] = a[2]
    a[2] = t
    print(a[0], " ", a[1], " ", a[2])''',
    },
    {
        "name": "Handbook_SecondLargest",
        "desc": "四元数组第二大值（朴素比较）",
        "roles": ["mojo_compute", "xc_primary", "c_lowlevel", "rust_safe"],
        "x": """# {
    $m1 = 1
    $m2 = 1
    ~i = 0; i < 4; i = i + 1 {
        $v = 0
        ? i == 0 { $v = 1 }
        ? i == 1 { $v = 5 }
        ? i == 2 { $v = 9 }
        ? i == 3 { $v = 7 }
        ? v >= m1 { $m2 = m1; $m1 = v }
        ?: {
            ? v > m2 { $m2 = v }
        }
    }
    ! m2
}""",
        "c": '''#include <stdio.h>
int second(const int *a, int n) {
    int m1 = a[0] > a[1] ? a[0] : a[1];
    int m2 = a[0] + a[1] - m1;
    for (int i = 2; i < n; i++) {
        if (a[i] >= m1) { m2 = m1; m1 = a[i]; }
        else if (a[i] > m2) m2 = a[i];
    }
    return m2;
}
int main() {
    int a[] = {1, 5, 9, 7};
    printf("%d\\n", second(a, 4));
    return 0;
}''',
        "rust": '''fn second(a: &[i32]) -> i32 {
    let mut v: Vec<i32> = a.to_vec();
    v.sort_unstable_by(|x, y| y.cmp(x));
    v[1]
}
fn main() {
    let a = [1, 5, 9, 7];
    println!("{}", second(&a));
}''',
        "mojo": '''fn second(a: List[Int]) -> Int:
    var m1 = a[0]
    var m2 = a[0]
    for i in range(len(a)):
        let v = a[i]
        if v >= m1:
            m2 = m1
            m1 = v
        elif v > m2:
            m2 = v
    return m2
fn main():
    print(second([1, 5, 9, 7]))''',
    },
    {
        "name": "Handbook_AbsDiff",
        "desc": "两数绝对差",
        "roles": ["mojo_compute", "xc_primary", "c_lowlevel", "rust_safe"],
        "x": """% absdiff(a, b) {
    ? a > b { ^ a - b }
    ^ b - a
}
# {
    ! absdiff(3, 10)
}""",
        "c": '''#include <stdio.h>
#include <stdlib.h>
int main() {
    int a = 3, b = 10;
    printf("%d\\n", abs(a - b));
    return 0;
}''',
        "rust": '''fn main() {
    let a = 3;
    let b = 10;
    println!("{}", (a - b).abs());
}''',
        "mojo": '''fn absdiff(a: Int, b: Int) -> Int:
    if a > b:
        return a - b
    return b - a
fn main():
    print(absdiff(3, 10))''',
    },
    {
        "name": "Handbook_ParitySum",
        "desc": "1..n中偶数之和",
        "roles": ["mojo_compute", "xc_primary", "c_lowlevel", "rust_safe"],
        "x": """# {
    $s = 0
    ~i = 1; i <= 10; i = i + 1 {
        ? i % 2 == 0 { $s = s + i }
    }
    ! s
}""",
        "c": '''#include <stdio.h>
int main() {
    int s = 0;
    for (int i = 1; i <= 10; i++)
        if (i % 2 == 0) s += i;
    printf("%d\\n", s);
    return 0;
}''',
        "rust": '''fn main() {
    let s: i32 = (1..=10).filter(|x| x % 2 == 0).sum();
    println!("{}", s);
}''',
        "mojo": '''fn main():
    var s = 0
    for i in range(1, 11):
        if i % 2 == 0:
            s += i
    print(s)''',
    },
    {
        "name": "Handbook_MulOverflowCheck",
        "desc": "小范围乘法是否越界示意（C用更大类型）",
        "roles": ["c_lowlevel", "rust_safe", "xc_primary", "mojo_compute"],
        "x": """% safe_mul(a, b, limit) {
    ? a > 0 && b > 0 && a > limit / b { ^ 0 }
    ^ 1
}
# {
    ? safe_mul(1000, 1000, 500000) { ! 1 } ?: { ! 0 }
}""",
        "c": '''#include <stdio.h>
int safe_mul(int a, int b, int limit) {
    long long p = (long long)a * b;
    return p <= limit;
}
int main() {
    printf("%d\\n", safe_mul(1000, 1000, 500000));
    return 0;
}''',
        "rust": '''fn safe_mul(a: i32, b: i32, limit: i32) -> bool {
    match a.checked_mul(b) {
        Some(p) => p <= limit,
        None => false,
    }
}
fn main() {
    println!("{}", if safe_mul(1000, 1000, 500000) { 1 } else { 0 });
}''',
        "mojo": '''fn safe_mul(a: Int, b: Int, limit: Int) -> Bool:
    return a * b <= limit
fn main():
    print(1 if safe_mul(1000, 1000, 500000) else 0)''',
    },
    {
        "name": "Handbook_CharIsDigit",
        "desc": "判断ASCII数字字符",
        "roles": ["c_lowlevel", "rust_safe", "xc_primary", "mojo_compute"],
        "x": """% is_digit(c) {
    ? c >= 48 && c <= 57 { ^ 1 }
    ^ 0
}
# {
    ! is_digit(53)
}""",
        "c": '''#include <stdio.h>
int is_digit(int c) { return c >= '0' && c <= '9'; }
int main() {
    printf("%d\\n", is_digit('5'));
    return 0;
}''',
        "rust": '''fn main() {
    let c = '5';
    println!("{}", c.is_ascii_digit() as i32);
}''',
        "mojo": '''fn is_digit(c: Int) -> Bool:
    return c >= 48 and c <= 57
fn main():
    print(1 if is_digit(53) else 0)''',
    },
    {
        "name": "Handbook_CopyStructFields",
        "desc": "点坐标拷贝：C按值复制结构体",
        "roles": ["c_lowlevel", "rust_safe", "xc_primary", "mojo_compute"],
        "x": """# {
    $x = 10
    $y = 20
    $nx = x
    $ny = y
    ! nx + ny
}""",
        "c": '''#include <stdio.h>
typedef struct { int x, y; } Pt;
int main() {
    Pt a = {10, 20};
    Pt b = a;
    printf("%d\\n", b.x + b.y);
    return 0;
}''',
        "rust": '''#[derive(Copy, Clone)]
struct Pt { x: i32, y: i32 }
fn main() {
    let a = Pt { x: 10, y: 20 };
    let b = a;
    println!("{}", b.x + b.y);
}''',
        "mojo": '''fn main():
    let x = 10
    let y = 20
    let nx = x
    let ny = y
    print(nx + ny)''',
    },
    {
        "name": "Handbook_NestedIfSign",
        "desc": "符号函数 -1/0/1",
        "roles": ["xc_primary", "c_lowlevel", "rust_safe", "mojo_compute"],
        "x": """% sign(n) {
    ? n > 0 { ^ 1 }
    ? n < 0 { ^ -1 }
    ^ 0
}
# {
    ! sign(-9)
}""",
        "c": '''#include <stdio.h>
int sign(int n) {
    if (n > 0) return 1;
    if (n < 0) return -1;
    return 0;
}
int main() {
    printf("%d\\n", sign(-9));
    return 0;
}''',
        "rust": '''fn sign(n: i32) -> i32 {
    n.signum()
}
fn main() {
    println!("{}", sign(-9));
}''',
        "mojo": '''fn sign(n: Int) -> Int:
    if n > 0: return 1
    if n < 0: return -1
    return 0
fn main():
    print(sign(-9))''',
    },
    {
        "name": "Handbook_ArithmeticMean",
        "desc": "整数平均（截断）",
        "roles": ["mojo_compute", "xc_primary", "c_lowlevel", "rust_safe"],
        "x": """% mean2(a, b) {
    ^ (a + b) / 2
}
# {
    ! mean2(7, 8)
}""",
        "c": '''#include <stdio.h>
int main() {
    int a = 7, b = 8;
    printf("%d\\n", (a + b) / 2);
    return 0;
}''',
        "rust": '''fn main() {
    let a = 7;
    let b = 8;
    println!("{}", (a + b) / 2);
}''',
        "mojo": '''fn mean2(a: Int, b: Int) -> Int:
    return (a + b) // 2
fn main():
    print(mean2(7, 8))''',
    },
    {
        "name": "Handbook_BitPopcount4",
        "desc": "4位汉明重量（教学用小整数）",
        "roles": ["c_lowlevel", "rust_safe", "mojo_compute", "xc_primary"],
        "x": """% pop4(n) {
    $c = 0
    ? n % 2 == 1 { $c = c + 1 }
    $n = n / 2
    ? n % 2 == 1 { $c = c + 1 }
    $n = n / 2
    ? n % 2 == 1 { $c = c + 1 }
    $n = n / 2
    ? n % 2 == 1 { $c = c + 1 }
    ^ c
}
# {
    ! pop4(13)
}""",
        "c": '''#include <stdio.h>
int pop4(unsigned n) {
    int c = 0;
    for (int i = 0; i < 4; i++) { c += n & 1; n >>= 1; }
    return c;
}
int main() {
    printf("%d\\n", pop4(13));
    return 0;
}''',
        "rust": '''fn main() {
    println!("{}", (13u8).count_ones());
}''',
        "mojo": '''fn pop4(n: Int) -> Int:
    var c = 0
    var x = n
    for _ in range(4):
        c += x % 2
        x = x // 2
    return c
fn main():
    print(pop4(13))''',
    },
    {
        "name": "Handbook_RangeInclusive",
        "desc": "闭区间求和 3..=7",
        "roles": ["mojo_compute", "rust_safe", "xc_primary", "c_lowlevel"],
        "x": """# {
    $s = 0
    ~i = 3; i <= 7; i = i + 1 {
        $s = s + i
    }
    ! s
}""",
        "c": '''#include <stdio.h>
int main() {
    int s = 0;
    for (int i = 3; i <= 7; i++) s += i;
    printf("%d\\n", s);
    return 0;
}''',
        "rust": '''fn main() {
    let s: i32 = (3..=7).sum();
    println!("{}", s);
}''',
        "mojo": '''fn main():
    var s = 0
    for i in range(3, 8):
        s += i
    print(s)''',
    },
    {
        "name": "Handbook_MulTableCell",
        "desc": "九九表一格 7*8",
        "roles": ["mojo_compute", "xc_primary", "c_lowlevel", "rust_safe"],
        "x": """# {
    ! 7 * 8
}""",
        "c": '''#include <stdio.h>
int main() {
    printf("%d\\n", 7 * 8);
    return 0;
}''',
        "rust": '''fn main() {
    println!("{}", 7 * 8);
}''',
        "mojo": '''fn main():
    print(7 * 8)''',
    },
    {
        "name": "Handbook_TernaryMax",
        "desc": "三目运算符取最大（C风格）",
        "roles": ["c_lowlevel", "rust_safe", "xc_primary", "mojo_compute"],
        "x": """% max3(a, b, c) {
    $m = a
    ? b > m { $m = b }
    ? c > m { $m = c }
    ^ m
}
# {
    ! max3(2, 9, 5)
}""",
        "c": '''#include <stdio.h>
int main() {
    int a = 2, b = 9, c = 5;
    int m = a > b ? a : b;
    m = m > c ? m : c;
    printf("%d\\n", m);
    return 0;
}''',
        "rust": '''fn main() {
    let m = *[2, 9, 5].iter().max().unwrap();
    println!("{}", m);
}''',
        "mojo": '''fn max3(a: Int, b: Int, c: Int) -> Int:
    var m = a
    if b > m: m = b
    if c > m: m = c
    return m
fn main():
    print(max3(2, 9, 5))''',
    },
    {
        "name": "Handbook_DivRoundToZero",
        "desc": "整数除法向零截断（负数）",
        "roles": ["rust_safe", "c_lowlevel", "xc_primary", "mojo_compute"],
        "x": """# {
    ! (-7) / 2
}""",
        "c": '''#include <stdio.h>
int main() {
    printf("%d\\n", (-7) / 2);
    return 0;
}''',
        "rust": '''fn main() {
    println!("{}", (-7i32) / 2);
}''',
        "mojo": '''fn main():
    print((-7) // 2)''',
    },
    {
        "name": "Handbook_Log2FloorSmall",
        "desc": "对2≤n≤16求floor(log2 n)",
        "roles": ["mojo_compute", "c_lowlevel", "xc_primary", "rust_safe"],
        "x": """% log2f(n) {
    $c = 0
    $x = n
    @x > 1 {
        $x = x / 2
        $c = c + 1
    }
    ^ c
}
# {
    ! log2f(10)
}""",
        "c": '''#include <stdio.h>
int log2f(unsigned n) {
    int c = 0;
    while (n > 1) { n >>= 1; c++; }
    return c;
}
int main() {
    printf("%d\\n", log2f(10));
    return 0;
}''',
        "rust": '''fn log2f(mut n: u32) -> u32 {
    let mut c = 0;
    while n > 1 { n >>= 1; c += 1; }
    c
}
fn main() {
    println!("{}", log2f(10));
}''',
        "mojo": '''fn log2f(n: Int) -> Int:
    var c = 0
    var x = n
    while x > 1:
        x = x // 2
        c += 1
    return c
fn main():
    print(log2f(10))''',
    },
    {
        "name": "Handbook_CoalesceZero",
        "desc": "零则替换默认值（Rust map_or）",
        "roles": ["rust_safe", "c_lowlevel", "xc_primary", "mojo_compute"],
        "x": """% nz(v, d) {
    ? v == 0 { ^ d }
    ^ v
}
# {
    ! nz(0, 100)
}""",
        "c": '''#include <stdio.h>
int nz(int v, int d) { return v == 0 ? d : v; }
int main() {
    printf("%d\\n", nz(0, 100));
    return 0;
}''',
        "rust": '''fn main() {
    let v = 0;
    println!("{}", if v == 0 { 100 } else { v });
}''',
        "mojo": '''fn nz(v: Int, d: Int) -> Int:
    if v == 0: return d
    return v
fn main():
    print(nz(0, 100))''',
    },
    {
        "name": "Handbook_SaturatingSub",
        "desc": "无符号饱和减（Rust saturating_sub）",
        "roles": ["rust_safe", "c_lowlevel", "xc_primary", "mojo_compute"],
        "x": """% sat_sub(a, b) {
    ? a > b { ^ a - b }
    ^ 0
}
# {
    ! sat_sub(3, 10)
}""",
        "c": '''#include <stdio.h>
unsigned sat_sub(unsigned a, unsigned b) {
    return a > b ? a - b : 0;
}
int main() {
    printf("%u\\n", sat_sub(3, 10));
    return 0;
}''',
        "rust": '''fn main() {
    let a: u32 = 3;
    let b: u32 = 10;
    println!("{}", a.saturating_sub(b));
}''',
        "mojo": '''fn sat_sub(a: Int, b: Int) -> Int:
    if a > b:
        return a - b
    return 0
fn main():
    print(sat_sub(3, 10))''',
    },
    {
        "name": "Handbook_WorkflowNote",
        "desc": "工作流备忘：人工样本→AI融合→你定稿（四语对照）",
        "roles": ["xc_primary", "c_lowlevel", "rust_safe", "mojo_compute"],
        "x": """# {
    ! "1手册样本 2AI融合 3你拍板 = 专属XC融合语言"
}""",
        "c": '''#include <stdio.h>
int main(void) {
    puts("1 samples 2 AI merge 3 you sign-off = fused XC language");
    return 0;
}''',
        "rust": '''fn main() {
    println!("1 samples 2 AI merge 3 you sign-off = fused XC language");
}''',
        "mojo": '''fn main():
    print("1 samples 2 AI merge 3 you sign-off = fused XC language")''',
    },
    # --- V3 定稿对齐样本（spec.md「XC 语言定稿（V3）」）---
    {
        "name": "Handbook_V3_PrintO",
        "desc": "V3：◎O 行输出（不用 ! 打印）",
        "roles": ["xc_primary", "c_lowlevel", "rust_safe", "mojo_compute"],
        "x": """# {
    ◎O (1 + 2)
}""",
        "c": '''#include <stdio.h>
int main() {
    printf("%d\\n", 1 + 2);
    return 0;
}''',
        "rust": '''fn main() {
    println!("{}", 1 + 2);
}''',
        "mojo": '''fn main():
    print(1 + 2)''',
    },
    {
        "name": "Handbook_V3_LogicalNotAdd",
        "desc": "V3：! 仅逻辑非；!x+y 为 (!x)+y（C 整型 0/1）",
        "roles": ["xc_primary", "c_lowlevel", "rust_safe", "mojo_compute"],
        "x": """# {
    $x: int = 0
    $y: int = 5
    ◎O (!x + y)
}""",
        "c": '''#include <stdio.h>
int main() {
    int x = 0, y = 5;
    printf("%d\\n", (!x) + y);
    return 0;
}''',
        "rust": '''fn main() {
    let x: i32 = 0;
    let y: i32 = 5;
    let nx = if x == 0 { 1 } else { 0 };
    println!("{}", nx + y);
}''',
        "mojo": '''fn main():
    let x = 0
    let y = 5
    let nx = 1 if x == 0 else 0
    print(nx + y)''',
    },
    {
        "name": "Handbook_V3_TypedVars",
        "desc": "V3：$name: type 注解",
        "roles": ["xc_primary", "rust_safe", "c_lowlevel", "mojo_compute"],
        "x": """# {
    $msg: string = "xc"
    $n: int = 3
    ◎O msg
    ◎O n
}""",
        "c": '''#include <stdio.h>
int main() {
    const char* msg = "xc";
    int n = 3;
    puts(msg);
    printf("%d\\n", n);
    return 0;
}''',
        "rust": '''fn main() {
    let msg: &str = "xc";
    let n: i32 = 3;
    println!("{}", msg);
    println!("{}", n);
}''',
        "mojo": '''fn main():
    let msg: String = "xc"
    let n: Int = 3
    print(msg)
    print(n)''',
    },
    {
        "name": "Handbook_V3_IfElse",
        "desc": "V3：? 仅 if；?: else；条件括号",
        "roles": ["xc_primary", "c_lowlevel", "rust_safe", "mojo_compute"],
        "x": """# {
    $x: int = -1
    ? ((x > 0)) {
        ◎O "pos"
    } ?: {
        ◎O "nonpos"
    }
}""",
        "c": '''#include <stdio.h>
int main() {
    int x = -1;
    if (x > 0) puts("pos");
    else puts("nonpos");
    return 0;
}''',
        "rust": '''fn main() {
    let x: i32 = -1;
    if x > 0 { println!("pos"); } else { println!("nonpos"); }
}''',
        "mojo": '''fn main():
    let x: Int = -1
    if x > 0:
        print("pos")
    else:
        print("nonpos")''',
    },
    {
        "name": "Handbook_V3_ForWhile",
        "desc": "V3：~ 三件套 for；@ while；比较在括号内",
        "roles": ["xc_primary", "c_lowlevel", "rust_safe", "mojo_compute"],
        "x": """# {
    $s: int = 0
    ~i = 0; (i < 3); i = i + 1 {
        $s = s + i
    }
    $k: int = 2
    @ ((k > 0)) {
        $k = k - 1
    }
    ◎O s
}""",
        "c": '''#include <stdio.h>
int main() {
    int s = 0;
    for (int i = 0; i < 3; i++) s += i;
    int k = 2;
    while (k > 0) k--;
    printf("%d\\n", s);
    return 0;
}''',
        "rust": '''fn main() {
    let mut s: i32 = 0;
    for i in 0..3 { s += i; }
    let mut k: i32 = 2;
    while k > 0 { k -= 1; }
    println!("{}", s);
}''',
        "mojo": '''fn main():
    var s = 0
    for i in range(3):
        s += i
    var k = 2
    while k > 0:
        k -= 1
    print(s)''',
    },
    {
        "name": "Handbook_V3_FuncTyped",
        "desc": "V3：%f(a:t)->r { ^ }；func 仅为对照",
        "roles": ["xc_primary", "rust_safe", "c_lowlevel", "mojo_compute"],
        "x": """% add(a: int, b: int) -> int {
    ^ a + b
}
# {
    ◎O add(2, 3)
}""",
        "c": '''#include <stdio.h>
int add(int a, int b) { return a + b; }
int main() {
    printf("%d\\n", add(2, 3));
    return 0;
}''',
        "rust": '''fn add(a: i32, b: i32) -> i32 { a + b }
fn main() {
    println!("{}", add(2, 3));
}''',
        "mojo": '''fn add(a: Int, b: Int) -> Int:
    return a + b
fn main():
    print(add(2, 3))''',
    },
    {
        "name": "Handbook_V3_ListLiteral",
        "desc": "V3：list<int> 与 [] 字面量",
        "roles": ["rust_safe", "xc_primary", "c_lowlevel", "mojo_compute"],
        "x": """# {
    $xs: list<int> = [1, 2, 3]
    ◎O xs[0] + xs[2]
}""",
        "c": '''#include <stdio.h>
int main() {
    int xs[] = {1, 2, 3};
    printf("%d\\n", xs[0] + xs[2]);
    return 0;
}''',
        "rust": '''fn main() {
    let xs: Vec<i32> = vec![1, 2, 3];
    println!("{}", xs[0] + xs[2]);
}''',
        "mojo": '''fn main():
    let xs = [1, 2, 3]
    print(xs[0] + xs[2])''',
    },
    {
        "name": "Handbook_V3_StructPoint",
        "desc": "V3：结构体 &Name{ } 与字段访问",
        "roles": ["xc_primary", "c_lowlevel", "rust_safe", "mojo_compute"],
        "x": """& Point { x: int, y: int }
# {
    $p: &Point = &Point{ x: 3, y: 4 }
    ◎O (p.x + p.y)
}""",
        "c": '''#include <stdio.h>
typedef struct { int x, y; } Point;
int main() {
    Point p = {3, 4};
    printf("%d\\n", p.x + p.y);
    return 0;
}''',
        "rust": '''struct Point { x: i32, y: i32 }
fn main() {
    let p = Point { x: 3, y: 4 };
    println!("{}", p.x + p.y);
}''',
        "mojo": '''struct Point:
    var x: Int
    var y: Int
fn main():
    let p = Point(3, 4)
    print(p.x + p.y)''',
    },
    {
        "name": "Handbook_V3_MathMuQ",
        "desc": "V3 标准库：µQ 平方根",
        "roles": ["mojo_compute", "xc_primary", "c_lowlevel", "rust_safe"],
        "x": """# {
    ◎O µQ(16)
}""",
        "c": '''#include <stdio.h>
#include <math.h>
int main() {
    printf("%f\\n", sqrt(16.0));
    return 0;
}''',
        "rust": '''fn main() {
    println!("{}", (16.0_f64).sqrt());
}''',
        "mojo": '''fn main():
    print(4)''',
    },
    {
        "name": "Handbook_V3_LenMuN",
        "desc": "V3 标准库：µN 长度",
        "roles": ["rust_safe", "xc_primary", "c_lowlevel", "mojo_compute"],
        "x": """# {
    $s: string = "abc"
    ◎O µN(s)
}""",
        "c": '''#include <stdio.h>
#include <string.h>
int main() {
    const char* s = "abc";
    printf("%zu\\n", strlen(s));
    return 0;
}''',
        "rust": '''fn main() {
    let s = "abc";
    println!("{}", s.len());
}''',
        "mojo": '''fn main():
    let s = "abc"
    print(len(s))''',
    },
    {
        "name": "Handbook_V3_IOCore",
        "desc": "V3：◎O / ◎I 与 C/Rust/Mojo 映射示意",
        "roles": ["c_lowlevel", "rust_safe", "xc_primary", "mojo_compute"],
        "x": """# {
    $name: string = "Ada"
    ◎O name
}""",
        "c": '''#include <stdio.h>
int main() {
    const char* name = "Ada";
    puts(name);
    return 0;
}''',
        "rust": '''fn main() {
    let name = "Ada";
    println!("{}", name);
}''',
        "mojo": '''fn main():
    let name = "Ada"
    print(name)''',
    },
    {
        "name": "Handbook_V3_NetStub",
        "desc": "V3：≈ 网络族映射占位（实现依赖目标 API）",
        "roles": ["c_lowlevel", "xc_primary", "rust_safe", "mojo_compute"],
        "x": """# {
    $port: int = 8080
    ◎O ≈L(port)
}""",
        "c": '''#include <stdio.h>
int main() {
    int port = 8080;
    printf("listen stub %d\\n", port);
    return 0;
}''',
        "rust": '''fn main() {
    let port: u16 = 8080;
    println!("listen stub {}", port);
}''',
        "mojo": '''fn main():
    let port: Int = 8080
    print("listen stub ", port)''',
    },
    {
        "name": "Handbook_V3_BreakContinue",
        "desc": "V3：循环体内单独 > 为 break，< 为 continue",
        "roles": ["xc_primary", "c_lowlevel", "rust_safe", "mojo_compute"],
        "x": """# {
    $i: int = 0
    ~ j = 0; (j < 10); j = j + 1 {
        $i = i + 1
        ? ((j == 2)) {
            <
        }
        ? ((j == 5)) {
            >
        }
    }
    ◎O i
}""",
        "c": '''#include <stdio.h>
int main() {
    int i = 0;
    for (int j = 0; j < 10; j++) {
        i++;
        if (j == 2) continue;
        if (j == 5) break;
    }
    printf("%d\\n", i);
    return 0;
}''',
        "rust": '''fn main() {
    let mut i: i32 = 0;
    for j in 0..10 {
        i += 1;
        if j == 2 { continue; }
        if j == 5 { break; }
    }
    println!("{}", i);
}''',
        "mojo": '''fn main():
    var i = 0
    for j in range(10):
        i += 1
        if j == 2:
            continue
        if j == 5:
            break
    print(i)''',
    },
]
