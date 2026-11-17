"""Shared helpers: config, seeding, model loading, chat template, SFT tokenisation."""
import random

import yaml


def load_config(path="config.yaml"):
    return yaml.safe_load(open(path, encoding="utf-8"))


def set_seed(seed):
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_model(path, dtype=None):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    tok = AutoTokenizer.from_pretrained(path)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(path, dtype=dtype or torch.float32)
    return tok, model.to("cuda" if torch.cuda.is_available() else "cpu")


def chat_prompt(tok, system, question):
    """The one chat template used everywhere (Qwen ChatML, system + user, generation prompt)."""
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": question}]
    return tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)


def encode_sft_example(tok, system, question, answer, max_len, end_token):
    """Loss on the answer tokens only: prompt tokens get label -100."""
    p_ids = tok(chat_prompt(tok, system, question), add_special_tokens=False)["input_ids"]
    c_ids = tok(answer + end_token, add_special_tokens=False)["input_ids"]
    ids = (p_ids + c_ids)[:max_len]
    labels = ([-100] * len(p_ids) + c_ids)[:max_len]
    return {"input_ids": ids, "attention_mask": [1] * len(ids), "labels": labels,
            "truncated": int(len(p_ids) + len(c_ids) > max_len)}
