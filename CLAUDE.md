# Bikeshare demand capstone

Daily Capital Bikeshare counts, 2011-2012. We forecast `cnt` (total daily
rides) from calendar, weather, and lagged-demand features.

## Commands
- `make data` - download raw CSV and assert its shape
- `make features` - build `data/processed/features.parquet`
- `make train` - fit models, write `reports/metrics.json`
- `make exercise4` - ratio-target hgb, write `reports/exercise4.json`
- `make test` - pytest; run this before claiming anything works
- `make all` - data, features, train in order

## Non-negotiable rules
- **Never** put `casual` or `registered` in a feature set:
  `casual + registered == cnt` exactly. `src/config.py` lists these and the
  other excluded columns (`cnt_2d_bfr`, raw time indexes) with the reason
  for each. Derive feature lists from `FORBIDDEN`; never hand-type them.
- **Never** split this data randomly. Use `src.train.temporal_split`.
  Train = 2011, valid = H1 2012, test = H2 2012. Never tune on test.
  Test is read once, at the very end, by `make exercise4` and `make train`.
- **Never** modify `data/raw/bike_daily.csv`, including via Bash `cp` or
  `sed`. The permission deny list does not cover Bash; the sha256 test does.
- Any new lag or rolling feature must be built on a gap-free calendar
  index (`src.features.reindex_to_calendar`) and must `.shift(1)` before
  it aggregates. Write the failing test in `tests/test_leakage.py` first,
  with a hand-computed value on a named date, then the feature.
- A new raw column must be added to `FORBIDDEN` or `SAFE_RAW_COLS` in
  `src/config.py` before anything uses it, or `test_contract.py` fails.
- Tests that guard `src/` behaviour go in `tests/test_leakage.py`, because
  the hook only re-runs that file. A test elsewhere is invisible to it.
- Report the mean baseline **and** the persistence baseline (yesterday's
  count) alongside every model. A negative R^2 is a finding, not a bug.
- Add one dated line to `docs/DECISIONS.md` per decision, newest last.
  If a feature's validation gain is under 0.01 R^2, say it is noise.

## Style
- Standard library, pandas, scikit-learn only. No new dependencies
  without asking. Versions are pinned in `requirements.txt`.
- Modules are runnable: `python -m src.<module>` prints a one-line `OK ...`
  summary or the metrics it wrote.
- Paths and constants live in `src/config.py`. Nothing is hardcoded twice.

## Gotchas
- The mirror in `DATA_URL` is missing 2011-03-10: 728 rows from 2011-01-03.
- `weather` uses `GOOD` / `MISTY` / `BAD`, not the UCI codes 1-4.
- Ridership grew ~65% from 2011 to 2012, so trees on raw `cnt` cannot
  extrapolate to 2012. Predicting `cnt / cnt_roll_7` is the fix we kept.
- 2012-10-29 (Hurricane Sandy, 22 rides) is in the test set.
