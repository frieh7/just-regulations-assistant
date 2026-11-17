# Scoreboard (Phase 2)

Test set: 30 questions (`tests/test_questions.csv`: 15 easy / 10 medium / 5 hard; ids 28-30 are refusals).
Same settings for every row: greedy decoding, max 200 new tokens, repetition penalty 1.1, same system prompt.
Held-out perplexity: same text and same block size (1536) for every row, computed by `score.py`.

| Version | Held-out perplexity | Accuracy | Refusal accuracy | Avg. latency (s) | Notes |
|---|---|---|---|---|---|
| Small model, base | 2.83 | 0% (0/30) | 0% (0/3) | 22.6 | Qwen2.5-0.5B, no answer format, degenerate text |
| + continued pretraining | 1.57 | 0% (0/30) | 0% (0/3) | 22.5 | 3 epochs, LR 1e-4, LoRA, seq 1536; writes plan-style text, no answers |
| + SFT | 1.90 | 20% (6/30) | 100% (3/3) | 9.0 | 1,930 pairs (1,738 train / 192 val), 3 epochs, LR 1e-4 |

SFT accuracy on the 27 answerable questions is 11% (3/27); it wrongly refused 6 of them.
By difficulty (easy / medium / hard) the SFT model scores 20% / 0% / 60% (hard = the 3 refusals + 2 wrong answers).

**Status of the scores: first-pass grading by Claude** (files `results/claude_first_pass.xlsx`).
The brief asks for two team graders; their independent grades and the first-agreement rate are added here
once they finish (`results/grading_blind.xlsx` is the blank sheet). Until then these numbers are provisional.

Notes
- Latency averages exclude question 1: the first call of the cpt and sft runs stalled on the GPU (439 s and 535 s).
- The automatic scorer in `score.py` gave cpt ids 2, 10, 12, 13 a score of 1 (it found "no prerequisite" / "2 hours" in text about other courses); these were corrected to 0.
- Held-out perplexity from the CPT notebook (3.37 -> 1.58) used a different blocking; the table uses `score.py` for all three rows.
