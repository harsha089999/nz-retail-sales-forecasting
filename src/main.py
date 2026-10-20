"""Retail sales forecasting on real ABS data: compare models per industry, forecast ahead, export for Power BI.

Data: Australian Bureau of Statistics, Retail Trade (cat. 8501.0), monthly turnover by state and industry,
as packaged in the tsibbledata R package (aus_retail). Stored in data/aus_retail.csv.gz.
"""
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "aus_retail.csv.gz"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

INDUSTRIES = ["Supermarket and grocery stores", "Hardware, building and garden supplies retailing",
              "Clothing retailing", "Cafes, restaurants and takeaway food services", "Department stores"]
START = "2005-01"          # use the most recent ~14 years
TEST_M, HORIZON = 24, 12   # backtest on last 24 months, forecast 12 ahead


def load() -> pd.DataFrame:
    """National monthly turnover (AUD millions) per industry = sum of the state series."""
    raw = pd.read_csv(DATA)
    raw = raw[raw.Industry.isin(INDUSTRIES) & (raw.Month >= START)]
    # some state/industry series are suppressed by the ABS; only sum months where every state reported
    n_states = raw.groupby("Industry").State.nunique()
    df = (raw.groupby(["Industry", "Month"])
          .agg(turnover_aud_m=("Turnover", "sum"), states=("State", "nunique")).reset_index())
    df = df[df.states == df.Industry.map(n_states)].drop(columns="states")
    df["Month"] = pd.PeriodIndex(df.Month, freq="M")
    return df.rename(columns={"Industry": "industry", "Month": "month"})


def mape(y, yhat):
    return float(np.mean(np.abs((y - yhat) / y)) * 100)


def fit_predict(name, train, steps):
    if name == "seasonal_naive":
        return np.tile(train[-12:], steps // 12 + 1)[:steps]
    if name == "holt_winters":
        m = ExponentialSmoothing(np.log(train), trend="add", seasonal="add", seasonal_periods=12).fit()
        return np.exp(m.forecast(steps))
    m = SARIMAX(np.log(train), order=(1, 1, 1), seasonal_order=(0, 1, 1, 12)).fit(disp=False)
    return np.exp(m.forecast(steps))


def main():
    df = load()
    print(f"Loaded {len(df):,} rows: {df.month.min()} to {df.month.max()}, {df.industry.nunique()} industries\n")
    scores, forecasts = [], []
    for ind, g in df.groupby("industry"):
        g = g.sort_values("month")
        y = g["turnover_aud_m"].to_numpy()
        train, test = y[:-TEST_M], y[-TEST_M:]
        results = {m: mape(test, fit_predict(m, train, TEST_M))
                   for m in ["seasonal_naive", "holt_winters", "sarima"]}
        best = min(results, key=results.get)
        scores += [{"industry": ind, "model": m, "test_mape": round(s, 2), "chosen": m == best}
                   for m, s in results.items()]

        fc = fit_predict(best, y, HORIZON)
        # interval from backtest errors, in percentage terms so it scales with the level
        pct_err = (test - fit_predict(best, train, TEST_M)) / test
        sd = np.std(pct_err)
        last = g["month"].max()
        for h, v in enumerate(fc, 1):
            forecasts.append({"industry": ind, "month": str(last + h), "type": "forecast",
                              "turnover_aud_m": round(v, 1),
                              "lower_80": round(v * (1 - 1.28 * sd), 1),
                              "upper_80": round(v * (1 + 1.28 * sd), 1), "model": best})

    actuals = df.assign(month=df["month"].astype(str), type="actual")
    pd.concat([actuals, pd.DataFrame(forecasts)]).to_csv(OUT / "forecast.csv", index=False)
    scores = pd.DataFrame(scores)
    scores.to_csv(OUT / "model_scores.csv", index=False)
    print(scores.pivot(index="industry", columns="model", values="test_mape").to_string())
    print("\nChosen per industry:")
    print(scores.query("chosen")[["industry", "model", "test_mape"]].to_string(index=False))


if __name__ == "__main__":
    main()
