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

# Impact data

Subnational impact data from HDX

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
from io import BytesIO

import pandas as pd
import matplotlib.pyplot as plt

from src.utils import blob_utils
from src.datasources import codab
from src.constants import *
```

```python
adm2 = codab.load_codab_from_blob(admin_level=2)
```

```python
adm2.plot()
```

```python
df_all = pd.DataFrame(columns=["year", "ADM2_PCODE", "total_affected"])
```

```python
year = 2024
blob_name = f"{PROJECT_PREFIX}/raw/impact/ssd_flood_response_20122024.xlsx"

df_in = pd.read_excel(BytesIO(blob_utils._load_blob_data(blob_name)))

df_in = df_in.rename(
    columns={"Admin2_Pcode": "ADM2_PCODE", "People_Affected": "total_affected"}
)

df_in = df_in.dropna(subset="ADM2_PCODE")

assert all([x in adm2["ADM2_PCODE"].to_list() for x in df_in["ADM2_PCODE"]])

df_in["year"] = year

cols = ["ADM2_PCODE", "year", "total_affected"]
df_all = df_all.merge(df_in[cols], how="outer")
```

```python
fig, ax = plt.subplots()
adm2.merge(df_all).plot(
    column="total_affected", ax=ax, cmap="hot_r", legend=True
)
adm2.boundary.plot(ax=ax, color="k", linewidth=0.5)
```

```python
year = 2022
blob_name = (
    f"{PROJECT_PREFIX}/raw/impact/ss_floodsaffected_people_20211213.xlsx"
)
```

```python
df_in = pd.read_excel(BytesIO(blob_utils._load_blob_data(blob_name)))
```

```python
cols = ["State", "County", "Affected People"]
df_in = df_in[cols]
```

```python
df_in = df_in.dropna()
```

```python
isinstance()
```

```python
df_in = df_in[df_in["Affected People"]]
```

```python
df_all["total_affected"] = df_all["total_affected"].astype(int)
```

```python
df_all
```

```python

```
