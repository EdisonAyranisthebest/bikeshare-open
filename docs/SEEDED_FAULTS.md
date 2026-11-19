# Seeded faults

All output below is pasted from real runs in this repo (Python 3.13, pinned requirements). The faults were applied and reverted by hand with `git checkout`, and the hook was exercised by piping a PostToolUse JSON payload into `.claude/hooks/check_leakage.sh`, not by a live Claude Code session. See REPORT.md, Attribution.

## Step 0: failing feature test (written before the feature)

Commit 45aa43a. `python -m pytest tests/test_leakage.py -q`, tail:

```
name = 'cnt_roll_3'

    @final
    def __getattr__(self, name: str):
        """
        After regular attribute access, try looking up the name
        This allows simpler access to columns for interactive use.
        """
        # Note: obj.x will always call obj.__getattribute__('x') prior to
        # calling obj.__getattr__('x').
        if (
            name not in self._internal_names_set
            and name not in self._metadata
            and name not in self._accessors
            and self._info_axis._can_hold_identifiers_and_holds_name(name)
        ):
            return self[name]
>       return object.__getattribute__(self, name)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'Series' object has no attribute 'cnt_roll_3'. Did you mean: 'cnt_roll_7'?

.venv/lib/python3.13/site-packages/pandas/core/generic.py:6194: AttributeError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_cnt_roll_3_on_named_date - AttributeError:...
1 failed, 7 passed in 0.48s
```

## Fault 1: forbidden column in `feature_columns`

Commits: 7a3c416 (seed), 314ddd3 (fix)

Exact change:

```diff
diff --git a/src/features.py b/src/features.py
index d8cc103..c4af860 100644
--- a/src/features.py
+++ b/src/features.py
@@ -82,7 +82,7 @@ def build_features(df: pd.DataFrame) -> pd.DataFrame:
 def feature_columns(df: pd.DataFrame) -> list[str]:
     """Numeric columns that are safe to feed the model."""
     numeric = df.select_dtypes(include="number").columns
-    return [c for c in numeric if c not in FORBIDDEN]
+    return [c for c in numeric if c not in (FORBIDDEN - {"casual"})]
 
 
 if __name__ == "__main__":
```

Red test output (`python -m pytest tests/ -q`, tail):

```
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_3', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 14 passed in 1.21s
```

Hook stderr (hook script fed a PostToolUse payload for `src/features.py`; last line is its exit code):

```
Leakage tests failed after editing /home/claude/bs/bikeshare-open-starter/src/features.py:
feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....142857  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1531.428571  2077.333333

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_3', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 7 passed in 0.36s
exit 2
```

Caught by `test_no_forbidden_features`. Hook fired (exit 2). Turns to fix: 1 (revert, done by hand, not measured with the agent).
## Fault 2: remove `.shift(1)` in `cnt_roll_7`

Commits: ce41ed6 (seed), 79c3da7 (fix)

Exact change:

```diff
diff --git a/src/features.py b/src/features.py
index d8cc103..97a81f4 100644
--- a/src/features.py
+++ b/src/features.py
@@ -73,7 +73,7 @@ def build_features(df: pd.DataFrame) -> pd.DataFrame:
     # If you add a longer lag, raise LAG_WARMUP in src/config.py.
     out["cnt_lag_1"] = out[TARGET].shift(1)
     out["cnt_lag_7"] = out[TARGET].shift(LAG_WARMUP)
-    out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()
+    out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()
     out["cnt_roll_3"] = out[TARGET].shift(1).rolling(3).mean()
 
     return out.dropna().reset_index(drop=True)
```

Red test output (`python -m pytest tests/ -q`, tail):

```
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 15 passed in 1.31s
```

Hook stderr (hook script fed a PostToolUse payload for `src/features.py`; last line is its exit code):

```
Leakage tests failed after editing /home/claude/bs/bikeshare-open-starter/src/features.py:
[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:57: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 7 passed in 0.38s
exit 2
```

Caught by `test_rolling_mean_excludes_today`. Hook fired (exit 2). Turns to fix: 1 (revert, done by hand, not measured with the agent).
## Fault 3: remove the `raise` in `encode_weather`

### First attempt: the hook stayed silent

Commits: 2fb37d6 (test added), 3deffa1 (seed), e0ee68f (fix). The weather test lived in `tests/test_contract.py`, but the hook only runs `tests/test_leakage.py`.

```diff
diff --git a/src/features.py b/src/features.py
index d8cc103..63a2660 100644
--- a/src/features.py
+++ b/src/features.py
@@ -27,7 +27,7 @@ def encode_weather(series: pd.Series) -> pd.Series:
     known = series.dropna()
     unknown = set(known.unique()) - set(WEATHER_ORDER)
     if unknown:
-        raise ValueError(f"unmapped weather labels: {sorted(unknown)}")
+        pass
     return series.map(WEATHER_ORDER).astype(float)
```

`python -m pytest tests/ -q`:

```
>       with pytest.raises(ValueError, match="unmapped weather labels"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_contract.py:65: Failed
=========================== short test summary info ============================
FAILED tests/test_contract.py::test_encode_weather_raises_on_unknown_label - ...
1 failed, 15 passed in 1.22s
```

Hook stderr:

```
exit 0
```

The suite caught it but the hook exited 0: a hole in the hook's coverage, not in the tests. Fix: move the test into `tests/test_leakage.py` (commit c743992), and add a rule to CLAUDE.md.

### Retry

Commits: 6e2e224 (seed), 76da57e (fix)

Exact change:

```diff
diff --git a/src/features.py b/src/features.py
index d8cc103..63a2660 100644
--- a/src/features.py
+++ b/src/features.py
@@ -27,7 +27,7 @@ def encode_weather(series: pd.Series) -> pd.Series:
     known = series.dropna()
     unknown = set(known.unique()) - set(WEATHER_ORDER)
     if unknown:
-        raise ValueError(f"unmapped weather labels: {sorted(unknown)}")
+        pass
     return series.map(WEATHER_ORDER).astype(float)
```

Red test output (`python -m pytest tests/ -q`, tail):

```
    def test_encode_weather_raises_on_unknown_label():
        """An unseen weather label must raise, not silently become NaN."""
        from src.features import encode_weather
    
>       with pytest.raises(ValueError, match="unmapped weather labels"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:83: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_encode_weather_raises_on_unknown_label - F...
1 failed, 15 passed in 1.29s
```

Hook stderr (hook script fed a PostToolUse payload for `src/features.py`; last line is its exit code):

```
Leakage tests failed after editing /home/claude/bs/bikeshare-open-starter/src/features.py:
........F                                                                [100%]
=================================== FAILURES ===================================
_________________ test_encode_weather_raises_on_unknown_label __________________

    def test_encode_weather_raises_on_unknown_label():
        """An unseen weather label must raise, not silently become NaN."""
        from src.features import encode_weather
    
>       with pytest.raises(ValueError, match="unmapped weather labels"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:83: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_encode_weather_raises_on_unknown_label - F...
1 failed, 8 passed in 0.36s
exit 2
```

Caught by `test_encode_weather_raises_on_unknown_label`. Hook fired (exit 2). Turns to fix: 1 (revert, done by hand, not measured with the agent).
## Fault 4: a change the hook cannot see

Commits: 455ef0f (seed), 4c43237 (fix), 4df0d16 (catch).

What I did: ran `cp /tmp/raw_tampered2.csv data/raw/bike_daily.csv`, a copy of the CSV where the 2012-10-29 row (Hurricane Sandy, 22 rides) was changed to casual=100, registered=6900, cnt=7000. The row stays internally consistent, so `casual + registered == cnt` still holds. (My first tamper changed only cnt and registered, which broke that identity and an existing test caught it by accident. I redid it consistently.)

New sha256 (starts `143c5f69a78ab80a`, original starts `a6bed1577f6e4de5`):

```
143c5f69a78ab80af6ccc4b7d5681b88d3880e485ddc451e50af332227073034  data/raw/bike_daily.csv
```

`python -m pytest tests -q` before the catch existed:

```
.................                                                        [100%]
17 passed in 1.46s
```

All tests green. `make all` then silently moved the test-set numbers:

```
baseline_persistence {'r2': 0.4372, 'mae': 856.0}
ridge {'r2': 0.5564, 'mae': 936.7}
hgb {'r2': -0.6765, 'mae': 2012.0}
```

(Before tampering: persistence test R^2 0.5099, ridge 0.58, hgb -0.5338.)

Why nothing saw it: the hook matches only `Edit|Write` tool calls on paths containing `src/*.py`; a Bash `cp` is neither. The deny rules in `.claude/settings.json` cover `Write` and `Edit` on `data/raw/` and `Bash(rm -rf:*)`, not `cp`.

What catches it: a content check, not a permission. I added `test_raw_data_is_unmodified` (commit 4df0d16), which compares the file's sha256 prefix to the one in the assignment. Same tampered file, after the catch:

```
tests/test_contract.py:79: AssertionError
=========================== short test summary info ============================
FAILED tests/test_contract.py::test_raw_data_is_unmodified - AssertionError: ...
1 failed, 17 passed in 1.38s
```

Remaining gap: the check only runs when someone runs `make test`. A `Stop` hook that runs `make test` and exits 2 on failure would make it run before the agent can finish. Not implemented.

## Agent run: `/seed-fault no-shift` (2026-11-18)

Model: `bikeshare-coder` (qwen3.5:9b via local Ollama, 64k context), Claude Code 2.1.327. I ran `/seed-fault no-shift` in a live session. The agent checked `git status`, removed `.shift(1)` from the `cnt_roll_7` line in `src/features.py`, and the PostToolUse hook fired inside the session and reported `test_rolling_mean_excludes_today` failing (obtained 4389.0, expected 4414.857...). The agent named the test and printed the hook stderr, as the skill asks. I interrupted the run before its revert step, so a full red-to-green turn count was not measured. I restored the file with `git checkout -- src/features.py`; `make test` then gave 18 passed.
