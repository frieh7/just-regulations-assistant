"""Stage 1: continued pretraining (next-token loss on the study-plan documents, LoRA).

Usage:  python train_cpt.py
NOTE: reconstructed from the settings of the Kaggle notebook "Continued pretraining"
(seq 1536, LR 1e-4, 3 epochs, LoRA, fixed seed). The reported numbers (held-out perplexity
3.37 -> 1.58) come from that notebook; re-check this script against it before final submission.
"""
import json, math, os
import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import Trainer, TrainingArguments, DataCollatorForLanguageModeling
from src.common import load_config, set_seed, load_model

cfg = load_config()
C, L = cfg["cpt"], cfg["lora"]
os.makedirs("results/cpt", exist_ok=True)
set_seed(cfg["seed"])
tok, model = load_model(cfg["base_model"])


def read_docs(path):
    out = []
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        out.append(r.get("text") or next(v for v in r.values() if isinstance(v, str)))
    return out


def blocks(docs):
    """Join documents with EOS and cut into seq_len blocks."""
    ids = []
    for d in docs:
        ids += tok(d, add_special_tokens=False)["input_ids"] + [tok.eos_token_id]
    n = C["seq_len"]
    return Dataset.from_list([{"input_ids": ids[i:i + n], "attention_mask": [1] * len(ids[i:i + n])}
                              for i in range(0, len(ids) - n + 1, n)])


train_ds, held_ds = blocks(read_docs(C["train_file"])), blocks(read_docs(C["heldout_file"]))
print("blocks: train", len(train_ds), "| held-out", len(held_ds))

model = get_peft_model(model, LoraConfig(r=L["r"], lora_alpha=L["alpha"], lora_dropout=L["dropout"],
                                         task_type="CAUSAL_LM", target_modules=L["target_modules"]))
args = TrainingArguments(output_dir="cpt_tmp", num_train_epochs=C["epochs"], learning_rate=C["learning_rate"],
                         lr_scheduler_type="cosine", warmup_steps=5, per_device_train_batch_size=2,
                         per_device_eval_batch_size=2, gradient_accumulation_steps=8, logging_steps=5,
                         eval_strategy="epoch", save_strategy="no", seed=cfg["seed"], report_to="none",
                         fp16=False, bf16=False)
trainer = Trainer(model=model, args=args, train_dataset=train_ds, eval_dataset=held_ds,
                  data_collator=DataCollatorForLanguageModeling(tok, mlm=False))

b = trainer.evaluate()["eval_loss"]
trainer.train()
a = trainer.evaluate()["eval_loss"]
print(f"held-out loss {b:.4f} -> {a:.4f} | perplexity {math.exp(b):.2f} -> {math.exp(a):.2f}")
json.dump({"loss_before": b, "loss_after": a, "ppl_before": math.exp(b), "ppl_after": math.exp(a),
           "log_history": trainer.state.log_history}, open("results/cpt/cpt_metrics.json", "w"), indent=1)

merged = trainer.model.merge_and_unload()
merged.save_pretrained(C["output_dir"]); tok.save_pretrained(C["output_dir"])
