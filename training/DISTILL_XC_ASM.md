# XC→ASM 模型蒸馏与部署说明

## 目标

在已通过 **SL + 规则校验** 的大模型（或 LoRA 适配器）基础上，蒸馏出更小、延迟更低的模型，用于 IDE 内联汇编生成或批处理编译，同时保持 `tools/xc_asm_validate.py` 中的汇编语法门通过率。

## 推荐流程

1. **教师**：`train_xc_asm.py` 训练得到的高分 LoRA 或全参微调模型（在 held-out JSONL 上 `assemble_ok` 比例高）。
2. **学生**：更小基座（如 0.5B–1.5B Coder），在同一 JSONL 上 **只模仿教师 logits 或硬标签**（标准知识蒸馏：KL(student || teacher) 或序列级 CE）。
3. **数据**：子集优先——短程序、无 IO、与 Oracle 子集一致，减少长尾错误。
4. **门控**：学生输出仍经仓库根目录 `xc_asm_validate.py` 中的 `assemble_check` / `basic_asm_sanity`；未通过则重采样或回退到教师（产品策略可配置，但**不**使用 gcc/clang 修复汇编文本）。

## 部署检查清单

- 固定 ISA 字符串与调用约定文档（与 `xc_asm_config.py` 一致）。
- 推理侧 tokenizer 与训练一致；汇编侧禁止吞掉 `.text` / `.globl main`。
- CI：对固定 golden XC 跑 Oracle 与学生，对比 `assemble_ok` 与（若工具链齐全）qemu 退出码。

## 与 RLHF 的关系

蒸馏通常在 DPO/ORPO 之后做：先偏好对齐再压缩。也可只对 **通过规则门** 的样本做蒸馏，避免放大错误模式。
