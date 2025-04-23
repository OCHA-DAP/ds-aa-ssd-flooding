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

# IRI

Check IRI seasonal forecast

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import calendar

import ocha_stratus as stratus
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm

from src.datasources import iri, codab
from src.utils.blob_utils import PROJECT_PREFIX
from src.utils import rp_calc
```

## Load and process data

```python
codab.download_codab_to_blob()
```

```python
adm = codab.load_codab_from_blob()
```

```python
adm.plot()
```

```python
ds_iri = iri.load_raw_iri()
```

```python
ds_iri
```

```python
da_season = ds_iri.sel(F=ds_iri.F[ds_iri.F.dt.month == 4], L=3).isel(C=-1)[
    "prob"
]
```

```python
da_season
```

```python
blob_name = f"{PROJECT_PREFIX}/raw/ssd_watershed.zip"
```

```python
gdf_shed = stratus.load_shp_from_blob(blob_name)
```

```python
gdf_shed.plot()
```

```python
blob_name = f"{PROJECT_PREFIX}/raw/ssd_rivers.zip"
```

```python
gdf_rivers = stratus.load_shp_from_blob(blob_name)
```

```python
gdf_rivers.plot()
```

```python
gdf_rivers[gdf_rivers["sorder"] > 3].plot()
```

```python
da_season = da_season.rio.write_crs(4326)
```

```python
def upsample_dataarray(
    da: xr.DataArray, resolution: float = 0.1
) -> xr.DataArray:
    new_lat = np.arange(da.Y.min() - 1, da.Y.max() + 1, resolution)
    new_lon = np.arange(da.X.min() - 1, da.X.max() + 1, resolution)
    return da.interp(
        Y=new_lat,
        X=new_lon,
        method="nearest",
        kwargs={"fill_value": "extrapolate"},
    )
```

```python
# clip before upsample to save memory
da_clip = da_season.rio.clip(gdf_shed.geometry, all_touched=True)
da_clip_up = upsample_dataarray(da_clip)
```

```python
da_clip_up_clip = da_clip_up.rio.clip(gdf_shed.geometry)
```

```python
da_clip_up_clip.isel(F=-1).plot()
```

## Plotting

### Watershed-level current forecast

```python
# Define your color boundaries and corresponding colors
bounds = [0, 33, 40, 45, 50, 60, 70, 100]  # Add 0 and 100 to cover full range
colors = [
    "khaki",
    "white",
    "palegreen",
    "limegreen",
    "seagreen",
    "royalblue",
    "navy",
]
cmap = mcolors.ListedColormap(colors)
norm = mcolors.BoundaryNorm(bounds, cmap.N)

da_plot = da_clip_up_clip.isel(F=-1)

fig, ax = plt.subplots(dpi=200)
adm.boundary.plot(ax=ax, linewidth=0.5, color="k")
da_plot.plot(
    ax=ax,
    cmap=cmap,
    norm=norm,
    alpha=0.9,
    cbar_kwargs={
        "label": "Probability of above-normal rainfall (%)",
        "shrink": 0.7,
    },
)
gdf_shed.boundary.plot(ax=ax, linewidth=0.5, color="grey", linestyle="--")
gdf_rivers[gdf_rivers["sorder"] > 4].plot(
    ax=ax, linewidth=0.3, color="dodgerblue"
)

valid_months_str = "".join(
    [
        calendar.month_abbr[
            int(da_plot.F.dt.month) + x + int(da_plot.L.values)
        ][0]
        for x in range(3)
    ]
)
issued_date_str = str(da_plot.F.values).split(" ")[0]

ax.axis("off")
ax.set_title(
    f"IRI forecast issued {issued_date_str} "
    f"for {valid_months_str},\n"
    "over watershed of White Nile at exit from South Sudan",
    fontsize=10,
)
```

### Mean over watershed per year

```python
da_mean = da_clip_up_clip.mean(dim=["X", "Y"])
```

```python
df_iri = da_mean.to_dataframe()["prob"].reset_index()
df_iri["year"] = df_iri["F"].astype(str).str[:4].astype(int)
df_iri["issued_month"] = df_iri["F"].astype(str).str[5:7].astype(int)
df_iri
```

```python
df_iri = rp_calc.calculate_one_group_rp(
    df_iri, ascending=False, col_name="prob"
)
```

```python
df_iri
```

```python
issued_mo_str = calendar.month_abbr[df_iri.iloc[0]["issued_month"]]
```

```python
fig, ax = plt.subplots(dpi=200)
df_iri.plot(
    x="year",
    y="prob",
    ax=ax,
    legend=False,
    kind="bar",
    width=0.7,
    color="royalblue",
)
ax.axhline(33.333, color="grey", linestyle="--")
ax.annotate(
    "theoretical\nclimatology\n(33%)",
    # (df_iri["year"].max() + 1, 33),
    (len(df_iri), 33.333),
    va="center",
    fontstyle="italic",
    color="grey",
)

# ax.set_xlim(left=df_iri["year"].min(), right=df_iri["year"].max() + 1)
ax.set_xlim(left=-0.5, right=len(df_iri))
ax.set_ylim(top=50, bottom=30)

ax.set_xlabel("Year")
ax.set_ylabel("Probability of above-normal rainfall (%)")
ax.set_title(f"IRI forecast issued {issued_mo_str} " f"for {valid_months_str}")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
```
