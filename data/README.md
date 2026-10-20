# Data

Real data, not simulated. Files are the original CSVs, gzip-compressed to keep the repo small. pandas and DuckDB read
`.csv.gz` directly, so nothing needs unzipping.

**Dataset:** Australian Bureau of Statistics, Retail Trade, Australia (cat. 8501.0)

- [ABS Retail Trade](https://www.abs.gov.au/statistics/industry/retail-and-wholesale-trade/retail-trade-australia)
- [tsibbledata `aus_retail` (the packaged copy used here)](https://github.com/tidyverts/tsibbledata)

**Licence:** ABS data is released under CC BY 4.0. Packaged in the tsibbledata R package (GPL-3).

| File | Contents |
|---|---|
| `aus_retail.csv.gz` | 64,532 rows: state, industry, ABS series ID, month (1982-04 to 2018-12), turnover in AUD millions |

To refresh from Kaggle instead, download the dataset with the Kaggle CLI (`kaggle datasets download <owner/dataset>`),
then gzip the needed files into this folder with the same names.
