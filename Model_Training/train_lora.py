"""Phase 0: train a Mistral-7B-Instruct-v0.2 LoRA adapter (GPU machine only).

Run on a GPU host (Colab A100 / HF AutoTrain equivalent). NOT runnable on this
Windows CPU box — needs ~24GB VRAM, torch+peft+transformers.

Setup (GPU host):
    pip install torch transformers peft datasets
    python train_lora.py --train lora_train.jsonl --val lora_val.jsonl --out ./lora_adapter

Constraints enforced for Cloudflare Workers AI compat (docs):
- base = mistralai/Mistral-7B-Instruct-v0.2 (matches @cf/...-lora family)
- rank r=8 default (allowed: <=8 and up to 32); alpha=16; targets q_proj+v_proj
- NO quantization (Cloudflare rejects quantized adapters)
- output files exactly: adapter_model.safetensors + adapter_config.json
  with "model_type": "mistral" injected, total <300MB (r=8 q+v ≈ 35MB)
"""
import argparse
import json
import os

BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="lora_train.jsonl")
    ap.add_argument("--val", default="lora_val.jsonl")
    ap.add_argument("--out", default="./lora_adapter")
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--alpha", type=int, default=16)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=2e-4)
    a = ap.parse_args()
    if a.rank > 32:
        raise SystemExit("Cloudflare requires rank <= 32")

    import torch
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling
    from peft import LoraConfig, get_peft_model

    tok = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    def fmt(ex):
        # Causal-LM format; inference sends raw problem text with raw:true
        return {"text": f"Categorize this societal challenge: {ex['prompt']}\nLabel: {ex['response']}{tok.eos_token}"}

    ds = load_dataset("json", data_files={"train": a.train, "validation": a.val})
    ds = ds.map(fmt, remove_columns=["prompt", "response"])
    ds = ds.map(lambda b: tok(b["text"], truncation=True, max_length=256), batched=True)

    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.float16, device_map="auto")
    model = get_peft_model(model, LoraConfig(
        r=a.rank, lora_alpha=a.alpha, lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM"))

    args = TrainingArguments(output_dir=a.out, num_train_epochs=a.epochs,
                             learning_rate=a.lr, per_device_train_batch_size=4,
                             gradient_accumulation_steps=4, logging_steps=20,
                             evaluation_strategy="epoch", save_strategy="epoch",
                             load_best_model_at_end=True, fp16=True,
                             report_to="none")
    Trainer(model=model, args=args, train_dataset=ds["train"],
            eval_dataset=ds["validation"],
            data_collator=DataCollatorForLanguageModeling(tok, mlm=False)).train()

    model.peft_model.save_pretrained(a.out)  # writes adapter_model.safetensors + adapter_config.json
    cfg_path = os.path.join(a.out, "adapter_config.json")
    cfg = json.load(open(cfg_path))
    cfg["model_type"] = "mistral"  # required by Cloudflare uploader
    json.dump(cfg, open(cfg_path, "w"), indent=2)
    size_mb = sum(os.path.getsize(os.path.join(a.out, f)) for f in
                  ("adapter_model.safetensors", "adapter_config.json")) / 1e6
    print(f"saved {a.out} rank={a.rank} size={size_mb:.1f}MB model_type=mistral")
    print("next: python check_adapter.py --dir ./lora_adapter")


if __name__ == "__main__":
    main()
