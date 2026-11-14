"""Model bake-off for the JUST Regulations Assistant (run on Kaggle T4 GPU).
Per model it measures, with NO training:
  1) tokenizer fertility  = tokens per word on the held-out university documents
  2) perplexity on held-out documents (lower = closer to this language/domain)
  3) zero-shot answers to the 30 test questions (saved for manual review)
Outputs: bakeoff_results.csv (numbers) and answers_<model>.csv (answers).
"""
import csv, gc, json, math, sys, time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# --- compatibility shim: Jais remote code imports a helper that new transformers removed ---
import transformers.pytorch_utils as _pu
if not hasattr(_pu, "find_pruneable_heads_and_indices"):
    def _fphi(heads, n_heads, head_size, already_pruned_heads):
        mask = torch.ones(n_heads, head_size)
        heads = set(heads) - already_pruned_heads
        for head in heads:
            head = head - sum(1 if h < head else 0 for h in already_pruned_heads)
            mask[head] = 0
        mask = mask.view(-1).contiguous().eq(1)
        return heads, torch.arange(len(mask))[mask].long()
    _pu.find_pruneable_heads_and_indices = _fphi

# ---- edit this list -------------------------------------------------------
MODELS = [
    "inceptionai/jais-family-1p3b",          # Arabic-native (needs trust_remote_code)
    "stabilityai/ar-stablelm-2-base",        # Arabic StableLM 1.6B base
    "tiiuae/Falcon-H1-1.5B-Base",            # multilingual
    "Qwen/Qwen3-1.7B-Base",                  # multilingual control
]
MAX_DOCS, WINDOW, MAX_WINDOWS = 44, 512, 60   # perplexity budget
MAX_NEW = 120
SYSTEM = ("أنت مساعد جامعة العلوم والتكنولوجيا الأردنية لشؤون الأنظمة والتعليمات. "
          "أجب بالعربية فقط اعتماداً على الوثائق الرسمية للجامعة، واختم كل جواب بذكر المصدر "
          "(اسم الوثيقة ورقم المادة). إذا لم تجد الإجابة قل: لا أعرف.")
# ---------------------------------------------------------------------------

docs = [json.loads(l)["text"] for l in open("heldout.jsonl", encoding="utf-8")][:MAX_DOCS]
questions = list(csv.DictReader(open("seed_test_set.csv", encoding="utf-8-sig")))
dev = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if dev == "cuda" else torch.float32   # T4 has no bf16


def fertility(tok):
    words = sum(len(d.split()) for d in docs)
    toks = sum(len(tok(d, add_special_tokens=False)["input_ids"]) for d in docs)
    return toks / words


def perplexity(model, tok):
    nll, n, used, chars = 0.0, 0, 0, 0
    for d in docs:
        ids = tok(d, add_special_tokens=False, return_tensors="pt")["input_ids"][0]
        for i in range(0, max(len(ids) - 1, 1), WINDOW):
            if used >= MAX_WINDOWS:
                break
            w = ids[i:i + WINDOW + 1]
            if len(w) < 16:
                continue
            x = w[:-1].unsqueeze(0).to(model.device)
            y = w[1:].unsqueeze(0).to(model.device)
            with torch.no_grad():
                logits = model(x).logits.float()
            loss = torch.nn.functional.cross_entropy(logits[0], y[0], reduction="sum")
            nll += loss.item(); n += y.numel(); used += 1
            chars += len(tok.decode(w[1:], skip_special_tokens=True))
    return math.exp(nll / n), nll / max(chars, 1)


def prompt_for(tok, q):
    if getattr(tok, "chat_template", None):
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": q}]
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True), True
    return f"{SYSTEM}\n\nالسؤال: {q}\nالجواب:", False


# --- Hugging Face login (needed for gated models: Jais, Arabic StableLM) ---
try:
    from kaggle_secrets import UserSecretsClient
    from huggingface_hub import login
    login(UserSecretsClient().get_secret("HF_TOKEN"))
    print("HF login ok")
except Exception as e:
    print("HF login skipped:", repr(e)[:100])

rows = []
for name in MODELS:
    t0 = time.time()
    res = {"model": name}
    try:
        tok = AutoTokenizer.from_pretrained(name, trust_remote_code=True)
        res["tokens_per_word"] = round(fertility(tok), 3)
        model = AutoModelForCausalLM.from_pretrained(
            name, torch_dtype=dtype, trust_remote_code=True).to(dev).eval()
        res["params_B"] = round(sum(p.numel() for p in model.parameters()) / 1e9, 2)
        ppl, nll_char = perplexity(model, tok)
        res["perplexity"] = round(ppl, 2)
        res["nll_per_char"] = round(nll_char, 4)   # comparable across tokenizers
        res["has_chat_template"] = bool(getattr(tok, "chat_template", None))
        out = []
        for q in questions:
            p, chat = prompt_for(tok, q["question"])
            enc = tok(p, return_tensors="pt", add_special_tokens=not chat).to(model.device)
            with torch.no_grad():
                g = model.generate(**enc, max_new_tokens=MAX_NEW, do_sample=False,
                                   pad_token_id=tok.eos_token_id)
            a = tok.decode(g[0][enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            out.append({"id": q["id"], "question": q["question"],
                        "expected_answer": q["expected_answer"], "model_answer": a})
        fn = "answers_" + name.replace("/", "_") + ".csv"
        with open(fn, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
        res["seconds"] = round(time.time() - t0)
        del model
    except Exception as e:
        res["error"] = repr(e)[:200]
    print(res, flush=True)
    rows.append(res)
    gc.collect()
    if dev == "cuda":
        torch.cuda.empty_cache()

keys = ["model", "params_B", "tokens_per_word", "perplexity", "nll_per_char", "has_chat_template", "seconds", "error"]
with open("bakeoff_results.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in keys})
print("done -> bakeoff_results.csv + answers_*.csv")
