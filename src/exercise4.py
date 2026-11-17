"""Exercise 4: a target transformation that lets gradient boosting compete.

hgb on raw `cnt` fails because 2012 demand sits above anything in the 2011
training target and trees predict inside the training range. Here the model
predicts the ratio cnt / cnt_roll_7 instead, then multiplies the known
trailing level back in. cnt_roll_7 is shifted (excludes today), so the
divisor is available at prediction time.

Candidates were compared on validation only (see docs/DECISIONS.md). This
script reports validation for every split in play and touches test once.

Run: python -m src.exercise4
"""
import json

import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from src.config import PROCESSED, ROOT, TARGET
from src.features import feature_columns
from src.train import temporal_split

OUT = ROOT / "reports" / "exercise4.json"
LEVEL = "cnt_roll_7"


class RatioTargetRegressor(BaseEstimator, RegressorMixin):
    """Fit on cnt / level, predict level * fitted ratio."""

    def __init__(self, base, level: str = LEVEL):
        self.base = base
        self.level = level

    def fit(self, X, y):
        self.base.fit(X, y / X[self.level])
        return self

    def predict(self, X):
        return self.base.predict(X) * X[self.level].to_numpy(dtype=float)


def _score(model, part, cols):
    pred = model.predict(part[cols])
    return {
        "r2": round(float(r2_score(part[TARGET], pred)), 4),
        "mae": round(float(mean_absolute_error(part[TARGET], pred)), 1),
    }


if __name__ == "__main__":
    df = pd.read_parquet(PROCESSED)
    cols = feature_columns(df)
    train, valid, test = temporal_split(df)
    model = RatioTargetRegressor(HistGradientBoostingRegressor(random_state=0, max_iter=300))
    model.fit(train[cols], train[TARGET])
    res = {"hgb_ratio": {"valid": _score(model, valid, cols), "test": _score(model, test, cols)}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
