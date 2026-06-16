import pandas as pd
import requests
import io
from ._utils import apply_cooldown


def fred(symbols, start, end=None, freq=None, agg=None, units=None, cooldown=1.2):
    # --- validazione parametri ---
    freq_map = {'d': 'D', 'w': 'W', 'm': 'MS', 'q': 'QS', 'a': 'YS',
                'daily': 'D', 'weekly': 'W', 'monthly': 'MS', 'quarterly': 'QS', 'annual': 'YS'}
    agg_map = {'avg': 'mean', 'sum': 'sum', 'eop': 'last'}
    valid_units = {'lin', 'chg', 'pch', 'pca', 'cch', 'cca'}

    if freq is not None:
        pd_freq = freq_map.get(freq.lower() if isinstance(freq, str) else freq)
        if pd_freq is None:
            raise ValueError(f"freq='{freq}' non valido. Usa: {list(freq_map.keys())}")
    else:
        pd_freq = None

    if agg is not None:
        pd_agg = agg_map.get(agg.lower() if isinstance(agg, str) else agg)
        if pd_agg is None:
            raise ValueError(f"agg='{agg}' non valido. Usa: {list(agg_map.keys())}")
    else:
        pd_agg = None

    if units is not None:
        actual_units = units.lower() if isinstance(units, str) else None
        if actual_units not in valid_units:
            raise ValueError(f"units='{units}' non valido. Usa: {valid_units}")
    else:
        actual_units = None

    if pd_agg and not pd_freq:
        print("Warning: 'agg' ignored because 'freq' is not specified.")
        pd_agg = None

    # --- download ---
    names = [symbols] if isinstance(symbols, str) else symbols
    series_list = []
    session = requests.Session()

    for name in names:
        if len(series_list) > 0: apply_cooldown(cooldown)
        url = f"https://www.ivo-welch.info/cgi-bin/fredwrap?symbol={name}"
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            data = pd.read_csv(io.StringIO(resp.text), index_col=0, parse_dates=True, na_values=".")
            data.columns = [name]
            data.index.name = "DATE"
            data = data[data.index >= pd.to_datetime(start)]
            if end: data = data[data.index <= pd.to_datetime(end)]

            # resample + aggregazione
            if pd_freq and pd_agg:
                data = data.resample(pd_freq).agg(pd_agg)
            elif pd_freq:
                data = data.resample(pd_freq).mean()

            # trasformazioni
            if actual_units == 'chg':
                data = data.diff()
            elif actual_units == 'pch':
                data = data.pct_change() * 100
            elif actual_units == 'pca':
                days = data.index.to_series().diff().dt.days.median()
                data = data.pct_change() * 100 * (365.25 / max(days, 1))
            elif actual_units == 'cch':
                if len(data) > 0:
                    data = data.apply(lambda s: (s / s.iloc[0] - 1) * 100)
            elif actual_units == 'cca':
                if len(data) > 1:
                    days = (data.index - data.index[0]).days.to_series(index=data.index).replace(0, 1)
                    data = data.apply(lambda s: ((s / s.iloc[0]) ** (365.25 / days) - 1) * 100)

            series_list.append(data)
        except Exception as e:
            print(f"Warning: could not download '{name}': {e}")
            continue

    if not series_list:
        print("Warning: no data was downloaded.")
        return pd.DataFrame()
    return pd.concat(series_list, axis=1, join="outer")