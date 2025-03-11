---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.1
  kernelspec:
    display_name: ds-aa-ssd-flooding
    language: python
    name: ds-aa-ssd-flooding
---

# Exposure export

Exporting flood exposure data to CSV

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import pandas as pd

from src.utils import db_utils, blob_utils
```

```python
pcode = "SS"
query = f"SELECT * FROM app.floodscan_exposure WHERE pcode = '{pcode}'"
```

```python
query
```

```python
df_exp = pd.read_sql(query, db_utils.get_engine(), parse_dates=["valid_date"])
df_exp["sum"] = df_exp["sum"].astype(int)
```

```python
df_exp.dtypes
```

```python
df_exp["doy"] = df_exp["valid_date"].dt.dayofyear
df_exp["year"] = df_exp["valid_date"].dt.year
df_exp["date_1900"] = pd.to_datetime(df_exp["doy"], format="%j")
```

```python
df_exp
```

```python
df_exp.pivot(index="date_1900", columns="year", values="sum").plot()
```

```python
blob_name = f"{blob_utils.PROJECT_PREFIX}/processed/floodscan/{pcode}_flood_exposure.csv"
blob_utils.upload_csv_to_blob(df_exp, blob_name)
```
