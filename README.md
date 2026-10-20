# Retail Sales Forecasting (ABS Retail Trade)

[![Run project](https://github.com/harsha089999/nz-retail-sales-forecasting/actions/workflows/run.yml/badge.svg)](https://github.com/harsha089999/nz-retail-sales-forecasting/actions/workflows/run.yml)

**Monthly turnover forecasts for five Australian retail industries, three competing models per industry, error bands, and a Power BI-ready export.**

> **About the data:** this project runs on a real public dataset, **Australian Bureau of Statistics, Retail Trade, Australia (cat. 8501.0)**, included in `data/` so it runs straight after cloning. Sources and licence are listed below and in [`data/README.md`](data/README.md).

## The business question

How much will each retail industry turn over in the next 12 months, and how confident can we be in that number?

## What this project does

A retailer's planning team needs a forecast they can trust and read in a dashboard, not a notebook. For each industry this script backtests three models on the last 24 months of real data, keeps whichever was most accurate for that industry, refits on the full history and forecasts 12 months ahead with an 80% band.

## The data

Real monthly retail turnover by state and industry from the ABS, April 1982 to December 2018. The script uses January 2005 onwards and sums the state series into a national total for five industries: supermarket and grocery, hardware and garden, clothing, cafes and takeaway, and department stores. A month is only kept if every state reported it, because the ABS suppresses some small state series.

**Source:**
- [ABS Retail Trade](https://www.abs.gov.au/statistics/industry/retail-and-wholesale-trade/retail-trade-australia)
- [tsibbledata `aus_retail` (the packaged copy used here)](https://github.com/tidyverts/tsibbledata)

**Licence:** ABS data is released under CC BY 4.0. Packaged in the tsibbledata R package (GPL-3).

## How it works

1. Load the raw ABS table, filter to the five industries, and sum states into a national monthly series (`load()`).
2. Hold out the last 24 months (2017-01 to 2018-12) as a test period.
3. Fit three models on the rest: **seasonal naive** (repeat last year), **Holt-Winters** (additive trend and seasonality on log turnover) and **SARIMA(1,1,1)(0,1,1,12)** on log turnover.
4. Score each by MAPE on the 24 test months and keep the lowest per industry.
5. Refit the winner on the full history and forecast 12 months ahead.
6. Build an 80% band from the spread of the backtest's percentage errors.
7. Write actuals and forecasts to one long CSV for Power BI, plus a model scorecard.

## Run it

```bash
git clone https://github.com/harsha089999/nz-retail-sales-forecasting
cd nz-retail-sales-forecasting
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

Outputs are written to `outputs/`. Python 3.10 or newer is recommended.

## Results from the included run

This is the actual console output when the script is run as shipped:

```text
Loaded 840 rows: 2005-01 to 2018-12, 5 industries

model                                             holt_winters  sarima  seasonal_naive
industry                                                                              
Cafes, restaurants and takeaway food services             3.58    3.38            5.05
Clothing retailing                                        4.80    5.09            3.71
Department stores                                         2.38    2.06            2.96
Hardware, building and garden supplies retailing          7.54    7.69            3.11
Supermarket and grocery stores                            1.43    2.05            4.50

Chosen per industry:
                                        industry          model  test_mape
   Cafes, restaurants and takeaway food services         sarima       3.38
                              Clothing retailing seasonal_naive       3.71
                               Department stores         sarima       2.06
Hardware, building and garden supplies retailing seasonal_naive       3.11
                  Supermarket and grocery stores   holt_winters       1.43
```

No single model won everywhere. Holt-Winters was best for supermarkets (1.4% MAPE), SARIMA for cafes and department stores, and plain seasonal naive beat both fitted models for clothing and hardware. That last point is the useful one: hardware growth slowed from 16% over the previous two years to 4% in the test window, so the models that carry the trend forward overshot by about 7.5%, while 'same month last year' stayed at 3.1%. Picking per series, and always comparing against a naive baseline, is the main lesson of the project.

## Output files

| File | What it contains |
|---|---|
| `outputs/forecast.csv` | Actuals and forecasts stacked: `industry, month, type (actual/forecast), turnover_aud_m, lower_80, upper_80, model`. |
| `outputs/model_scores.csv` | Test MAPE for every model and industry, with a `chosen` flag. |

## Limitations and honest caveats

- The data stops at December 2018, so COVID-era behaviour isn't in it. The method is the point, not a current forecast.
- The interval comes from backtest errors, not a model-based prediction interval. It will be too narrow if the next year breaks pattern.
- Turnover is in current prices, so part of the trend is inflation. A volume series would separate price from quantity.
- Summing state series means a month with any suppressed state is dropped for that industry.

## Turning it into a dashboard

A line chart of actuals plus forecast with the 80% band as a shaded area, an industry slicer, and a small table of each model's test error so a planner can see why a model was picked.

## Ideas to extend it

- Rolling-origin backtests instead of one 24-month split.
- Add the NZ Retail Trade Survey from Stats NZ (Infoshare) with the same code; only `load()` changes.
- Forecast at state level and reconcile up to the national total (hierarchical forecasting).

## Skills demonstrated

Time series forecasting, model selection by backtest, baselines, communicating uncertainty, shaping data for BI.

**Tools:** Python, pandas, statsmodels

## Project structure

```text
nz-retail-sales-forecasting/
├── src/main.py                 # the whole pipeline
├── data/                       # real source data (gzipped) + data/README.md with source and licence
├── outputs/                    # files from the run shown above
├── requirements.txt
├── .github/workflows/run.yml   # CI: installs and runs the project on every push
└── LICENSE
```

## Licence

Code: MIT, see [LICENSE](LICENSE). The data in `data/` keeps its original licence (see above).
