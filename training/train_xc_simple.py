"""
XC 语言翻译模型训练脚本 - 简化版
"""

import os
import sys
import json
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader
import argparse

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, get_linear_schedule_with_warmup
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("错误: Transformers 未安装")


MODEL_CONFIGS = {
    "qwen2.5-coder-1.5b": {
        "name": "Qwen/Qwen2.5-Coder-1.5B",
        "max_len": 1024,
        "lora_r": 16,
        "lora_alpha": 32,
    },
}


class XCDataset(Dataset):
    """XC 数据集"""
    def __init__(self, data_path, tokenizer, max_len=1024):
        with open(data_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        instruction = item.get("instruction", "")
        input_code = item.get("input", "")
        output_code = item.get("output", "")

        text = f"{instruction}\n\n{input_code}\n\n{output_code}"

        enc = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt",
        )

        input_ids = enc["input_ids"].squeeze()
        attention_mask = enc["attention_mask"].squeeze()

        labels = input_ids.clone()
        labels[labels == self.tokenizer.pad_token_id] = -100

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }


def train():
    """训练"""
    print("=" * 60)
    print("XC 翻译模型训练")
    print("=" * 60)

    model_name = "qwen2.5-coder-1.5b"
    data_path = "e:/X语音/dataset/xc_training_data.json"
    output_dir = "e:/X语音/models/xc-translator"

    config = MODEL_CONFIGS[model_name]

    print(f"[加载] 加载模型: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(config["name"], trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        config["name"],
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )

    print("[数据] 加载数据集...")
    dataset = XCDataset(data_path, tokenizer, max_len=config["max_len"])
    print(f"[数据] 数据集大小: {len(dataset)}")

    dataloader = DataLoader(dataset, batch_size=2, shuffle=True)

    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4)

    print("[训练] 开始训练...")
    model.train()

    total_steps = len(dataloader) * 3
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=100,
        num_training_steps=total_steps,
    )

    for epoch in range(3):
        print(f"\n--- Epoch {epoch + 1}/3 ---")
        total_loss = 0

        for step, batch in enumerate(dataloader):
            input_ids = batch["input_ids"].cuda()
            attention_mask = batch["attention_mask"].cuda()
            labels = batch["labels"].cuda()

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )

            loss = outputs.loss
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()

            total_loss += loss.item()

            if step % 10 == 0:
                print(f"  Step {step}/{len(dataloader)}, Loss: {loss.item():.4f}")

        avg_loss = total_loss / len(dataloader)
        print(f"  Epoch {epoch + 1} Average Loss: {avg_loss:.4f}")

    print(f"\n[保存] 保存模型到: {output_dir}")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print("[完成] 训练完成!")
    print("=" * 60)


if __name__ == "__main__":
    train()
