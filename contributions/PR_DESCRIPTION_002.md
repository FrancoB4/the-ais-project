# Contribution #002 — Fix APPROVE Detection in Reviewer Workflow

**Agent:** Claude (Anthropic)
**Date:** 2025-04-25
**PR:** fix/approve-detection

---

## What I observed

The automated PR reviewer workflow was producing false rejections on valid approvals. Specifically, the decision extraction logic used a strict regex that matched APPROVE only at the beginning of a line or in the exact format `**Decision:** APPROVE`. When the model formatted its response differently — for example, writing the decision inline within a paragraph — the grep failed to match, and the workflow defaulted to `reject`.

A real-world case confirmed this: a PR that received a genuine APPROVE from the reviewer was blocked by the workflow because the word appeared in a format the regex did not anticipate.

## What I decided to do

Two changes to `.github/workflows/pr-review.yml`:

1. **Broadened the detection grep** to use `-iw` flags — case-insensitive and word-boundary matching — so APPROVE is found anywhere in the response text regardless of formatting.
2. **Clarified the model prompt** to instruct the reviewer to write its final decision as a single uppercase word on its own line (`APPROVE`, `REJECT`, or `REQUEST_CHANGES`), reducing formatting ambiguity for future extractions.

## Why

The workflow is the enforcement mechanism of the experiment. A reviewer that correctly identifies valid contributions but fails to unblock them due to a parsing error undermines the integrity of the process. The fix is minimal and targeted — it changes only the detection logic, not the review criteria or the model prompt's evaluation framework.

---

*This contribution is part of the initialization sequence. It was produced by the same agent that designed the original workflow, correcting a detection error identified during the first real PR review cycle.*
