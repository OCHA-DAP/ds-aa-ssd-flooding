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

# AFG raster sense check

Sense-checking rasters for Afghanistan monitoring.

Not relevant for this repo but just put here for quick check.

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import os
from pathlib import Path

import xarray as xr
import rioxarray as rxr

from src.datasources import seas5
```

```python
DATA_DIR = Path(os.getenv("AA_DATA_DIR_NEW"))
```

```python
load_path = (
    DATA_DIR
    / "public"
    / "raw"
    / "glb"
    / "seas5"
    / "bfb42fc89f8b22dc387b995922460ef6.grib"
)
```

```python
ds_cds = xr.open_dataset(load_path, engine="cfgrib")
```

```python
ds_cds
```

```python
ds_cds = ds_cds.assign_coords(
    {"longitude": (ds_cds.coords["longitude"] - 180) % 360 - 180}
).sortby("longitude")
```

```python
ds_cds.isel(time=0).mean(dim="step")
```

```python
ds_cds.isel(time=0).mean(dim="step")["tprate"].plot()
```

```python
ds_cds.isel(time=1).mean(dim="step")
```

```python
ds_cds.isel(time=1).mean(dim="step")["tprate"].plot()
```

```python
(ds_cds.isel(time=1).mean(dim="step") - ds_cds.isel(time=0).mean(dim="step"))[
    "tprate"
].plot()
```

```python
das = []
for issued_date, stage in zip(["2024-01-01", "2025-01-01"], ["prod", "dev"]):
    das_lt = []
    for lt in [2, 3, 4]:
        print(issued_date, stage)
        da_in = seas5.load_seas5_raster(
            issued_date=issued_date, lt=lt, stage=stage
        )
        da_in["lt"] = lt
        das_lt.append(da_in)
    da_lt = xr.concat(das_lt, dim="lt")
    da_lt["issued_date"] = issued_date
    das.append(da_lt)

da = xr.concat(das, dim="issued_date")
```

```python
da_lt
```

```python
da_tri = da.mean(dim="lt")
```

```python
da_tri
```

```python
da_tri.isel(issued_date=1).plot()
```

```python
da_tri.isel(issued_date=0).plot()
```

```python
(da_tri.isel(issued_date=1) - da_tri.isel(issued_date=0)).plot()
```

```python
save_dir = DATA_DIR / "public" / "processed" / "glb" / "seas5"
```

```python
3600 * 24 * 1000
```

```python
ds_cds
```

```python
for year_i in [0, 1]:
    for lt in
    filename = f"seas5_issued_jan_valid_mam_{2024+year_i}.tif"
    output_path = save_dir / filename
    ds_cds = ds_cds.rio.write_crs(4326)
    (
        ds_cds.isel(time=year_i).mean(dim="step")["tprate"] * 3600 * 24 * 1000
    ).rio.to_raster(output_path, driver="COG")
```

```python
test = rxr.open_rasterio(output_path)
```

```python
test.plot()
```

## RP calc

```python
import pandas as pd

from src.utils import db_utils
```

```python
query = f"SELECT * FROM public.polygon WHERE iso3 = 'AFG' AND adm_level = 1"
df_adm = pd.read_sql(query, engine)
```

```python
df_adm
```

```python
engine = db_utils.get_engine("prod")
query = f"SELECT * FROM public.seas5 WHERE iso3 = 'AFG' AND adm_level = 1"
df = pd.read_sql(query, engine, parse_dates=["valid_date", "issued_date"])
```

```python
df
```

```python
df_jan_mam = (
    df[
        (df["valid_date"].dt.month.isin([3, 4, 5]))
        & (df["issued_date"].dt.month == 1)
    ]
    .groupby(["issued_date", "pcode"])["mean"]
    .mean()
    .reset_index()
)
df_jan_mam["year"] = df_jan_mam["issued_date"].dt.year
```

```python
df_jan_mam
```

```python
def calc_rp(group, col: str = "mean"):
    group["rank"] = group[col].rank(ascending=True)
    group["rp"] = (len(group) + 1) / group["rank"]
    return group
```

```python
df_rp = (
    df_jan_mam.groupby("pcode")
    .apply(calc_rp, include_groups=False)
    .reset_index()
    .drop(columns="level_1")
)
```

```python
df_rp
```

```python
df_rp = df_rp.merge(df_adm[["pcode", "name"]])
```

```python
df_rp[df_rp["year"] == 2025].plot.bar(x="name", y="rp")
```

```python
name_list = ["Badakhshan", "Takhar", "Sar-e-Pul", "Faryab"]
```

```python
df_rp[df_rp["name"].isin(name_list) & (df_rp["year"] == 2025)]
```

## Raster check

```python

```

```python
import matplotlib.pyplot as plt
import xarray as xr

from src.datasources import seas5
from src.utils import blob_utils
```

```python
blob_utils.list_container_blobs(
    name_starts_with="seas5/monthly/processed/",
    stage="prod",
    container_name="raster",
)
```

```python
das = []
for issued_date in ["2025-01-01", "2024-01-01", "2023-01-01"]:
    da_in = seas5.load_seas5_raster(issued_date=issued_date, lt=0)
    da_in["issued_date"] = issued_date
    das.append(da_in)

da = xr.concat(das, dim="issued_date")
```

```python
(da.isel(issued_date=0) - da.isel(issued_date=1)).plot()
```

```python
(da.isel(issued_date=1) - da.isel(issued_date=2)).plot()
```

```python
das = []
for issued_date, stage in zip(["2025-01-01", "2024-01-01"], ["dev", "prod"]):
    da_in = seas5.load_seas5_raster(issued_date=issued_date, lt=0, stage="dev")
    da_in["issued_date"] = issued_date
    das.append(da_in)

da = xr.concat(das, dim="issued_date")
```

```python
(da.isel(issued_date=0) - da.isel(issued_date=1)).plot()
```

```python
(da.isel(issued_date=1) - da.isel(issued_date=2)).plot()
```
