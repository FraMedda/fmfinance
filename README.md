# fmfinance

A lightweight Python package to fetch financial data from the **Kenneth French Data Library** and the **St. Louis FED (FRED)**, with no manual CSV or Excel imports required.

> **Disclaimer**: this package is not affiliated with or endorsed by Kenneth R. French, Dartmouth College, or the Federal Reserve Bank of St. Louis.

---

## Installation

```bash
pip install https://github.com/FraMedda/fmfinance/archive/refs/heads/main.zip
```

For local/development use:
```bash
pip install -e .
```

---

## Usage

### Fama-French factors

```python
import fmfinance as fm

# Search available datasets
fm.ff_search("3 factors")

# Download Fama-French 3 factors (monthly)
data = fm.ff("F-F_Research_Data_Factors", start="2000-01-01")
df = data[0]
print(df.head())

# Download with end date
data = fm.ff("F-F_Research_Data_Factors", start="2000-01-01", end="2020-12-31")

# Download daily data
data = fm.ff("F-F_Research_Data_Factors_daily", start="2020-01-01")
```
## Custom Dataset Names

Some dataset names are handled internally and do not correspond to files on the French library:

| Name | Description |
|---|---|
| `F-F_Research_Data_Factors_Yearly` | Annual version of the FF3 factors |
| `4_factors` | Carhart 4-factor model (monthly) |
| `4_factors_daily` | Carhart 4-factor model (daily) |
| `4_factors_Yearly` | Carhart 4-factor model (annual) |


### FRED data

```python
import fmfinance as fm

# Single series
df = fm.fred("GDP", start="2000-01-01")

# Multiple series
df = fm.fred(["GDP", "CPIAUCSL", "UNRATE"], start="2000-01-01")

# With frequency and transformation
df = fm.fred("GDP", start="2000-01-01", freq="q", units="pch")
```

---

## Parameters

### `ff(dataset_name, start, end=None, cooldown=1.2)`
| Parameter | Type | Description |
|---|---|---|
| `dataset_name` | str | Dataset name from the French library (use `ff_search` to find it) |
| `start` | str | Start date, e.g. `"2000-01-01"` |
| `end` | str | End date (optional) |
| `cooldown` | float | Seconds to wait between requests (default 1.2) |

Returns a `dict` where keys are integers (one per table in the dataset) and `"DESCR"` contains a description.

### `ff_search(search=None)`
Searches available datasets in the French library. If `search` is `None`, prints all available datasets.

### `fred(symbols, start, end=None, freq=None, agg=None, units=None, cooldown=1.2)`
| Parameter | Type | Description |
|---|---|---|
| `symbols` | str or list | One or more FRED series IDs |
| `start` | str | Start date |
| `end` | str | End date (optional) |
| `freq` | str | Frequency: `'d'`, `'w'`, `'m'`, `'q'`, `'a'` (optional) |
| `agg` | str | Aggregation method: `'avg'`, `'sum'`, `'eop'` (optional) |
| `units` | str | Transformation: `'lin'`, `'chg'`, `'pch'`, `'pca'`, `'cch'`, `'cca'` (optional) |
| `cooldown` | float | Seconds to wait between requests (default 1.2) |

Returns a `pandas.DataFrame` with one column per series.

---

## Dependencies
- `pandas >= 2.0`
- `requests >= 2.28`

---

## License
MIT — see [LICENSE](LICENSE) for details.