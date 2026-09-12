"""QLoRA fine-tune StarCoder2-3B on VecGlypher Google Fonts dataset.

Trains a local font glyph generator on an RTX 3090 (24GB VRAM).
Input: style description + target character
Output: SVG path d-attribute

Usage: python pipeline/train_font_model.py
"""
import os
import json
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

# Load env
from pathlib import Path
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

MODEL_NAME = "bigcode/starcoder2-3b"
DATASET_REPO = "VecGlypher/Google-Fonts-Dataset"
DATASET_PATH = "250910-alphanumeric-abs_coord/train_font_family"
OUTPUT_DIR = "./models/fontgen-starcoder2-3b-lora"

# QLoRA config — fits in ~12-14GB on RTX 3090
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

# LoRA config
lora_config = LoraConfig(
    r=32,
    lora_alpha=64,
    target_modules="all-linear",
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)


def format_sample(sample):
    """Convert Alpaca-format sample to chat-style prompt for training."""
    system = sample.get("system", "")
    instruction = sample.get("instruction", "")
    output = sample.get("output", "")

    # Format as: system + instruction → output
    text = f"### System:\n{system}\n\n### Instruction:\n{instruction}\n\n### Response:\n{output}"
    return {"text": text}


def main():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # Load tokenizer
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # Load model with 4-bit quantization
    print("Loading model with QLoRA 4-bit...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"Trainable: {trainable/1e6:.1f}M / {total/1e6:.1f}M ({100*trainable/total:.2f}%)")
    print(f"VRAM after model load: {torch.cuda.memory_allocated() / 1024**3:.1f} GB")

    # Load dataset
    print("Loading dataset...")
    dataset = load_dataset(
        DATASET_REPO,
        data_dir="250910-alphanumeric-abs_coord",
        data_files={"train": "train_font_family/*.jsonl"},
        split="train",
    )
    print(f"Dataset: {len(dataset)} samples")

    # Format for SFT
    dataset = dataset.map(format_sample, remove_columns=dataset.column_names)

    # Training args — conservative for RTX 3090
    training_args = SFTConfig(
        output_dir=OUTPUT_DIR,
        num_train_epochs=1,  # Start with 1 epoch, increase if quality is good
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,  # Effective batch size = 16
        learning_rate=2e-5,
        lr_scheduler_type="cosine",
        warmup_steps=100,
        bf16=True,
        logging_steps=50,
        save_steps=500,
        save_total_limit=3,
        max_grad_norm=1.0,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        report_to="none",
        dataloader_num_workers=0,  # Windows compatibility
        max_length=4096,
    )

    # Trainer
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        args=training_args,
        train_dataset=dataset,
    )

    print("Starting training...")
    print(f"Steps: {len(dataset) // (training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps)}")

    trainer.train()

    # Save
    print(f"Saving to {OUTPUT_DIR}...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("Done!")


if __name__ == "__main__":
    main()
