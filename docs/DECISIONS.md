# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.
- 2026-11-16: Add `cnt_roll_3` (3-day trailing mean, `shift(1)` before `rolling`, built after `reindex_to_calendar`). Available at prediction time because it only uses the three days before d. Validation delta: ridge R^2 0.6475 -> 0.6439 (-0.0036), hgb 0.2185 -> 0.1983 (-0.0202). Test failing first: 45aa43a; feature: 26321e9.
- 2026-11-16: Keep `cnt_roll_3` in the code anyway. The delta is negative and far inside the 0.01 noise band the `new-feature` skill uses, so on modelling grounds it should be dropped; it stays because the assignment requires a feature in `src/features.py`, and every result in REPORT.md is reported with and without it (commit 26321e9).
- 2026-11-16: Move `test_encode_weather_raises_on_unknown_label` from `tests/test_contract.py` to `tests/test_leakage.py`. First seeded run of fault 3 passed the hook silently because the hook only runs `test_leakage.py` (commits 2fb37d6, e0ee68f, c743992). Rule added to CLAUDE.md.
- 2026-11-16: Add `SAFE_RAW_COLS` / `CLASSIFIED_COLS` to `src/config.py` and `test_every_raw_column_is_classified` so a new raw column fails the suite until someone classifies it (commit c02e36d).
- 2026-11-16: Add `test_raw_data_is_unmodified` (sha256 prefix `a6bed1577f6e4de5`) to catch the fourth fault, a Bash `cp` into `data/raw/` that neither the hook nor the deny rules see (commits 455ef0f, 4c43237, 4df0d16).
- 2026-11-16: Exercise 4 choice: fit hgb on `cnt / cnt_roll_7` and multiply the level back. Chosen on validation only among raw, log1p, `cnt - cnt_lag_1`, `cnt - cnt_roll_7`, `cnt / cnt_roll_7`, `log(cnt / cnt_roll_7)`; validation R^2 0.7483 vs 0.1983 raw. Test read once, by `make exercise4` (commit 1fbd353).
- 2026-11-16: CLAUDE.md updated (49 lines): raw data immutable including via Bash, failing hand-computed test before any feature, hook-visible test location, raw-column classification, validation-only tuning, `make exercise4` (commit 891c934).
- 2026-11-16: Remove `reports/` from `.gitignore` so `metrics.json`, `exercise4.json` and `metrics_before_feature.json` are tracked; add the `seed-fault` skill (commit 891c934).
- 2026-11-18: Ran the seed-fault skill once in a live Claude Code session on the local model to confirm the skill and the hook work with an agent; the run was interrupted before the revert, so turns-to-fix stays unmeasured (docs/SEEDED_FAULTS.md).
- 2026-11-18: Ran `python agent/audit.py . --out reports/audit.jsonl` on this repo with bikeshare-coder (qwen3.5:9b, local). It reported leakage none, temporal_ok, baseline_reported and reproducible all true, and no findings, so nothing to fix. A clean report from a 9b model is weak evidence, so it complements the tests rather than replacing them (reports/audit.jsonl).
- 2026-11-18: Remove the `audit.jsonl` pattern from .gitignore so reports/audit.jsonl is tracked, as the submission requires (.gitignore).
- 2026-11-24: Audited a classmate repo (Azi23333/bikeshare-open) with agent/audit.py after the /leakage-auditor subagent failed on the local 9b model; no findings, verdict in docs/AUDIT.md.
