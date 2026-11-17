"""Stage 2: supervised fine-tuning (LoRA, loss on answers only).

Usage:  python train_sft.py [--start cpt|base]
Mirrors the Kaggle notebook that produced the reported results (transformers Trainer, no TRL).
"""
import argparse, csv, json, os
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import Trainer, TrainingArguments, DataCollatorForSeq2Seq
from src.common import load_config, set_seed, load_model, encode_sft_example

ap = argparse.ArgumentParser()
ap.add_argument("--config", default="config.yaml")
ap.add_argument("--start", choices=["cpt", "base"], default=None)
a = ap.parse_args()

cfg = load_config(a.config)
S, L = cfg["sft"], cfg["lora"]
start = a.start or S["start"]
src_path = S["cpt_model_dir"] if start == "cpt" else cfg["base_model"]
out_dir = f"sft_from_{start}"
res_dir = f"results/sft_{start}"
os.makedirs(res_dir, exist_ok=True)
set_seed(cfg["seed"])

tok, model = load_model(src_path)
rows = [json.loads(l) for l in open(S["data_file"], encoding="utf-8")]
enc = lambda r: encode_sft_example(tok, cfg["system_prompt"], r["question"], r["answer"],
                                   S["max_len"], S["end_token"].replace("<|endoftext|>", tok.eos_token))
train = [enc(r) for r in rows if r["split"] == "train"]
val = [enc(r) for r in rows if r["split"] == "val"]
print(f"train {len(train)} | val {len(val)} | truncated train {sum(e['truncated'] for e in train)}")
strip = lambda xs: Dataset.from_list([{k: v for k, v in e.items() if k != "truncated"} for e in xs])
train_ds, val_ds = strip(train), strip(val)

model = get_peft_model(model, LoraConfig(r=L["r"], lora_alpha=L["alpha"], lora_dropout=L["dropout"],
                                         task_type="CAUSAL_LM", target_modules=L["target_modules"]))
args = TrainingArguments(output_dir=out_dir + "_tmp", num_train_epochs=S["epochs"],
                         learning_rate=S["learning_rate"], lr_scheduler_type="cosine",
                         warmup_steps=S["warmup_steps"],
                         per_device_train_batch_size=S["per_device_batch_size"],
                         per_device_eval_batch_size=S["per_device_batch_size"],
                         gradient_accumulation_steps=S["grad_accum_steps"], logging_steps=10,
                         eval_strategy="epoch", save_strategy="no", seed=cfg["seed"],
                         report_to="none", fp16=False, bf16=False, remove_unused_columns=False)
trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=val_ds,
                  data_collator=DataCollatorForSeq2Seq(tok, padding=True, label_pad_token_id=-100))

before = trainer.evaluate()["eval_loss"]
trainer.train()
after = trainer.evaluate()["eval_loss"]
print(f"VAL loss before {before:.4f} -> after {after:.4f}")

logs = trainer.state.log_history
with open(f"{res_dir}/sft_loss_log.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["type", "x", "loss"])
    w.writerows([["train", l["step"], l["loss"]] for l in logs if "loss" in l])
    w.writerows([["val", l["epoch"], l["eval_loss"]] for l in logs if "eval_loss" in l])
json.dump({"start": start, "train_pairs": len(train), "val_pairs": len(val), "epochs": S["epochs"],
           "lr": S["learning_rate"], "val_loss_before": before, "val_loss_after": after},
          open(f"{res_dir}/sft_metrics.json", "w"), indent=1)

merged = trainer.model.merge_and_unload()
merged.save_pretrained(out_dir); tok.save_pretrained(out_dir)
print("saved", out_dir)
