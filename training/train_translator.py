"""
C ↔ Rust ↔ Mojo 三语互译模型训练脚本
基于 Qwen2.5-Coder 或 StarCoder2 进行 LoRA 微调
"""

import os
import json
import torch
from pathlib import Path
from typing import Optional, Dict, List
import argparse

try:
    from unsloth import FastLanguageModel
except ImportError:
    FastLanguageModel = None

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, DataCollatorForLanguageModeling
    from peft import LoraConfig, get_peft_model, TaskType
except ImportError:
    AutoModelForCausalLM = None

try:
    from datasets import Dataset
except ImportError:
    Dataset = None


MODEL_CONFIGS = {
    "qwen2.5-coder-1.5b": {
        "model_name": "Qwen/Qwen2.5-Coder-1.5B",
        "max_seq_length": 8192,
        "load_in_4bit": True,
        "lora_r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
    },
    "qwen2.5-coder-7b": {
        "model_name": "Qwen/Qwen2.5-Coder-7B",
        "max_seq_length": 8192,
        "load_in_4bit": True,
        "lora_r": 32,
        "lora_alpha": 64,
        "lora_dropout": 0.05,
    },
    "starcoder2-3b": {
        "model_name": "bigcode/starcoder2-3b",
        "max_seq_length": 8192,
        "load_in_4bit": True,
        "lora_r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
    },
    "starcoder2-7b": {
        "model_name": "bigcode/starcoder2-7b",
        "max_seq_length": 8192,
        "load_in_4bit": True,
        "lora_r": 32,
        "lora_alpha": 64,
        "lora_dropout": 0.05,
    },
}


TRANSLATION_PROMPTS = {
    "c_to_rust": """You are an expert C to Rust translator. Convert the following C code to idiomatic Rust.

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


def format_training_data(pairs: List[Dict], direction: str = "bidirectional") -> List[Dict]:
    """格式化训练数据"""
    formatted_data = []

    for pair in pairs:
        source_lang = pair["source_lang"]
        target_lang = pair["target_lang"]
        source_code = pair["source_code"]
        target_code = pair["target_code"]

        key = f"{source_lang}_to_{target_lang}"
        if key in TRANSLATION_PROMPTS:
            prompt = TRANSLATION_PROMPTS[key].format(input_code=source_code)

            formatted_data.append({
                "prompt": prompt,
                "response": target_code,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "direction": key,
            })

        if direction == "bidirectional":
            reverse_key = f"{target_lang}_to_{source_lang}"
            if reverse_key in TRANSLATION_PROMPTS:
                reverse_prompt = TRANSLATION_PROMPTS[reverse_key].format(input_code=target_code)
                formatted_data.append({
                    "prompt": reverse_prompt,
                    "response": source_code,
                    "source_lang": target_lang,
                    "target_lang": source_lang,
                    "direction": reverse_key,
                })

    return formatted_data


def prepare_dataset_from_json(file_path: str, direction: str = "bidirectional") -> List[Dict]:
    """从 JSON 文件准备数据集"""
    with open(file_path, "r", encoding="utf-8") as f:
        pairs = json.load(f)

    return format_training_data(pairs, direction)


class TranslationModelTrainer:
    """翻译模型训练器"""

    def __init__(
        self,
        model_config: str = "qwen2.5-coder-1.5b",
        output_dir: str = "e:/X语音/models/x-language-model",
    ):
        self.model_config_name = model_config
        self.model_config = MODEL_CONFIGS.get(model_config, MODEL_CONFIGS["qwen2.5-coder-1.5b"])
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.model = None
        self.tokenizer = None
        self.lora_config = None

    def load_model(self):
        """加载模型和分词器"""
        print(f"[加载] 正在加载模型: {self.model_config_name}")
        print(f"[加载] 模型配置: {self.model_config}")

        if FastLanguageModel:
            print("[加载] 使用 UnSloth 加速...")
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.model_config["model_name"],
                max_seq_length=self.model_config["max_seq_length"],
                dtype=torch.float16,
                load_in_4bit=self.model_config["load_in_4bit"],
            )
        else:
            print("[加载] 使用标准 Transformers...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_config["model_name"],
                torch_dtype=torch.float16,
                device_map="auto",
            )
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_config["model_name"],
            )

        print("[加载] 模型加载完成")

    def setup_lora(self):
        """设置 LoRA 微调"""
        if FastLanguageModel:
            self.model = FastLanguageModel.get_peft_model(
                self.model,
                lora_r=self.model_config["lora_r"],
                lora_alpha=self.model_config["lora_alpha"],
                lora_dropout=self.model_config["lora_dropout"],
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            )
        else:
            self.lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=self.model_config["lora_r"],
                lora_alpha=self.model_config["lora_alpha"],
                lora_dropout=self.model_config["lora_dropout"],
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            )
            self.model = get_peft_model(self.model, self.lora_config)

        print("[LoRA] LoRA 配置完成")

    def prepare_training_data(self, data_path: str):
        """准备训练数据"""
        if Dataset is None:
            raise ImportError("datasets 库未安装，请运行: pip install datasets")

        formatted_data = prepare_dataset_from_json(data_path)

        def generate_prompt_pair(example):
            prompt = example["prompt"]
            response = example["response"]
            full_prompt = f"{prompt}{response}"
            return {
                "text": full_prompt,
            }

        dataset = Dataset.from_list(formatted_data)
        dataset = dataset.map(generate_prompt_pair, remove_columns=dataset.column_names)

        return dataset

    def train(
        self,
        train_data_path: str,
        eval_data_path: Optional[str] = None,
        num_train_epochs: int = 3,
        per_device_train_batch_size: int = 4,
        gradient_accumulation_steps: int = 4,
        learning_rate: float = 2e-4,
        warmup_steps: int = 100,
        save_steps: int = 500,
        logging_steps: int = 50,
    ):
        """执行训练"""
        if self.model is None:
            self.load_model()
            self.setup_lora()

        print("[训练] 准备训练数据...")
        train_dataset = self.prepare_training_data(train_data_path)

        training_args = TrainingArguments(
            output_dir=str(self.output_dir / "checkpoints"),
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            save_steps=save_steps,
            logging_steps=logging_steps,
            fp16=True,
            optim="adamw_torch",
            report_to="none",
            save_total_limit=3,
        )

        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )

        print("[训练] 开始训练...")
        from transformers import Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=data_collator,
        )

        trainer.train()

        print(f"[保存] 保存模型到: {self.output_dir}")
        self.model.save_pretrained(str(self.output_dir))
        self.tokenizer.save_pretrained(str(self.output_dir))

        print("[完成] 训练完成！")

    def export_to_gguf(self, output_path: str):
        """导出为 GGUF 格式（用于 llama.cpp）"""
        print(f"[导出] 导出模型到 GGUF: {output_path}")
        print("[导出] 注意: 需要安装 llama.cpp 并使用 quantize 工具")


def main():
    parser = argparse.ArgumentParser(description="C ↔ Rust ↔ Mojo 翻译模型训练")
    parser.add_argument("--model", type=str, default="qwen2.5-coder-1.5b", choices=list(MODEL_CONFIGS.keys()))
    parser.add_argument("--data", type=str, default="e:/X语音/dataset/final/trilingual_dataset.json")
    parser.add_argument("--output", type=str, default="e:/X语音/models/x-language-model")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)

    args = parser.parse_args()

    trainer = TranslationModelTrainer(
        model_config=args.model,
        output_dir=args.output,
    )

    trainer.train(
        train_data_path=args.data,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.lr,
    )


if __name__ == "__main__":
    main()
