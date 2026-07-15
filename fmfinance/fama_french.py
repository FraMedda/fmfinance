import pandas as pd
import requests
import io
import re
import zipfile
from ._utils import apply_cooldown

def ff_search(search=None):
    url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        resp.raise_for_status()
        all_names = sorted(list(set(re.compile(r'ftp/([\w-]+)_CSV\.zip').findall(resp.text))))
        
        if not search:
            for name in all_names:
                print(name)
            return
        
        search_lower = search.lower()
        shortcuts = {
            "3 factors": ["F-F_Research_Data_Factors", "F-F_Research_Data_Factors_daily", "F-F_Research_Data_Factors_weekly"],
            "4 factors": ["F-F_Momentum_Factor", "F-F_Momentum_Factor_daily"],
            "carhart": ["F-F_Momentum_Factor", "F-F_Momentum_Factor_daily"],
            "25": ["25_Portfolios_5x5"]
        }
        
        sugg = [n for k, v in shortcuts.items() if k in search_lower for n in v if n in all_names]
        others = [n for n in all_names if all(t in n.lower().replace('_', ' ') for t in search_lower.split()) and n not in sugg]
        
        print(f"\nResults for: '{search}'\n" + "-"*30)
        if sugg:
            print("SUGGESTIONS:")
            for s in set(sugg):
                print(f" > {s}")
        if others:
            print("\nOTHER MATCHES:")
            for o in others:
                print(f" > {o}")
    except Exception as e:
        print(f"Error searching datasets: {e}")

def ff(dataset_name, start, end=None, cooldown=1.2):
    # Custom dataset names (not available on French's website):
    # 'F-F_Research_Data_Factors_Yearly' -> annual table from F-F_Research_Data_Factors
    # '4_factors'                        -> Carhart 4-factor (FF3 + Momentum), monthly
    # '4_factors_daily'                  -> Carhart 4-factor (FF3 + Momentum), daily
    # '4_factors_Yearly'                 -> Carhart 4-factor (FF3 + Momentum), annual
    if dataset_name == 'F-F_Research_Data_Factors_Yearly':
        data = ff('F-F_Research_Data_Factors', start, end, cooldown)
        return {0: data.get(1, pd.DataFrame()), "DESCR": "Fama-French 3 Factors (Annual)"}
    
    if '4_factors' in dataset_name:
        suffix, idx = ("_daily", 0) if 'daily' in dataset_name else ("", 1 if 'Yearly' in dataset_name else 0)
        ff3_all = ff(f'F-F_Research_Data_Factors{suffix}', start, end, cooldown)
        mom_all = ff(f'F-F_Momentum_Factor{suffix}', start, end, cooldown)
        ff3, mom = ff3_all.get(idx, pd.DataFrame()), mom_all.get(idx, pd.DataFrame())
        combined = pd.concat([ff3, mom], axis=1, join='inner')
        cols = [c for c in combined.columns if c != 'RF'] + ['RF']
        return {0: combined[cols], "DESCR": "Carhart 4-Factor Model"}
    
    if 'Momentum' in dataset_name:
        return _ff_momentum(dataset_name, start, end, cooldown)

    apply_cooldown(cooldown)
    url = f"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{dataset_name}_CSV.zip"
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        resp.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            raw_data = zf.read(zf.namelist()[0]).decode('utf-8', errors='replace')
        chunks = raw_data.split("\r\n\r\n")
        tables = [c for c in chunks if c.strip() and re.search(r"^\s*\d{4,8}\s*,", c, re.M)]
        res = {}
        for i, src in enumerate(tables):
            match = re.search(r"^\s*,", src, re.M)
            df = pd.read_csv(io.StringIO("Date" + src[match.start():] if match else src), index_col=0)
            
            if df.index.empty:
                res[i] = pd.DataFrame()
                continue
            
            sample = str(df.index[0]).strip().replace(".0", "")
            if len(sample) <= 4:
                date_format = "%Y"
            elif len(sample) == 6:
                date_format = "%Y%m"
            else:
                date_format = "%Y%m%d"
            
            df.index = pd.to_datetime(df.index.astype(str).str.replace(".0", "").str.strip(), errors='coerce', format=date_format)
            df = df[df.index.notnull() & (df.index >= pd.to_datetime(start))]
            if end: df = df[df.index <= pd.to_datetime(end)]
            res[i] = df.apply(pd.to_numeric, errors='coerce')
        res["DESCR"] = f"Dataset: {dataset_name}"
        return res
    except Exception as e:
        if "404" in str(e) or "Bad request" in str(e).lower():
            print(f"Dataset '{dataset_name}' not found. Use ff_search() to find valid dataset names.")
        else:
            print(f"Error downloading '{dataset_name}': {e}")
        return {0: pd.DataFrame(), "DESCR": "Error"}
    
def _ff_momentum(dataset_name, start, end, cooldown):
    apply_cooldown(cooldown)
    url = f"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{dataset_name}_CSV.zip"
    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        raw = zf.read(zf.namelist()[0]).decode('utf-8', errors='replace')

    # righe 'data,valore' + testo di testa come descrizione
    rows, descr = [], []
    for line in raw.splitlines():
        parts = line.strip().split(',')
        is_data = False
        if len(parts) == 2 and parts[0].strip().isdigit():
            try:
                rows.append((parts[0].strip(), float(parts[1])))
                is_data = True
            except ValueError:
                pass
        if not is_data and not rows and line.strip() and not line.strip().startswith(','):
            descr.append(line.strip())

    res = {}
    for n, fmt in [(8, "%Y%m%d"), (6, "%Y%m"), (4, "%Y")]:
        sub = [(d, v) for d, v in rows if len(d) == n]
        if not sub:
            continue
        df = pd.DataFrame(sub, columns=["Date", "Mom"])
        df.index = pd.to_datetime(df.pop("Date"), format=fmt, errors='coerce')
        df = df[df.index.notnull() & (df.index >= pd.to_datetime(start))]
        if end:
            df = df[df.index <= pd.to_datetime(end)]
        res[len(res)] = df

    res["DESCR"] = f"Dataset: {dataset_name}\n" + "\n".join(descr)
    return res