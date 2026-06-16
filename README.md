# fmfinance

A lightweight Python package to fetch financial data from the **Kenneth French Data Library** and the **St. Louis FED (FRED)**, plus a **cross-section bootstrap** engine for mutual fund performance analysis.

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

### Custom Dataset Names

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

### Cross-Section Bootstrap

Based on Kosowski et al. (2006) and Cuthbertson et al. (2008). Separates skill from luck in mutual fund performance by comparing observed t-alphas against a bootstrapped luck distribution.

```python
import fmfinance as fm
import numpy as np

np.random.seed(42)

# factors: DataFrame of risk factors (Mkt-RF, SMB, HML, MOM)
# funds: DataFrame of fund excess returns
alpha_obs, alpha_t_obs, alphas_boot, t_alphas_boot = fm.bootstrap(
    factors, funds, n_boot=1000, min_obs=36
)

# alpha_obs:     Series — observed alphas per fund
# alpha_t_obs:   Series — observed t-alphas per fund
# alphas_boot:   DataFrame (n_boot x n_funds) — simulated alphas under H0
# t_alphas_boot: DataFrame (n_boot x n_funds) — simulated t-alphas under H0
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
**Notes:**
- Data is sourced via the [FRED CSV Gateway](https://www.ivo-welch.info/professional/fredcsv.html) (cached, refreshed every 12h).
- `freq`, `agg`, and `units` are applied client-side in pandas; results may differ slightly from FRED's server-side transformations.
- `freq` without `agg` defaults to `'avg'`.
- `units='pca'` and `units='cca'` require `freq` to be specified.

### `bootstrap(factors, funds, n_boot, min_obs=36)`
| Parameter | Type | Description |
|---|---|---|
| `factors` | DataFrame | Risk factors (e.g. Mkt-RF, SMB, HML, MOM) |
| `funds` | DataFrame | Fund excess returns (one column per fund) |
| `n_boot` | int | Number of bootstrap simulations |
| `min_obs` | int | Minimum observations required per fund (default 36) |

Returns a tuple of 4 elements:
- `alpha_obs` — `pd.Series` of observed alphas
- `alpha_t_obs` — `pd.Series` of observed t-statistics of alpha
- `alphas_boot` — `pd.DataFrame` (n_boot × n_funds) of simulated alphas under H₀: α=0
- `t_alphas_boot` — `pd.DataFrame` (n_boot × n_funds) of simulated t-alphas under H₀: α=0

---

## Dependencies
- `pandas >= 2.0`
- `requests >= 2.28`
- `numpy >= 1.24`

---

## License
MIT — see [LICENSE](LICENSE) for details.