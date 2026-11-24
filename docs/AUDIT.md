# Audit of a classmate's repo

Audited repo: https://github.com/Azi23333/bikeshare-open
Commit audited: 9d07ad0
Date: 2026-11-24
Auditor model: bikeshare-coder (qwen3.5:9b, local Ollama, 64k context), Claude Code 2.1.327 and Agent SDK

## Why this is not `/leakage-auditor` output

I tried the `/leakage-auditor` subagent in Claude Code on this repo. Asking "Use the leakage-auditor subagent" made the model's tool call fail with "Invalid tool parameters", and the retry was interrupted. `@agent-leakage-auditor review the diff from 67dd845 to HEAD` then stalled on "Waiting for API response", even after I raised the WSL memory limit from 9 GB to 12 GB. I got no report from the subagent. I then ran the repo's batch auditor, `agent/audit.py`, which reports on leakage, the temporal split, baselines and reproducibility. Its output is below, verbatim.

## `agent/audit.py` output (verbatim)

```
{"repo": "/home/ediso/audited-repo", "leakage": "none", "temporal_ok": true, "baseline_reported": true, "reproducible": true, "findings": [], "confidence": "high"}
```

## Verdict

The auditor reported no leakage and no findings, so no finding changes a number. I agree with that, and I checked it myself rather than relying on the model. The raw CSV in the audited repo has the expected sha256 prefix (a6bed1577f6e4de5). `make all` and `make test` run clean (15 tests pass at the audited commit). The new feature, `cnt_roll_range_7`, is built from `shift(1)` before the rolling max and min, so it uses only the seven days before the forecast date, and its hand-computed value on 2011-03-18 (2744 minus 1977 = 767) matches the feature table (767.0). The excluded columns (`casual`, `registered`, time indexes) stay excluded through the shared config. One caveat: a clean report from a 9b model is weak evidence, and it cannot see anything it was not pointed at, so I treat it as a complement to the tests. The classmate's own DECISIONS.md shows the feature helped ridge on validation and hurt HGB, which is a modelling result, not a leakage issue.
