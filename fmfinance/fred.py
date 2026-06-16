import os
import pandas as pd
import requests
from ._utils import apply_cooldown


def fred(symbols, start, end=None, freq=None, agg=None, units=None, cooldown=1.2, api_key=None):
    # --- API key ---
    key = api_key or os.environ.get("FRED_API_KEY")
    if not key:
        raise PermissionError(
            "\n\n"
            "  FRED API key not found.\n"
            "  Run this in a cell before calling fred():\n\n"
            '      import os\n'
            '      os.environ["FRED_API_KEY"] = "your_key_here"\n\n'
            "  Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html\n"
        )

    # --- validazione parametri ---
    freq_map = {'d': 'd', 'w': 'w', 'm': 'm', 'q': 'q', 'a': 'a',
                'daily': 'd', 'weekly': 'w', 'monthly': 'm', 'quarterly': 'q', 'annual': 'a'}
    agg_map = {'avg': 'avg', 'sum': 'sum', 'eop': 'eop'}
    valid_units = {'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'}

    if freq is not None:
        actual_freq = freq_map.get(freq.lower() if isinstance(freq, str) else freq)
        if actual_freq is None:
            raise ValueError(f"freq='{freq}' non valido. Usa: {list(freq_map.keys())}")
    else:
        actual_freq = None

    if agg is not None:
        actual_agg = agg_map.get(agg.lower() if isinstance(agg, str) else agg)
        if actual_agg is None:
            raise ValueError(f"agg='{agg}' non valido. Usa: {list(agg_map.keys())}")
    else:
        actual_agg = None

    if units is not None:
        actual_units = units.lower() if isinstance(units, str) else None
        if actual_units not in valid_units:
            raise ValueError(f"units='{units}' non valido. Usa: {valid_units}")
    else:
        actual_units = None

    if actual_agg and not actual_freq:
        print("Warning: 'agg' ignored because 'freq' is not specified.")
        actual_agg = None

    # --- download ---
    names = [symbols] if isinstance(symbols, str) else symbols
    series_list = []
    session = requests.Session()
    base_url = "https://api.stlouisfed.org/fred/series/observations"

    for name in names:
        if len(series_list) > 0: apply_cooldown(cooldown)
        params = {
            "series_id": name,
            "api_key": key,
            "file_type": "json",
            "observation_start": start,
        }
        if end: params["observation_end"] = end
        if actual_freq: params["frequency"] = actual_freq
        if actual_agg: params["aggregation_method"] = actual_agg
        if actual_units: params["units"] = actual_units

        try:
            resp = session.get(base_url, params=params, timeout=15)
            resp.raise_for_status()
            obs = resp.json()["observations"]
            data = pd.DataFrame(obs)[["date", "value"]]
            data["date"] = pd.to_datetime(data["date"])
            data["value"] = pd.to_numeric(data["value"], errors="coerce")
            data = data.set_index("date")
            data.index.name = "DATE"
            data.columns = [name]
            series_list.append(data)
        except Exception as e:
            print(f"Warning: could not download '{name}': {e}")
            continue

    if not series_list:
        print("Warning: no data was downloaded.")
        return pd.DataFrame()
    return pd.concat(series_list, axis=1, join="outer")