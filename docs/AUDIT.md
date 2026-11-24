# Audit of a classmate's repo

Audited repo: https://github.com/Azi23333/bikeshare-open
Commit audited: 9d07ad0
Date: 2026-11-24
Auditor model: bikeshare-coder (qwen3.5:9b, local Ollama, 64k context), Claude Code 2.1.327

## `/leakage-auditor` output (as printed by Claude Code)

My first attempts failed: "Use the leakage-auditor subagent" ended in "Invalid tool parameters", and a retry stalled on "Waiting for API response". Calling it as `@agent-leakage-auditor review the diff from 67dd845 to HEAD in this repo` worked. The subagent ran as a background agent on the local model and finished after 6 h 13 m. The text below is the final report Claude Code printed afterwards, pasted verbatim. I did not accept its offer to apply a fix.

```
Leakage Audit Results ✓

The subagent reviewed the diff from 67dd845 to HEAD and found one critical issue:

❌ Target Leakage Violation (src/features.py)

The build_features() function does not filter out forbidden columns before returning the feature dataframe. This means the parquet file at data/processed/features.parquet contains:
- casual, registered, cnt, instant, yr, days_since_2011, cnt_2d_bfr

These should never be in the feature set per CLAUDE.md: "Never put casual or registered in a feature set: casual + registered == cnt exactly."

Fix needed: Add filtering to drop forbidden columns before returning.

✅ Other Checks Pass

- Temporal split (train=2011, valid=H1 2012, test=H2 2012) ✓
- Calendar gap handling with lag/rolling features ✓
- Baseline reporting (mean + persistence) in metrics.json ✓

Would you like me to apply this fix now?
```

## Second auditor: `agent/audit.py` (Agent SDK, same local model)

```
{"repo": "/home/ediso/audited-repo", "leakage": "none", "temporal_ok": true, "baseline_reported": true, "reproducible": true, "findings": [], "confidence": "high"}
```

The two auditors disagree: this one reports no leakage and no findings.

## Verdict

I reject the one critical finding, and I agree with the other three checks (temporal split, calendar gap handling, baselines reported). The finding says `build_features()` leaves `casual`, `registered`, `cnt` and the other forbidden columns in `features.parquet`. That is true but it is not leakage. The parquet is the full feature table on purpose, and the model never reads it directly: `src/train.py` builds its inputs with `feature_columns()`, which drops everything in `FORBIDDEN`. I printed the table and the model inputs in the audited repo at 9d07ad0. All seven forbidden columns are in the table, and none is in the model inputs (temp, atemp, hum, windspeed, dayofweek, is_weekend, is_holiday, is_workday, month_sin, month_cos, weather_severity, cnt_lag_1, cnt_lag_7, cnt_roll_7, cnt_roll_range_7), and `test_no_forbidden_features` guards that gate and passes (15 tests). So the finding changes no reported number, and applying its suggested fix would have removed columns the pipeline needs. I also checked that the raw CSV hash matches (a6bed1577f6e4de5) and that the new feature `cnt_roll_range_7` shifts by one day before the rolling max and min (hand-computed value 2744 minus 1977 = 767 on 2011-03-18, matching the table). The disagreement between the two auditors, and the six hours the subagent needed on a 9b local model, are a reminder that a small model's report is evidence to verify, not a verdict.
