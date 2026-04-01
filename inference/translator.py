"""
C ↔ Rust ↔ Mojo 推理引擎
加载微调后的模型进行代码翻译
"""

import os
import torch
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import argparse

try:
    from unsloth import FastLanguageModel
except ImportError:
    FastLanguageModel = None

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
except ImportError:
    AutoModelForCausalLM = None


TRANSLATION_PROMPTS = {
    "c_to_rust": """You are an expert C to Rust translator. Convert the following C code to idiomatic, memory-safe Rust.

C Code:
```{c}
{input_code}
```

Rust Code:
""",
    "c_to_mojo": """You are an expert C to Mojo translator. Convert the following C code to Mojo.

C Code:
```{c}
{input_code}
```

Mojo Code:
""",
    "rust_to_c": """You are an expert Rust to C translator. Convert the following Rust code to C.

Rust Code:
```{rust}
{input_code}
```

C Code:
""",
    "rust_to_mojo": """You are an expert Rust to Mojo translator. Convert the following Rust code to Mojo.

Rust Code:
```{rust}
{input_code}
```

Mojo Code:
""",
    "mojo_to_c": """You are an expert Mojo to C translator. Convert the following Mojo code to C.

Mojo Code:
```{mojo}
{input_code}
```

C Code:
""",
    "mojo_to_rust": """You are an expert Mojo to Rust translator. Convert the following Mojo code to Rust.

Mojo Code:
```{mojo}
{input_code}
```

Rust Code:
""",
}

COMPILATION_COMMANDS = {
    "c": {
        "gcc": "gcc -o output source.c -Wall -Wextra",
        "clang": "clang -o output source.c -Wall -Wextra",
        "msvc": "cl /Fe:output.exe source.c /W4",
    },
    "rust": {
        "cargo": "cargo build --release",
        "rustc": "rustc source.rs -o output",
    },
    "mojo": {
        "mojo": "mojo build source.mojo",
    },
}

SUPPORTED_DIRECTIONS = list(TRANSLATION_PROMPTS.keys())


class CodeTranslator:
    """代码翻译器"""

    def __init__(
        self,
        model_path: str = "e:/X语音/models/x-language-model",
        model_type: str = "qwen2.5-coder",
        device: Optional[str] = None,
    ):
        self.model_path = Path(model_path)
        self.model_type = model_type

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model = None
        self.tokenizer = None
        self.pipeline = None

    def load(self):
        """加载模型"""
        print(f"[加载] 从 {self.model_path} 加载模型...")

        if not self.model_path.exists():
            raise FileNotFoundError(f"模型路径不存在: {self.model_path}")

        if FastLanguageModel:
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=str(self.model_path),
                dtype=torch.float16,
                load_in_4bit=True,
            )
            FastLanguageModel.for_inference(self.model)
        else:
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
        top_p: float = 0.95,
    ) -> Tuple[str, float]:
        """
        翻译代码

        Args:
            code: 源代码
            source_lang: 源语言 (c, rust, mojo)
            target_lang: 目标语言 (c, rust, mojo)
            max_length: 最大生成长度
            temperature: 采样温度
            top_p: nucleus 采样

        Returns:
            (翻译后的代码, 置信度分数)
        """
        if self.model is None:
            self.load()

        direction = f"{source_lang}_to_{target_lang}"
        if direction not in TRANSLATION_PROMPTS:
            raise ValueError(f"不支持的翻译方向: {direction}")

        prompt_template = TRANSLATION_PROMPTS[direction]
        prompt = prompt_template.format(input_code=code)

        if FastLanguageModel:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
                )

            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            response = generated_text[len(prompt):].strip()

            lines = response.split("\n")
            code_lines = []
            in_code_block = False

            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or line.strip():
                    code_lines.append(line)

            response = "\n".join(code_lines).strip()
        else:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
                )

            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = full_response[len(prompt):].strip()

            code_start = response.find("```")
            code_end = response.rfind("```")
            if code_start != -1 and code_end != -1 and code_start != code_end:
                response = response[code_start + 3:code_end].strip()
                if response.startswith(target_lang):
                    response = response[len(target_lang):].strip()

        confidence = self._estimate_confidence(response, code)

        return response, confidence

    def _estimate_confidence(self, translation: str, original: str) -> float:
        """估算翻译置信度"""
        if not translation or len(translation) < 10:
            return 0.0

        confidence = 0.5

        if len(translation) > len(original) * 0.5:
            confidence += 0.2

        if "error" not in translation.lower() and "undefined" not in translation.lower():
            confidence += 0.15

        if translation.count("{") == translation.count("}"):
            confidence += 0.1

        if translation.count("(") == translation.count(")"):
            confidence += 0.1

        return min(confidence, 1.0)

    def batch_translate(
        self,
        codes: List[str],
        source_lang: str,
        target_lang: str,
        **kwargs
    ) -> List[Tuple[str, float]]:
        """批量翻译"""
        results = []
        for code in codes:
            try:
                translation, confidence = self.translate(code, source_lang, target_lang, **kwargs)
                results.append((translation, confidence))
            except Exception as e:
                print(f"[警告] 翻译失败: {e}")
                results.append(("", 0.0))
        return results


class CodeVerifier:
    """代码验证器"""

    def __init__(self):
        self.temp_dir = Path("e:/X语音/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def verify_compilation(self, code: str, language: str) -> Tuple[bool, Optional[str]]:
        """验证代码是否能编译"""
        if language not in COMPILATION_COMMANDS:
            return False, f"不支持的语言: {language}"

        temp_file = self.temp_dir / f"test_code.{self._get_extension(language)}"

        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(code)

            if language == "c":
                return self._verify_c(temp_file)
            elif language == "rust":
                return self._verify_rust(temp_file)
            elif language == "mojo":
                return self._verify_mojo(temp_file)

        except Exception as e:
            return False, str(e)
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def _get_extension(self, language: str) -> str:
        """获取文件扩展名"""
        extensions = {"c": "c", "rust": "rs", "mojo": "mojo"}
        return extensions.get(language, "txt")

    def _verify_c(self, temp_file: Path) -> Tuple[bool, Optional[str]]:
        """验证 C 代码"""
        import subprocess

        try:
            result = subprocess.run(
                ["gcc", str(temp_file), "-o", str(temp_file.with_suffix(".exe")), "-Wall"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return True, None
            return False, result.stderr
        except FileNotFoundError:
            return False, "gcc 未安装"
        except subprocess.TimeoutExpired:
            return False, "编译超时"
        except Exception as e:
            return False, str(e)

    def _verify_rust(self, temp_file: Path) -> Tuple[bool, Optional[str]]:
        """验证 Rust 代码"""
        import subprocess

        try:
            result = subprocess.run(
                ["rustc", str(temp_file), "-o", str(temp_file.with_suffix(".exe"))],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return True, None
            return False, result.stderr
        except FileNotFoundError:
            return False, "rustc 未安装"
        except subprocess.TimeoutExpired:
            return False, "编译超时"
        except Exception as e:
            return False, str(e)

    def _verify_mojo(self, temp_file: Path) -> Tuple[bool, Optional[str]]:
        """验证 Mojo 代码"""
        return False, "Mojo 编译器验证暂不支持"


def demo():
    """演示翻译功能"""
    translator = CodeTranslator()

    if not translator.model_path.exists():
        print("[演示] 模型文件不存在，使用规则翻译演示...")

        from utils.grammar_mapping import get_type_mapping

        examples = [
            ("c", "rust", '#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}'),
            ("rust", "mojo", 'fn main() {\n    println!("Hello!");\n}'),
            ("c", "mojo", 'int add(int a, int b) {\n    return a + b;\n}'),
        ]

        for source_lang, target_lang, code in examples:
            print(f"\n{'='*60}")
            print(f"翻译: {source_lang.upper()} -> {target_lang.upper()}")
            print(f"原文:\n{code}")
            print(f"\n译文: (规则翻译示例)")
            print(f"# {target_lang.upper()} translation would be here")
    else:
        try:
            translator.load()

            test_code = '''#include <stdio.h>

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int main() {
    int result = factorial(5);
    printf("Factorial: %d\\n", result);
    return 0;
}'''

            print("\n" + "=" * 60)
            print("翻译演示: C -> Rust")
            print("=" * 60)
            print("\n原文 (C):")
            print(test_code)

            translation, confidence = translator.translate(test_code, "c", "rust")
            print(f"\n译文 (Rust) [置信度: {confidence:.2%}]:")
            print(translation)

        except Exception as e:
            print(f"[错误] 演示失败: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="C ↔ Rust ↔ Mojo 代码翻译")
    parser.add_argument("--model", type=str, default="e:/X语音/models/x-language-model")
    parser.add_argument("--input", type=str, help="输入代码文件")
    parser.add_argument("--source", type=str, choices=["c", "rust", "mojo"], required=True)
    parser.add_argument("--target", type=str, choices=["c", "rust", "mojo"], required=True)
    parser.add_argument("--verify", action="store_true", help="验证编译")

    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            code = f.read()

        translator = CodeTranslator(model_path=args.model)
        translation, confidence = translator.translate(code, args.source, args.target)

        print(f"\n翻译结果 [置信度: {confidence:.2%}]:\n")
        print(translation)

        if args.verify:
            verifier = CodeVerifier()
            success, error = verifier.verify_compilation(translation, args.target)
            if success:
                print(f"\n✓ {args.target.upper()} 代码编译成功")
            else:
                print(f"\n✗ {args.target.upper()} 代码编译失败: {error}")
    else:
        demo()
