"""
XC 语言翻译模型训练脚本

使用方法:
    python train_xc_translator.py --model qwen2.5-coder-1.5b --epochs 3
"""

import os
import sys
import json
from pathlib import Path
import argparse

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("错误: PyTorch 未安装")

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, DataCollatorForLanguageModeling
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("警告: Transformers 未安装")

try:
    from peft import LoraConfig, get_peft_model, TaskType
    HAS_PEFT = True
except ImportError:
    HAS_PEFT = False

try:
    from unsloth import FastLanguageModel
    HAS_UNSLOTH = True
except ImportError:
    HAS_UNSLOTH = False


MODEL_CONFIGS = {
    "qwen2.5-coder-1.5b": {
        "name": "Qwen/Qwen2.5-Coder-1.5B",
        "max_len": 8192,
        "lora_r": 16,
        "lora_alpha": 32,
    },
    "qwen2.5-coder-7b": {
        "name": "Qwen/Qwen2.5-Coder-7B",
        "max_len": 8192,
        "lora_r": 32,
        "lora_alpha": 64,
    },
    "starcoder2-3b": {
        "name": "bigcode/starcoder2-3b",
        "max_len": 8192,
        "lora_r": 16,
        "lora_alpha": 32,
    },
}


def load_dataset(data_path):
    """加载数据集"""
    path = Path(data_path)
    if not path.exists():
        print(f"[错误] 数据集不存在: {data_path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[加载] 加载了 {len(data)} 条数据")
    return data


class XCTanslatorTrainer:
    """XC 翻译模型训练器"""

    def __init__(
        self,
        model_name="qwen2.5-coder-1.5b",
        output_dir="e:/X语音/models/xc-translator",
    ):
        self.model_name = model_name
        self.config = MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["qwen2.5-coder-1.5b"])
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.model = None
        self.tokenizer = None

    def load_model(self):
        """加载模型"""
        print(f"[加载] 正在加载模型: {self.model_name}")

        if HAS_UNSLOTH:
            print("[加载] 使用 UnSloth 加速...")
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.config["name"],
                max_seq_length=self.config["max_len"],
                dtype=torch.float16,
                load_in_4bit=True,
            )
        elif HAS_TRANSFORMERS:
            print("[加载] 使用标准 Transformers...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.config["name"])
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config["name"],
                torch_dtype=torch.float16,
                device_map="auto",
            )
        else:
            raise ImportError("请安装 transformers: pip install transformers")

        print("[加载] 模型加载完成")

    def setup_lora(self):
        """设置 LoRA"""
        if HAS_UNSLOTH:
            self.model = FastLanguageModel.get_peft_model(
                self.model,
                r=self.config["lora_r"],
                lora_alpha=self.config["lora_alpha"],
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            )
        elif HAS_PEFT:
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=self.config["lora_r"],
                lora_alpha=self.config["lora_alpha"],
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            )
            self.model = get_peft_model(self.model, lora_config)

        print("[LoRA] LoRA 配置完成")

    def prepare_dataset(self, data_path):
        """准备数据集"""
        print("[数据] 加载并格式化数据集...")
        raw_data = load_dataset(data_path)

        texts = []
        for item in raw_data:
            instruction = item.get("instruction", "")
            input_code = item.get("input", "")
            output_code = item.get("output", "")
            text = f"{instruction}\n\n{input_code}\n\n{output_code}"
            texts.append(text)

        from datasets import Dataset
        dataset = Dataset.from_dict({"text": texts})
        return dataset

    def train(
        self,
        train_data_path="e:/X语音/dataset/xc_training_data.json",
        num_epochs=3,
        batch_size=4,
        learning_rate=2e-4,
        save_steps=500,
    ):
        """训练"""
        if not HAS_TORCH:
            raise ImportError("PyTorch 未安装")

        if self.model is None:
            self.load_model()
            self.setup_lora()

        dataset = self.prepare_dataset(train_data_path)
        print(f"[数据] 训练集大小: {len(dataset)}")

        training_args = TrainingArguments(
            output_dir=str(self.output_dir / "checkpoints"),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=learning_rate,
            warmup_steps=100,
            save_steps=save_steps,
            logging_steps=50,
            fp16=True,
            optim="adamw_torch",
            report_to="none",
            save_total_limit=3,
        )

        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )

        from transformers import Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator,
        )

        print("[训练] 开始训练...")
        trainer.train()

        print(f"[保存] 保存模型到: {self.output_dir}")
        self.model.save_pretrained(str(self.output_dir))
        self.tokenizer.save_pretrained(str(self.output_dir))

        print("[完成] 训练完成!")


def main():
    parser = argparse.ArgumentParser(description="XC 翻译模型训练")
    parser.add_argument("--model", type=str, default="qwen2.5-coder-1.5b",
                        choices=list(MODEL_CONFIGS.keys()), help="基座模型")
    parser.add_argument("--data", type=str, default="e:/X语音/dataset/xc_training_data.json",
                        help="训练数据路径")
    parser.add_argument("--output", type=str, default="e:/X语音/models/xc-translator",
                        help="输出目录")
    parser.add_argument("--epochs", type=int, default=3, help="训练轮数")
    parser.add_argument("--batch-size", type=int, default=4, help="批次大小")
    parser.add_argument("--lr", type=float, default=2e-4, help="学习率")

    args = parser.parse_args()

    if not Path(args.data).exists():
        print(f"[错误] 训练数据不存在: {args.data}")
        print("[提示] 请先运行 python dataset/generate_xc_dataset.py 生成数据")
        return

    trainer = XCTanslatorTrainer(
        model_name=args.model,
        output_dir=args.output,
    )

    trainer.train(
        train_data_path=args.data,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
    )


if __name__ == "__main__":
    main()
