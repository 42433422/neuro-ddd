"""
XC 语言翻译模型训练脚本 - LoRA量化版
"""

import os
import json
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader
import argparse

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, TaskType
except ImportError:
    print("错误: 请安装 transformers 和 peft")

try:
    import bitsandbytes as bnb
except ImportError:
    bnb = None


class XCDataset(Dataset):
    """XC 数据集"""
    def __init__(self, data_path, tokenizer, max_len=512):
        with open(data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        text = f"{item['instruction']}\n\n{item['input']}\n\n{item['output']}"

        enc = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt",
        )

        input_ids = enc["input_ids"].squeeze()
        labels = input_ids.clone()
        labels[labels == self.tokenizer.pad_token_id] = -100

        return {"input_ids": input_ids, "labels": labels}


def train():
    """LoRA 训练"""
    print("=" * 60)
    print("XC 翻译模型训练 (LoRA 4bit 量化)")
    print("=" * 60)

    model_name = "Qwen/Qwen2.5-Coder-1.5B"
    data_path = "e:/X语音/dataset/xc_training_data.json"
    output_dir = "e:/X语音/models/xc-translator"

    print("[1/5] 加载分词器...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    print("[2/5] 加载模型 (4bit 量化)...")
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=quantization_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False

    print("[3/5] 配置 LoRA...")
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("[4/5] 加载数据集...")
    dataset = XCDataset(data_path, tokenizer, max_len=512)
    print(f"  数据集大小: {len(dataset)}")

    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    print("[5/5] 开始训练...")
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4)

    model.train()
    for epoch in range(3):
        total_loss = 0
        for step, batch in enumerate(dataloader):
            batch = {k: v.cuda() for k, v in batch.items()}

            outputs = model(**batch)
            loss = outputs.loss

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            optimizer.zero_grad()

            total_loss += loss.item()

            if step % 20 == 0:
                print(f"  Epoch {epoch+1}/3, Step {step}/{len(dataloader)}, Loss: {loss.item():.4f}")

        avg_loss = total_loss / len(dataloader)
        print(f"  Epoch {epoch+1} 完成, 平均 Loss: {avg_loss:.4f}")

    print(f"\n[保存] 保存模型到: {output_dir}")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print("[完成] 训练完成!")
    print("=" * 60)


if __name__ == "__main__":
    train()
