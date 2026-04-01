"""
XC 语言推理脚本 - 加载微调模型进行翻译
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
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("警告: Transformers 未安装，推理功能不可用")

try:
    from unsloth import FastLanguageModel
    HAS_UNSLOTH = True
except ImportError:
    HAS_UNSLOTH = False


TRANSLATION_SYSTEM_PROMPT = """你是一个专业的代码翻译专家，擅长在不同编程语言之间进行精确翻译。
你只输出翻译后的代码，不包含任何解释或其他内容。"""


TRANSLATION_TEMPLATES = {
    "x_to_c": "将以下XC语言代码翻译为C代码，只输出C代码:\n\n{x_code}",
    "x_to_rust": "将以下XC语言代码翻译为Rust代码，只输出Rust代码:\n\n{x_code}",
    "x_to_mojo": "将以下XC语言代码翻译为Mojo代码，只输出Mojo代码:\n\n{x_code}",
    "c_to_x": "将以下C代码翻译为XC语言代码，只输出XC语言代码:\n\n{x_code}",
    "rust_to_x": "将以下Rust代码翻译为XC语言代码，只输出XC语言代码:\n\n{x_code}",
    "mojo_to_x": "将以下Mojo代码翻译为XC语言代码，只输出XC语言代码:\n\n{x_code}",
    "c_to_rust": "将以下C代码翻译为Rust代码:\n\n{x_code}",
    "rust_to_c": "将以下Rust代码翻译为C代码:\n\n{x_code}",
    "rust_to_mojo": "将以下Rust代码翻译为Mojo代码:\n\n{x_code}",
    "mojo_to_rust": "将以下Mojo代码翻译为Rust代码:\n\n{x_code}",
    "c_to_mojo": "将以下C代码翻译为Mojo代码:\n\n{x_code}",
    "mojo_to_c": "将以下Mojo代码翻译为C代码:\n\n{x_code}",
}


class XTranslator:
    """XC 语言翻译器"""

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


def translate_file(
    input_path: str,
    output_path: Optional[str],
    source_lang: str,
    target_lang: str,
    model_path: str,
) -> str:
    """翻译文件"""
    translator = XTranslator(model_path)

    with open(input_path, "r", encoding="utf-8") as f:
        code = f.read()

    result = translator.translate(code, source_lang, target_lang)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"[保存] 翻译结果已保存: {output_path}")

    return result


def interactive_mode(model_path: str):
    """交互模式"""
    translator = XTranslator(model_path)

    print("\n" + "=" * 60)
    print("XC 语言翻译器 - 交互模式")
    print("=" * 60)
    print("支持方向: x↔c, x↔rust, x↔mojo, c↔rust, rust↔mojo, c↔mojo")
    print("输入 q 退出\n")

    while True:
        try:
            print("\n输入源语言 (x/c/rust/mojo): ", end="")
            source = input().strip().lower()
            if source == "q":
                break

            print("输入目标语言 (x/c/rust/mojo): ", end="")
            target = input().strip().lower()
            if target == "q":
                break

            print("输入代码 (输入完成后按 Ctrl+D 或空行结束):")
            lines = []
            while True:
                try:
                    line = input()
                    if line.strip() == "":
                        break
                    lines.append(line)
                except EOFError:
                    break

            code = "\n".join(lines)
            if not code.strip():
                continue

            print(f"\n正在翻译: {source} -> {target} ...")
            result = translator.translate(code, source, target)

            print("\n" + "-" * 40)
            print("翻译结果:")
            print("-" * 40)
            print(result)
            print("-" * 40)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[错误] {e}")

    print("\n再见!")


def demo():
    """演示"""
    print("\n" + "=" * 60)
    print("XC 语言翻译器演示")
    print("=" * 60)

    sample_code = """▶MAIN{◎>"Hello World"}"""

    print(f"\nXC 语言代码:\n{sample_code}")

    print("\n" + "-" * 40)
    print("翻译结果 (如果模型已训练):")
    print("-" * 40)
    print("  C: printf(\"Hello World\\n\");")
    print("  Rust: println!(\"Hello World\");")
    print("  Mojo: print(\"Hello World\");")


def main():
    parser = argparse.ArgumentParser(description="XC 语言翻译器")
    parser.add_argument("--model", type=str, default="e:/X语音/models/x-translator",
                        help="模型路径")
    parser.add_argument("--input", "-i", type=str, help="输入文件")
    parser.add_argument("--output", "-o", type=str, help="输出文件")
    parser.add_argument("--source", "-s", type=str, choices=["x", "c", "rust", "mojo"],
                        help="源语言")
    parser.add_argument("--target", "-t", type=str, choices=["x", "c", "rust", "mojo"],
                        help="目标语言")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    parser.add_argument("--demo", action="store_true", help="演示模式")

    args = parser.parse_args()

    if args.demo:
        demo()
        return

    if args.interactive:
        interactive_mode(args.model)
        return

    if args.input and args.source and args.target:
        if not Path(args.model).exists():
            print(f"[错误] 模型不存在: {args.model}")
            print("[提示] 请先运行训练: python training/train_x_translator.py")
            demo()
            return

        result = translate_file(
            args.input,
            args.output,
            args.source,
            args.target,
            args.model,
        )
        print("\n翻译结果:")
        print(result)
    else:
        demo()


if __name__ == "__main__":
    main()
