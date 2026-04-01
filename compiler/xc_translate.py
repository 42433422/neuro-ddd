"""
XC 语言翻译推理脚本

使用方法:
    python xc_translate.py --source x --target rust --input code.x
    python xc_translate.py --demo
"""

import sys
import torch
from pathlib import Path
import argparse

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
    "x_to_c": "将XC代码翻译为C代码，只输出C代码:\n\n{x_code}",
    "x_to_rust": "将XC代码翻译为Rust代码，只输出Rust代码:\n\n{x_code}",
    "x_to_mojo": "将XC代码翻译为Mojo代码，只输出Mojo代码:\n\n{x_code}",
    "c_to_x": "将C代码翻译为XC代码:\n\n{x_code}",
    "rust_to_x": "将Rust代码翻译为XC代码:\n\n{x_code}",
    "mojo_to_x": "将Mojo代码翻译为XC代码:\n\n{x_code}",
}


class XCTranslator:
    """XC 翻译器"""

    def __init__(self, model_path: str = "e:/X语音/models/xc-translator"):
        self.model_path = Path(model_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None

    def load(self):
        """加载模型"""
        if not self.model_path.exists():
            raise FileNotFoundError(f"模型不存在: {self.model_path}")

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

    def translate(self, code: str, source_lang: str, target_lang: str, max_length: int = 2048) -> str:
        """翻译代码"""
        if self.model is None:
            self.load()

        direction = f"{source_lang}_to_{target_lang}"
        if direction not in TRANSLATION_TEMPLATES:
            raise ValueError(f"不支持的翻译方向: {source_lang} -> {target_lang}")

        prompt = TRANSLATION_TEMPLATES[direction].format(x_code=code)

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=0.2,
                pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response[len(prompt):].strip()


def demo():
    """演示"""
    print("\n" + "=" * 60)
    print("XC 语言翻译器 - 四语互译")
    print("=" * 60)

    print("\n【XC 语言示例】")
    samples = [
        '# { ! "Hello World" }',
        '# { $x = 10 ! x }',
        '% add(a, b) { ^ a + b } # { ! add(3, 5) }',
    ]

    for sample in samples:
        print(f"  {sample}")

    print("\n" + "=" * 60)
    print("翻译示例 (需要先训练模型)")
    print("=" * 60)

    xc = '# { ! "Hello World" }'

    print(f"\nXC: {xc}")
    print("↓ Rust:")
    print('fn main() { println!("Hello World"); }')
    print("↓ C:")
    print('int main() { printf("Hello World\\n"); return 0; }')
    print("↓ Mojo:")
    print('fn main(): print("Hello World")')


def main():
    parser = argparse.ArgumentParser(description="XC 语言翻译器")
    parser.add_argument("--model", type=str, default="e:/X语音/models/xc-translator", help="模型路径")
    parser.add_argument("--input", "-i", type=str, help="输入文件")
    parser.add_argument("--source", "-s", type=str, choices=["x", "c", "rust", "mojo"], help="源语言")
    parser.add_argument("--target", "-t", type=str, choices=["x", "c", "rust", "mojo"], help="目标语言")
    parser.add_argument("--demo", action="store_true", help="演示模式")

    args = parser.parse_args()

    if args.demo or not args.input:
        demo()
        return

    if not Path(args.model).exists():
        print(f"[错误] 模型不存在: {args.model}")
        print("[提示] 请先运行: python training/train_xc_translator.py")
        return

    with open(args.input, "r", encoding="utf-8") as f:
        code = f.read()

    translator = XCTranslator(args.model)
    result = translator.translate(code, args.source, args.target)

    print(result)


if __name__ == "__main__":
    main()
