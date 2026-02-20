import pandas as pd
import requests
import io
import re
import zipfile
from ._utils import apply_cooldown

def FFSearch(search=None):
    url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        all_names = sorted(list(set(re.compile(r'ftp/([\w-]+)_CSV\.zip').findall(resp.text))))
        if not search:
            for name in all_names: print(name)
            return
        
        search_lower = search.lower()
        shortcuts = {
            "3 factors": ["F-F_Research_Data_Factors"],
            "4 factors": ["F-F_Momentum_Factor"],
            "carhart": ["F-F_Momentum_Factor"],
            "25": ["25_Portfolios_5x5"]
        }
        
        sugg = [n for k, v in shortcuts.items() if k in search_lower for n in v if n in all_names]
        others = [n for n in all_names if all(t in n.lower().replace('_',' ') for t in search_lower.split()) and n not in sugg]
        
        print(f"\nResults for: '{search}'\n" + "-"*30)
        if sugg:
            print("SUGGESTIONS:"); [print(f" > {s}") for s in set(sugg)]
        if others:
            print("\nOTHER MATCHES:"); [print(f" > {o}") for o in others]
    except Exception as e: print(f"Error: {e}")

def FFReader(dataset_name, start, end=None, cooldown=1.2):
    if dataset_name == 'F-F_Research_Data_Factors_Yearly':
        data = FFReader('F-F_Research_Data_Factors', start, end, cooldown)
        return {0: data.get(1, pd.DataFrame()), "DESCR": "Fama-French 3 Factors (Annual)"}
    
    if '4_factors' in dataset_name:
        suffix, idx = ("_daily", 0) if 'daily' in dataset_name else ("", 1 if 'Yearly' in dataset_name else 0)
        ff3_all = FFReader(f'F-F_Research_Data_Factors{suffix}', start, end, cooldown)
        mom_all = FFReader(f'F-F_Momentum_Factor{suffix}', start, end, cooldown)
        ff3, mom = ff3_all.get(idx, pd.DataFrame()), mom_all.get(idx, pd.DataFrame())
        combined = pd.concat([ff3, mom], axis=1, join='inner')
        cols = [c for c in combined.columns if c != 'RF'] + ['RF']
        return {0: combined[cols], "DESCR": "Carhart 4-Factor Model"}

    apply_cooldown(cooldown)
    url = f"https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{dataset_name}_CSV.zip"
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            raw_data = zf.read(zf.namelist()[0]).decode('utf-8', errors='replace')
        chunks = raw_data.split("\r\n\r\n")
        tables = [c for c in chunks if c.strip() and (len(c) >= 800 or re.search(r"^\s*,", c, re.M))]
        res = {}
        for i, src in enumerate(tables):
            match = re.search(r"^\s*,", src, re.M)
            df = pd.read_csv(io.StringIO("Date" + src[match.start():] if match else src), index_col=0)
            df.index = pd.to_datetime(df.index.astype(str).str.replace(".0", "").str.strip(), errors='coerce', 
                                     format="%Y" if len(str(df.index[0]))<=4 else "%Y%m" if len(str(df.index[0]))==6 else "%Y%m%d")
            df = df[df.index.notnull() & (df.index >= pd.to_datetime(start))]
            if end: df = df[df.index <= pd.to_datetime(end)]
            res[i] = df.apply(pd.to_numeric, errors='coerce')
        res["DESCR"] = f"Dataset: {dataset_name}"
        return res
    except: return {0: pd.DataFrame(), "DESCR": "Error"}