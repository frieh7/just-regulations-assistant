"""
score.py — Phase 2: run the three models (base, +CPT, +SFT) on the 30 test questions
and score them the same way.

Two modes:
  python score.py run        # generate answers + auto scores + held-out perplexity + latency
  python score.py summarize  # after the two graders fill grader_1/grader_2 → accuracy & scoreboard

Every model is called through the same function (ask) with the same settings:
greedy decoding, max_new_tokens=200, same system prompt, same chat template.
"""
import argparse, csv, glob, json, math, os, re, sys, time

# ----------------------------- settings -----------------------------
SEED = 42
MAX_NEW_TOKENS = 200
REPETITION_PENALTY = 1.1          # same value for every model
PPL_BLOCK = 1536                  # same block size as CPT
SYSTEM = ("أنت مساعد لطلاب البكالوريوس في جامعة العلوم والتكنولوجيا الأردنية، "
          "تجيب عن الأسئلة حول الخطط الدراسية بدقة، وإذا ما كانت المعلومة موجودة "
          "بالوثائق تقول إنك لا تعرف.")   # identical to train_sft


def find(pattern, default=None):
    hits = glob.glob(pattern, recursive=True)
    return hits[0] if hits else default


def dir_of(pattern):
    p = find(pattern)
    return os.path.dirname(p) if p else None


# name -> model path (Kaggle defaults; override with --models name=path ...)
DEFAULT_MODELS = {
    "base": "Qwen/Qwen2.5-0.5B",
    "cpt": dir_of("/kaggle/input/**/cpt_model/config.json"),
    "sft": dir_of("/kaggle/input/**/sft_from_cpt/config.json"),
    "sft_from_base": dir_of("/kaggle/input/**/sft_from_base/config.json"),   # optional ablation
}
DEFAULT_TESTS = find("/kaggle/input/**/seed_test_set_plans.csv", "tests/test_questions.csv")
DEFAULT_HELDOUT = find("/kaggle/input/**/cpt_plans_heldout.jsonl", "data/cpt/cpt_plans_heldout.jsonl")
OUT_DIR = "results"

# ------------------------- text normalisation -------------------------
_DIAC = re.compile("[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")
_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def norm(s):
    s = (s or "").translate(_AR_DIGITS).lower()
    s = _DIAC.sub("", s)
    s = re.sub("[إأآٱ]", "ا", s).replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    return re.sub(r"\s+", " ", s).strip()


REFUSAL_MARKERS = ["لا اعرف", "لا تتوفر لدي", "غير موجوده في الخطط", "غير موجوده في الوثائق", "i don't know"]


def is_refusal(answer):
    a = norm(answer)
    return any(m in a for m in REFUSAL_MARKERS)


# ---------------- short exact answers (exact match after normalising) ----------------
# For questions whose expected answer is a number / yes-no / one word we check the key
# fact with a pattern on the normalised answer. Everything else is graded by hand.
def hours(n, words=()):
    pats = [rf"ساعاتها المعتمده\s*{n}(?!\d)", rf"(?<!\d){n}\s*(ساعه|ساعات)"]
    return {"any": pats + [re.escape(norm(w)) for w in words]}


NO_PREREQ = {"any": [r"ليس لها متطلب", r"لا يوجد لها متطلب", r"لا يوجد متطلب", r"بدون متطلب"],
             "none": [r"متطلبها السابق هو", r"المتطلب السابق .{0,60} هو"]}

EXACT_KEYS = {
    1:  {"any": [r"(?<!\d)15(?!\d)"]},
    2:  hours(2, ["ساعتان", "ساعتين"]),
    4:  hours(3),
    6:  NO_PREREQ,
    7:  hours(1, ["ساعه معتمده واحده", "ساعه واحده"]),
    9:  {"any": [r"مدمج"], "none": [r"وجاهي"]},
    10: NO_PREREQ,
    12: NO_PREREQ,
    13: NO_PREREQ,
    15: NO_PREREQ,
}


def exact_match(qid, answer):
    rule = EXACT_KEYS[qid]
    a = norm(answer)
    ok = any(re.search(p, a) for p in rule.get("any", []))
    bad = any(re.search(p, a) for p in rule.get("none", []))
    return int(ok and not bad)


def question_type(row):
    if row["source"].lower().startswith("out of scope"):
        return "refusal"
    return "exact" if int(row["id"]) in EXACT_KEYS else "manual"


def auto_score(row, answer):
    """Returns (score or '', note). '' means: graders decide."""
    t, refused = question_type(row), is_refusal(answer)
    if t == "refusal":
        return (1, "correct refusal") if refused else (0, "answered an out-of-scope question")
    if refused:
        return 0, "refused an in-scope question"
    if t == "exact":
        s = exact_match(int(row["id"]), answer)
        return s, "exact match" if s else "exact: key fact missing/wrong"
    return "", ""


# ------------------------------ models ------------------------------
def load(path):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    tok = AutoTokenizer.from_pretrained(path)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.float32).to(dev).eval()
    return tok, model


def ask(tok, model, question):
    """The single function every model is called through."""
    import torch
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt",
                                  return_dict=True).to(model.device)
    stop = [tok.convert_tokens_to_ids("<|im_end|>"), tok.eos_token_id]
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                             repetition_penalty=REPETITION_PENALTY,
                             eos_token_id=stop, pad_token_id=tok.pad_token_id)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    latency = time.perf_counter() - t0
    text = tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    return text, latency


def heldout_perplexity(tok, model, path):
    """Same text, same blocks for every model: docs joined with EOS, cut into PPL_BLOCK tokens."""
    import torch
    docs = []
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        docs.append(r.get("text") or next(v for v in r.values() if isinstance(v, str)))
    ids = []
    for d in docs:
        ids += tok(d, add_special_tokens=False)["input_ids"] + [tok.eos_token_id]
    nll, n = 0.0, 0
    with torch.no_grad():
        for i in range(0, len(ids) - 1, PPL_BLOCK):
            block = torch.tensor([ids[i:i + PPL_BLOCK]], device=model.device)
            if block.shape[1] < 2:
                break
            loss = model(block, labels=block).loss
            k = block.shape[1] - 1
            nll += loss.item() * k
            n += k
    return math.exp(nll / n)


# ------------------------------- run -------------------------------
FIELDS = ["id", "difficulty", "type", "question", "expected_answer", "model_answer",
          "refused", "auto_score", "grader_1", "grader_2", "score", "note", "latency_s"]


def run(args):
    import torch, random
    random.seed(SEED); torch.manual_seed(SEED)
    os.makedirs(OUT_DIR, exist_ok=True)
    tests = list(csv.DictReader(open(args.tests, encoding="utf-8-sig")))
    print(f"{len(tests)} test questions from {args.tests}")
    meta = {}
    for name, path in args.models.items():
        if not path:
            print(f"[skip] {name}: no path found"); continue
        print(f"\n=== {name}: {path}")
        tok, model = load(path)
        rows, lat = [], []
        for t in tests:
            ans, sec = ask(tok, model, t["question"])
            lat.append(sec)
            s, note = auto_score(t, ans)
            rows.append({"id": t["id"], "difficulty": t["difficulty"], "type": question_type(t),
                         "question": t["question"], "expected_answer": t["expected_answer"],
                         "model_answer": ans, "refused": int(is_refusal(ans)), "auto_score": s,
                         "grader_1": "", "grader_2": "", "score": s, "note": note,
                         "latency_s": round(sec, 3)})
            print(f"  [{t['id']:>2}] {sec:5.2f}s  auto={s!s:2}  {ans[:90]!r}")
        out = f"{OUT_DIR}/scores_{name}.csv"
        with open(out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
        ppl = heldout_perplexity(tok, model, args.heldout) if args.heldout and os.path.exists(args.heldout) else None
        meta[name] = {"path": path, "heldout_ppl": ppl, "avg_latency_s": sum(lat) / len(lat)}
        print(f"  -> {out} | held-out ppl={ppl} | avg latency={meta[name]['avg_latency_s']:.2f}s")
        del model; torch.cuda.empty_cache()
    json.dump({"settings": {"max_new_tokens": MAX_NEW_TOKENS, "do_sample": False,
                            "repetition_penalty": REPETITION_PENALTY, "seed": SEED, "system": SYSTEM},
               "models": meta}, open(f"{OUT_DIR}/run_meta.json", "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print("\nNext: two graders fill grader_1 / grader_2 (1, 0.5, 0) for type=manual rows, "
          "agree on disagreements in 'score', then run:  python score.py summarize")


# ---------------------------- summarize ----------------------------
def summarize(args):
    meta = json.load(open(f"{OUT_DIR}/run_meta.json", encoding="utf-8"))["models"]
    summary, agree_all = [], []
    for name in meta:
        path = f"{OUT_DIR}/scores_{name}.csv"
        rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
        missing, agree = [], []
        for r in rows:
            if r["type"] == "manual" and not r["refused"] == "1":
                g1, g2 = r["grader_1"].strip(), r["grader_2"].strip()
                if g1 and g2:
                    agree.append(float(g1) == float(g2))
                    if r["score"].strip() == "" and float(g1) == float(g2):
                        r["score"] = g1
                if r["score"].strip() == "":
                    missing.append(r["id"])
        if missing:
            print(f"[{name}] not graded yet / unresolved disagreement: ids {missing}")
            continue
        sc = lambda rs: sum(float(r["score"]) for r in rs) / len(rs) if rs else float("nan")
        ref = [r for r in rows if r["type"] == "refusal"]
        inscope = [r for r in rows if r["type"] != "refusal"]
        s = {"model": name,
             "heldout_ppl": meta[name]["heldout_ppl"],
             "accuracy": sc(rows),
             "accuracy_answerable": sc(inscope),
             "refusal_accuracy": sc(ref),
             "false_refusals": sum(r["refused"] == "1" for r in inscope),
             "easy": sc([r for r in rows if r["difficulty"] == "easy"]),
             "medium": sc([r for r in rows if r["difficulty"] == "medium"]),
             "hard": sc([r for r in rows if r["difficulty"] == "hard"]),
             "avg_latency_s": meta[name]["avg_latency_s"],
             "grader_agreement": (sum(agree) / len(agree)) if agree else None,
             "graded_by_hand": len(agree)}
        agree_all += agree
        summary.append(s)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:   # write back final scores
            w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    if not summary:
        return
    with open(f"{OUT_DIR}/summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
    pct = lambda x: f"{100 * x:.0f}%"
    print("\n| Version | Held-out perplexity | Accuracy | Refusal accuracy | Avg. latency (s) |")
    print("|---|---|---|---|---|")
    for s in summary:
        ppl = f"{s['heldout_ppl']:.2f}" if s["heldout_ppl"] else "-"
        print(f"| {s['model']} | {ppl} | {pct(s['accuracy'])} | {pct(s['refusal_accuracy'])} | {s['avg_latency_s']:.2f} |")
    print("\nBy difficulty (easy / medium / hard):")
    for s in summary:
        print(f"  {s['model']:14} {pct(s['easy'])} / {pct(s['medium'])} / {pct(s['hard'])}"
              f"   false refusals: {s['false_refusals']}")
    if agree_all:
        print(f"\nGraders agreed at first on {sum(agree_all)}/{len(agree_all)} "
              f"hand-graded answers ({pct(sum(agree_all) / len(agree_all))})")


# ------------------------------- main -------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["run", "summarize"], nargs="?", default="run")
    ap.add_argument("--tests", default=DEFAULT_TESTS)
    ap.add_argument("--heldout", default=DEFAULT_HELDOUT)
    ap.add_argument("--models", nargs="*", default=None,
                    help="name=path pairs, e.g. base=Qwen/Qwen2.5-0.5B cpt=./cpt_model")
    ap.add_argument("--only", nargs="*", default=None, help="run only these names, e.g. --only base cpt")
    args, _ = ap.parse_known_args()   # parse_known_args: also works with %run in a notebook
    models = dict(DEFAULT_MODELS)
    if args.models:
        models.update(dict(m.split("=", 1) for m in args.models))
    if args.only:
        models = {k: v for k, v in models.items() if k in args.only}
    args.models = models
    run(args) if args.mode == "run" else summarize(args)
