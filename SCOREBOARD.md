# Scoreboard (Phase 2)

Test set: 30 questions (`tests/test_questions.csv`), same settings for all rows
(greedy, max 200 new tokens, repetition penalty 1.1, same system prompt).
Perplexity: same held-out text and same block size (1536) for every row, computed by `score.py`.

| Version | Held-out perplexity | Accuracy | Refusal accuracy | Avg. latency (s) | Notes |
|---|---|---|---|---|---|
| Small model, base | 2.83 | TBD | TBD | TBD | Qwen2.5-0.5B |
| + continued pretraining | 1.57 | TBD | TBD | TBD | 3 epochs, LR 1e-4, LoRA r=16, seq 1536 |
| + SFT | 1.90 | TBD | TBD | TBD | 1,930 pairs (1,738 train / 192 val), 3 epochs, LR 1e-4 |

TBD = filled by `python score.py summarize` after the two graders finish (see README).
Latency: the first question of the cpt and sft runs included a ~440-535 s GPU stall; it is excluded from the averages.
