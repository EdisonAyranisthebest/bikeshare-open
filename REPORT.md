# Bikeshare demand: methodology report

## Results

Daily ridership `cnt`, temporal split (train 2011, validation H1 2012, test H2 2012). "before" is the starter pipeline's output (`reports/metrics_before_feature.json`), "after" adds `cnt_roll_3` (`reports/metrics.json`, from `make all`). Values are copied from those files.

| Model | cnt_roll_3 | Valid R^2 | Valid MAE | Test R^2 | Test MAE |
|---|---|---|---|---|---|
| mean baseline | before | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| mean baseline | after | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| persistence baseline | before | 0.4507 | 900.6 | 0.5099 | 840.1 |
| persistence baseline | after | 0.4507 | 900.6 | 0.5099 | 840.1 |
| ridge | before | 0.6475 | 832.9 | 0.5833 | 947.1 |
| ridge | after | 0.6439 | 836.5 | 0.58 | 946.2 |
| hgb | before | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| hgb | after | 0.1983 | 1311.6 | -0.5338 | 1998.7 |

Adding `cnt_roll_3` did not help: validation R^2 moved -0.0036 for ridge and -0.0202 for hgb, so by the `new-feature` skill's rule (under 0.01 is noise) it should be dropped. It is kept only because the assignment needs a feature in `src/features.py` (DECISIONS.md).

## Headline finding

Gradient boosting on raw `cnt` fails because of the 2011 to 2012 growth, not because of a bug: with the new feature hgb scores validation R^2 0.1983 and test R^2 -0.5338 (MAE 1998.7), against 0.6439 and 0.58 for ridge. Trees predict inside the range of the 2011 training target, and 2012 demand sits above it. The persistence baseline ("yesterday again") reaches test R^2 0.5099 with MAE 840.1 and no fitting; ridge's test R^2 is only 0.07 higher and its test MAE (946.2) is worse. A negative R^2 for hgb is reported as a finding, not hidden.

## Exercise 4: target transformation

All candidates were compared on validation only (hgb, `random_state=0`, `max_iter=300`); test was not read until the choice was fixed.

| Target for hgb | Valid R^2 | Valid MAE |
|---|---|---|
| raw `cnt` (reference) | 0.1983 | 1311.6 |
| `log1p(cnt)` | 0.1675 | 1342.0 |
| `cnt - cnt_lag_1` | 0.6251 | 805.4 |
| `cnt - cnt_roll_7` | 0.7209 | 722.4 |
| `cnt / cnt_roll_7` | 0.7483 | 681.5 |
| `log(cnt / cnt_roll_7)` | 0.7450 | 687.9 |

The chosen target is `cnt / cnt_roll_7`. Test, read once by `make exercise4`: R^2 0.6225, MAE 829.4 (validation 0.7483 and 681.5).

Defensible, with limits. `cnt_roll_7` shifts before it aggregates, so it excludes today and is known when the forecast is made; the model predicts a relative factor and the known recent level carries the growth trend that trees cannot extrapolate. It is not leakage. The caveats: the model is now anchored to a persistence-like level, so part of the gain is just a better baseline; I tried six targets on 182 validation days, so the winner's margin over `log(cnt / cnt_roll_7)` (0.0033) is noise, while the gap to raw `cnt` (0.55) is not; and test R^2 fell to 0.6225 from 0.7483, so the validation number overstates what to expect.

## Exercise 5: ridge vs persistence

I would not deploy ridge over persistence. On validation ridge looks clearly better (R^2 0.6439 vs 0.4507, MAE 836.5 vs 900.6, 7.1% lower), but on test the edge is 0.07 R^2 (0.58 vs 0.5099) while MAE flips to 946.2 against 840.1, 12.6% worse. Ridge also loses 0.0639 R^2 from validation to test while persistence gains 0.0592, which is what a model fitted on 2011 does when demand shifts and a fitted-nothing baseline does not. Persistence needs no training, no retraining schedule and no scaler, and a forecaster judged on average rides missed (MAE) is better served by it on the period that matters. Ridge is worth deploying only if squared error is the real cost and someone owns retraining. If a model is shipped, the ratio-target hgb (test R^2 0.6225, MAE 829.4) is the better candidate, though its MAE gain over persistence on test is only about 1.3%.

## Attribution

<!-- EDIT BEFORE SUBMITTING: confirm each line below is true for you. -->

Model used: Claude Sonnet 5.5, hosted, through the claude.ai chat interface. I did not use a local Ollama model (`qwen3.5:9b` or other) or Claude Code for this repository's content, and I did not switch models.

What the model generated: `tests/test_leakage.py` additions (`test_cnt_roll_3_on_named_date`, `test_encode_weather_raises_on_unknown_label`), `tests/test_contract.py` additions (column classification, sha256), the `cnt_roll_3` line in `src/features.py`, `SAFE_RAW_COLS` and `CLASSIFIED_COLS` in `src/config.py`, `src/exercise4.py`, the Makefile target, the `seed-fault` skill, the CLAUDE.md revision, the seeded-fault edits, and the first drafts of every document including this report.

Decisions that were mine: the {decisions to confirm} listed in `docs/DECISIONS.md` (feature choice, keeping the feature despite a negative delta, the Exercise 4 target, the ridge vs persistence call). Each traces to a dated line there and to a commit.

Not done by the agent: turns to fix for each seeded fault were not measured (I reverted by hand), the hook was tested by piping a payload into the script rather than from a live Claude Code session, and `reports/audit.jsonl` and `docs/AUDIT.md` come from my own runs of the auditors, not from this model.
