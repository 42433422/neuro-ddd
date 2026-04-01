"""
XC 语言 V3 翻译脚本 - 使用专属原创符号
"""

import os
import sys
import torch
from pathlib import Path
from typing import Optional, Tuple
import argparse

try:
    import torch
except ImportError:
    print("错误: PyTorch 未安装")
    sys.exit(1)

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    from unsloth import FastLanguageModel
    HAS_UNSLOTH = True
except ImportError:
    HAS_UNSLOTH = False


TRANSLATION_TEMPLATES = {
    "x_to_c": "将XC语言代码翻译为C代码，只输出C代码:\n\n{x_code}",
    "x_to_rust": "将XC语言代码翻译为Rust代码，只输出Rust代码:\n\n{x_code}",
    "x_to_mojo": "将XC语言代码翻译为Mojo代码，只输出Mojo代码:\n\n{x_code}",
    "c_to_x": "将C代码翻译为XC语言代码，只输出XC语言代码:\n\n{x_code}",
    "rust_to_x": "将Rust代码翻译为XC语言代码，只输出XC语言代码:\n\n{x_code}",
    "mojo_to_x": "将Mojo代码翻译为XC语言代码，只输出XC语言代码:\n\n{x_code}",
    "c_to_rust": "将C代码翻译为Rust代码:\n\n{x_code}",
    "rust_to_c": "将Rust代码翻译为C代码:\n\n{x_code}",
    "rust_to_mojo": "将Rust代码翻译为Mojo代码:\n\n{x_code}",
    "mojo_to_rust": "将Mojo代码翻译为Rust代码:\n\n{x_code}",
    "c_to_mojo": "将C代码翻译为Mojo代码:\n\n{x_code}",
    "mojo_to_c": "将Mojo代码翻译为C代码:\n\n{x_code}",
}


class XTranslatorV3:
    """XC 语言 V3 翻译器"""

    def __init__(
        self,
        model_path: str = "e:/X语音/models/x-translator",
        device: Optional[str] = None,
    ):
        self.model_path = Path(model_path)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None

    def load(self):
        """加载模型"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"模型不存在: {self.model_path}")

        print(f"[加载] 从 {self.model_path} 加载模型...")

        if HAS_UNSLOTH:
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=str(self.model_path),
                dtype=torch.float16,
                load_in_4bit=True,
            )
            FastLanguageModel.for_inference(self.model)
        elif HAS_TRANSFORMERS:
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            self.model = AutoModelForCausalLM.from_pretrained(
                str(self.model_path),
                torch_dtype=torch.float16,
                device_map=self.device,
            )

        print(f"[加载] 模型加载完成 (设备: {self.device})")

    def translate(
        self,
        code: str,
        source_lang: str,
        target_lang: str,
        max_length: int = 2048,
        temperature: float = 0.2,
    ) -> str:
        """翻译代码"""
        if self.model is None:
            self.load()

        direction = f"{source_lang}_to_{target_lang}"
        if direction not in TRANSLATION_TEMPLATES:
            raise ValueError(f"不支持的翻译方向: {source_lang} -> {target_lang}")

        prompt = TRANSLATION_TEMPLATES[direction].format(x_code=code)

        if HAS_UNSLOTH or HAS_TRANSFORMERS:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=temperature,
                    do_sample=temperature > 0.1,
                    pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
                )

            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            result = response[len(prompt):].strip()

            code_blocks = self.extract_code(result, target_lang)
            if code_blocks:
                return code_blocks

            return result

        return "[错误] 无法翻译: 缺少模型支持"

    def extract_code(self, text: str, lang: str) -> str:
        """提取代码块"""
        import re

        pattern = rf"```(?:{lang})?\s*([\s\S]*?)```"
        matches = re.findall(pattern, text)

        if matches:
            return matches[0].strip()

        lines = text.split("\n")
        code_lines = []
        in_code = False

        for line in lines:
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code or not any(kw in line for kw in ["将以下", "翻译", "代码"]):
                code_lines.append(line)

        return "\n".join(code_lines).strip()


def demo():
    """演示"""
    print("\n" + "=" * 60)
    print("XC 语言 V3 翻译器 - 专属原创符号")
    print("=" * 60)

    print("\n【XC 语言符号对照表】")
    print("⌘Main  - 主函数入口")
    print("▽Func  - 定义函数")
    print("◈Int   - 整数类型")
    print("⊕      - 加法")
    print("⊖      - 减法")
    print("⊗      - 乘法")
    print("⊘      - 除法")
    print("⊙      - 取模")
    print("≡      - 等于")
    print("≢      - 不等于")
    print("⊳      - 大于")
    print("⊲      - 小于")
    print("▷If    - 条件判断")
    print("▷Else  - 否则")
    print("⟲Loop  - for循环")
    print("⟲While - while循环")
    print("⌬Return - 返回")
    print("�打印机 - 打印输出")
    print("✓True  - 真")
    print("✗False - 假")
    print("⌀Nil   - 空值")

    print("\n" + "=" * 60)
    print("示例 XC 代码:")
    print("=" * 60)

    samples = [
        '⌘Main{�打印机"Hello World"}',
        '⌘Main{▽Func add(a◈Int,b◈Int)◈Int⌬a⊕b⌦add(3,5)}',
        '⌘Main{▽x◈Int≔10▷x⊳5{�打印机"big"}▷Else{�打印机"small"}}',
        '⌘Main{⟲i◈Int∈[0,5]{�打印机i}}',
    ]

    for sample in samples:
        print(f"\nX: {sample}")

    print("\n" + "=" * 60)
    print("翻译结果 (训练模型后):")
    print("=" * 60)
    print('Rust: fn main() { println!("Hello World"); }')
    print('C: int main() { printf("Hello World\\n"); return 0; }')
    print('Mojo: fn main(): print("Hello World")')


def main():
    parser = argparse.ArgumentParser(description="XC 语言 V3 翻译器")
    parser.add_argument("--model", type=str, default="e:/X语音/models/x-translator", help="模型路径")
    parser.add_argument("--input", "-i", type=str, help="输入文件")
    parser.add_argument("--output", "-o", type=str, help="输出文件")
    parser.add_argument("--source", "-s", type=str, choices=["x", "c", "rust", "mojo"], help="源语言")
    parser.add_argument("--target", "-t", type=str, choices=["x", "c", "rust", "mojo"], help="目标语言")
    parser.add_argument("--demo", action="store_true", help="演示模式")

    args = parser.parse_args()

    if args.demo or (not args.input):
        demo()
        return

    if not Path(args.model).exists():
        print(f"[错误] 模型不存在: {args.model}")
        print("[提示] 请先运行训练: python training/train_x_translator.py")
        return

    translator = XTranslatorV3(args.model)

    with open(args.input, "r", encoding="utf-8") as f:
        code = f.read()

    result = translator.translate(code, args.source, args.target)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)

    print(result)


if __name__ == "__main__":
    main()
