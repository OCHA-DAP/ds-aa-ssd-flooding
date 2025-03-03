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

# SEAS5

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import calendar

import matplotlib.pyplot as plt
import xarray as xr

from src.datasources import seas5
from src.utils import blob_utils
```

```python
df_seas5 = seas5.load_seas5(pcode="SS")
```

```python
df_seas5[df_seas5["issued_date"].dt.month == 2].sort_values(
    ["issued_date", "valid_date"]
).iloc[-14:]
```

```python
issued_month = 2
valid_months = [6, 7, 8]
```

```python
df_jj = (
    df_seas5[
        (df_seas5["valid_date"].dt.month.isin(valid_months))
        & (df_seas5["issued_date"].dt.month == issued_month)
        & (df_seas5["valid_date"].dt.year >= 1998)
    ]
    .groupby("issued_date")["mean"]
    .mean()
    .reset_index()
)
df_jj["year"] = df_jj["issued_date"].dt.year
```

```python
df_jj
```

```python
df_jj
```

```python
issued_month_str = calendar.month_abbr[issued_month]
```

```python
valid_months_str = "".join([calendar.month_abbr[x][0] for x in valid_months])
```

```python
thresh = df_jj["mean"].quantile(2 / 3)

fig, ax = plt.subplots(dpi=200)

current_val = df_jj[df_jj["issued_date"].dt.year == 2025].iloc[0]["mean"]

ax.annotate(" 2025", (2025, current_val), ha="left", va="bottom", fontsize=8)

for rp, color in zip([3, 5], ["darkorange", "crimson"]):
    thresh = df_jj["mean"].quantile((rp - 1) / rp)
    ax.axhline(thresh, color=color)
    ax.annotate(
        f" {rp}-yr RP", (2027, thresh), va="center", ha="left", color=color
    )

df_jj.plot(x="year", y="mean", ax=ax, legend=False, color="k")

current_val = df_jj.set_index("year").loc[2025, "mean"]
ax.plot(
    [2025],
    [current_val],
    marker=".",
    color="k",
    markersize=10,
)

ax.set_title(
    "South Sudan SEAS5 forecast (since 1998)\n"
    f"Issued: {issued_month_str}, Valid: {valid_months_str}"
)
ax.set_xlabel("Year")
ax.set_ylabel("Mean daily precipitation,\n averaged over whole country (mm)")

ax.set_xlim(left=1998, right=2027)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
```

```python

```

```python
adm_ni =
```

```python
ADM1_AOI_PCODES = ["NI25", "NI20", "NI05", "NI40"]
```

```python
df_seas5 = seas5.load_seas5_multiple_pcodes(ADM1_AOI_PCODES)
```

```python
df_seas5
```

```python
issued_month = 2
valid_months = [5, 6, 7, 8]
```

```python
df_seas5[
    (df_seas5["valid_date"].dt.month.isin(valid_months))
    & (df_seas5["issued_date"].dt.month == issued_month)
    # & (df_seas5["valid_date"].dt.year >= 1998)
]
```

```python
df_season = (
    df_seas5[
        (df_seas5["valid_date"].dt.month.isin(valid_months))
        & (df_seas5["issued_date"].dt.month == issued_month)
        # & (df_seas5["valid_date"].dt.year >= 1998)
    ]
    .groupby("issued_date")
    .apply(
        lambda x: (x["mean"] * x["count"]).sum() / x["count"].sum(),
        include_groups=False,
    )
    .reset_index(name="mean")
)
df_season["year"] = df_season["issued_date"].dt.year
df_season
```

```python
df_season["rank"] = df_season["mean"].rank()
df_season["rp"] = (len(df_season) + 1) / df_season["rank"]
```

```python
df_season
```

```python
df_season.sort_values("mean")
```

```python

```
