import pandas as pd
import requests
import io
from ._utils import apply_cooldown

def fred(symbols, start, end=None, freq=None, agg=None, units=None, cooldown=1.2):
    valid_freqs = {'d': 'Daily', 'w': 'Weekly', 'm': 'Monthly', 'q': 'Quarterly', 'a': 'Annual'}
    actual_fq = None
    if isinstance(freq, str):
        f_low = freq.lower()
        for key, value in valid_freqs.items():
            if f_low == key or f_low == value.lower():
                actual_fq = value
                break
    
    actual_agg = agg.lower() if agg in {'avg', 'sum', 'eop'} else None
    actual_units = units.lower() if units in {'lin', 'chg', 'pch', 'pca', 'cch', 'cca'} else None
    names = [symbols] if isinstance(symbols, str) else symbols
    series_list = []

    for name in names:
        if len(series_list) > 0: apply_cooldown(cooldown)
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={name}"
        if actual_agg: url += f"&aggregationmethod={actual_agg}"
        if actual_units: url += f"&transformation={actual_units}"
        if actual_fq: url += f"&fq={actual_fq}"
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            data = pd.read_csv(io.StringIO(resp.text), index_col=0, parse_dates=True, 
                               header=None, skiprows=1, names=["DATE", name], na_values=".")
            data = data[data.index >= pd.to_datetime(start)]
            if end: data = data[data.index <= pd.to_datetime(end)]
            series_list.append(data)
        except Exception as e:
            print(f"Warning: could not download '{name}': {e}")
            continue
    if not series_list:
        print("Warning: no data was downloaded.")
        return pd.DataFrame()
    return pd.concat(series_list, axis=1, join="outer")