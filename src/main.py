"""NZ retail sales forecasting: compare models, forecast ahead, export for Power BI."""
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

INDUSTRIES = ["Supermarket and grocery", "Hardware and garden", "Fuel retailing",
              "Clothing and footwear", "Food and beverage services"]
TEST_Q, HORIZON = 8, 4


def make_synthetic(seed: int = 42) -> pd.DataFrame:
    """Quarterly sales 2010Q1-2026Q2 with trend, Q4 peak and a 2020Q2 shock."""
    rng = np.random.default_rng(seed)
    idx = pd.period_range("2010Q1", "2026Q2", freq="Q")
    rows = []
    for i, ind in enumerate(INDUSTRIES):
        base = 800 + 400 * i
        trend = np.linspace(0, base * 0.6, len(idx))
        season = np.array([0, 0.02, 0.01, 0.08])[idx.quarter - 1] * base
        shock = np.where(idx == pd.Period("2020Q2", "Q"), -0.25 * base, 0)
        noise = rng.normal(0, base * 0.02, len(idx))
        for q, v in zip(idx, base + trend + season + shock + noise):
            rows.append({"quarter": q, "industry": ind, "sales_nzd_m": round(v, 1)})
    return pd.DataFrame(rows)


def mape(y, yhat):
    return float(np.mean(np.abs((y - yhat) / y)) * 100)


def fit_predict(name, train, steps):
    if name == "seasonal_naive":
        return np.tile(train[-4:], steps // 4 + 1)[:steps]
    if name == "holt_winters":
        m = ExponentialSmoothing(train, trend="add", seasonal="add", seasonal_periods=4).fit()
        return m.forecast(steps)
    m = SARIMAX(train, order=(1, 1, 1), seasonal_order=(0, 1, 1, 4)).fit(disp=False)
    return m.forecast(steps)


def main():
    df = make_synthetic()
    scores, forecasts = [], []
    for ind, g in df.groupby("industry"):
        y = g.sort_values("quarter")["sales_nzd_m"].to_numpy()
        train, test = y[:-TEST_Q], y[-TEST_Q:]
        results = {m: mape(test, fit_predict(m, train, TEST_Q))
                   for m in ["seasonal_naive", "holt_winters", "sarima"]}
        best = min(results, key=results.get)
        scores += [{"industry": ind, "model": m, "test_mape": round(s, 2), "chosen": m == best}
                   for m, s in results.items()]

        fc = fit_predict(best, y, HORIZON)
        resid_sd = np.std(test - fit_predict(best, train, TEST_Q))
        last = g["quarter"].max()
        for h, v in enumerate(fc, 1):
            forecasts.append({"industry": ind, "quarter": str(last + h), "type": "forecast",
                              "sales_nzd_m": round(v, 1),
                              "lower_80": round(v - 1.28 * resid_sd, 1),
                              "upper_80": round(v + 1.28 * resid_sd, 1), "model": best})

    actuals = df.assign(quarter=df["quarter"].astype(str), type="actual")
    pd.concat([actuals, pd.DataFrame(forecasts)]).to_csv(OUT / "forecast.csv", index=False)
    pd.DataFrame(scores).to_csv(OUT / "model_scores.csv", index=False)
    print(pd.DataFrame(scores).query("chosen")[["industry", "model", "test_mape"]].to_string(index=False))
    print(f"\nSaved outputs to {OUT}")


if __name__ == "__main__":
    main()
