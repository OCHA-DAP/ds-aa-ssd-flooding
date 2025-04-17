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
<!-- markdownlint-disable MD013 -->
Loads SEAS5 and ERA5 forecasts for a `pcode` to plot current value compared to historical values.

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import calendar
from typing import List

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import xarray as xr
import numpy as np
import seaborn as sns
import ocha_stratus as stratus

from src.datasources import seas5, era5
from src.utils import blob_utils, rp_calc
```

```python
pcode = "SS"
```

```python
query = f"SELECT * FROM public.polygon WHERE pcode = '{pcode}'"
df_adm = pd.read_sql(query, stratus.get_engine(stage="prod"))
adm_name = df_adm.iloc[0]["name"]
```

```python
df_era5 = era5.load_era5(pcode=pcode)
```

```python
df_era5
```

```python
df_seas5 = seas5.load_seas5(pcode=pcode)
```

```python
df_seas5
```

```python
df_seas5.groupby(df_seas5["valid_date"].dt.month)["mean"].mean().plot()
```

```python
df_seas5.groupby(df_seas5["valid_date"].dt.month)["mean"].mean()
```

```python
calendar.month_abbr[3][0]
```

```python
issued_month = 4
valid_months = [7, 8, 9]
# valid_months = [4]
min_year = 2000

valid_mo_str = "".join([calendar.month_abbr[x][0] for x in valid_months])

df_plot = (
    df_seas5[
        (df_seas5["valid_date"].dt.month.isin(valid_months))
        & (df_seas5["issued_date"].dt.month == issued_month)
        & (df_seas5["valid_date"].dt.year >= min_year)
    ]
    .groupby("issued_date")["mean"]
    .mean()
    .reset_index()
)
df_plot["year"] = df_plot["issued_date"].dt.year

df_plot = rp_calc.calculate_one_group_rp(df_plot, ascending=False)

issued_month_str = calendar.month_abbr[issued_month]

valid_months_str = "".join([calendar.month_abbr[x][0] for x in valid_months])

thresh = df_plot["mean"].quantile(2 / 3)

fig, ax = plt.subplots(dpi=200)

current_row = df_plot[df_plot["issued_date"].dt.year == 2025].iloc[0]

ax.annotate(
    f"  2025\n  RP = {current_row['mean_rp']:.1f} yrs",
    (2025, current_row["mean"]),
    ha="left",
    va="center",
    fontsize=8,
)

for rp, color in zip([3, 5], ["darkorange", "crimson"]):
    thresh = df_plot["mean"].quantile((rp - 1) / rp)
    ax.axhline(thresh, color=color)
    ax.annotate(
        f" {rp}-yr RP", (2027, thresh), va="center", ha="left", color=color
    )

df_plot.plot(x="year", y="mean", ax=ax, legend=False, color="k")

ax.plot(
    [2025],
    [current_row["mean"]],
    marker=".",
    color="k",
    markersize=10,
)

ax.set_title(
    f"{adm_name} SEAS5 forecast (since {min_year})\n"
    f"Issued: {issued_month_str}, Valid: {valid_mo_str}"
)
ax.set_xlabel("Year")
ax.set_ylabel("Mean daily precipitation,\n averaged over whole country (mm)")

ax.set_xlim(left=min_year, right=2027)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
```

```python
df_compare = df_seas5.merge(
    df_era5,
    on=["valid_date", "pcode", "adm_level", "iso3"],
    suffixes=["_s", "_e"],
    how="left",
)
```

```python
df_season = (
    df_compare[
        (df_compare["valid_date"].dt.month.isin(valid_months))
        & (df_compare["issued_date"].dt.month == issued_month)
        & (df_compare["valid_date"].dt.year >= min_year)
    ]
    .groupby("issued_date")[["mean_s", "mean_e"]]
    .mean()
    .reset_index()
)
df_season["year"] = df_season["issued_date"].dt.year

corr = df_season.corr().loc["mean_s", "mean_e"]
```

```python
corr
```

```python
fig, ax = plt.subplots(figsize=(8, 8), dpi=200)

for year, row in df_season.set_index("year").iterrows():
    ax.annotate(
        year,
        (row["mean_s"], row["mean_e"]),
        ha="center",
        va="center",
        fontsize=7,
    )

df_season.plot(x="mean_s", y="mean_e", linewidth=0, legend=False, ax=ax)

current_row = df_season.set_index("year").loc[2025]
current_color = "crimson"

ax.axvline(current_row["mean_s"], color=current_color)
ax.annotate(
    f" {current_row['issued_date'].year}\n forecast",
    (current_row["mean_s"], df_season["mean_e"].max()),
    color="crimson",
)

ax.set_xlabel(
    f"Forecasted mean daily precipitation, issued {calendar.month_abbr[issued_month]} (mm)"
)
ax.set_ylabel("Actual mean daily precipitation (mm)")

ax.set_title(f"SEA5-ERA5 comparison for {adm_name}, valid {valid_mo_str}")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
```

## Full correlation analysis

Looking at correlation per leadtime per issued month.

```python
df_compare = df_seas5.merge(
    df_era5,
    on=["valid_date", "pcode", "adm_level", "iso3"],
    suffixes=["_s", "_e"],
    how="left",
)
```

```python
df_compare
```

```python
11 % 12 + 1
```

```python
dicts = []
for i_mo in range(1, 13):
    for v_mo in range(i_mo, i_mo + 7):
        v_mo = (v_mo - 1) % 12 + 1
        valid_months = [v_mo]
        min_year = 2000

        df_season = (
            df_compare[
                (df_compare["valid_date"].dt.month.isin(valid_months))
                & (df_compare["issued_date"].dt.month == i_mo)
                & (df_compare["valid_date"].dt.year >= min_year)
            ]
            .groupby("issued_date")[["mean_s", "mean_e"]]
            .mean()
            .reset_index()
        )
        df_season["year"] = df_season["issued_date"].dt.year

        corr = df_season.corr().loc["mean_s", "mean_e"]
        dicts.append({"i_mo": i_mo, "v_mo": v_mo, "corr": corr})
```

```python
df_corr = pd.DataFrame(dicts)
df_corr["lt"] = (df_corr["v_mo"] - df_corr["i_mo"]) % 12
```

```python
df_corr.pivot(index="lt", columns="i_mo", values="corr").plot()
```

```python
df_corr
```

```python
season_months = [7, 8, 9]

season_months_str = "".join([calendar.month_abbr[x][0] for x in season_months])

df_corr_pivot = df_corr.pivot(columns="lt", index="i_mo", values="corr")

df_condition = df_corr_pivot.astype(bool)

for lt in df_condition:
    df_condition[lt] = ((df_condition.index + lt - 1) % 12 + 1).isin(
        season_months
    )
condition = df_condition.to_numpy()

fig, ax = plt.subplots(dpi=200, figsize=(6, 6))

sns.heatmap(
    df_corr_pivot,
    annot=True,
    cmap="RdYlGn",
    fmt=".1f",
    cbar_kws={"label": "Correlation", "shrink": 0.7},
    annot_kws={"color": "black"},
    ax=ax,
    vmax=1,
    vmin=0,
    alpha=0.6,
)

for y_idx in range(df_corr_pivot.shape[0]):  # Iterate over rows (lt)
    for x_idx in range(df_corr_pivot.shape[1]):  # Iterate over columns (i_mo)
        if condition[y_idx, x_idx]:
            # Get the annotation text and set it to bold
            text = ax.texts[y_idx * df_corr_pivot.shape[1] + x_idx]
            text.set_fontweight("bold")

# contour = ax.contour(condition, levels=[0.5], colors="black", linewidths=2)
plt.title(
    f"SEAS5-ERA5 correlation for {pcode}\n"
    f"{season_months_str} season in "
    r"$\bf{bold}$"
)
plt.xlabel("Leadtime (months)")
plt.ylabel("Issue month")
plt.show()
```

## Nicaragua / other countries

Can ignore below - just sandbox for checking other countries or admins.

```python
ADM1_AOI_PCODES = ["NI25", "NI20", "NI05", "NI40"]
```

```python
df_seas5 = seas5.load_seas5_multiple_pcodes(ADM1_AOI_PCODES)
```

```python
df_seas5 = seas5.load_seas5("AO")
```

```python
df_seas5
```

```python
issued_month = 4
# valid_months = [5, 6, 7, 8]
# valid_months = [7, 8, 9]
valid_months = [4]
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
45 / 13
```

```python
issued_month = 3
valid_months = [7, 8, 9]
min_year = 1981

df_jj = (
    df_seas5[
        (df_seas5["valid_date"].dt.month.isin(valid_months))
        & (df_seas5["issued_date"].dt.month == issued_month)
        & (df_seas5["valid_date"].dt.year >= min_year)
    ]
    .groupby("issued_date")["mean"]
    .mean()
    .reset_index()
)
df_jj["year"] = df_jj["issued_date"].dt.year

df_jj = rp_calc.calculate_one_group_rp(df_jj, ascending=True)

issued_month_str = calendar.month_abbr[issued_month]

valid_months_str = "".join([calendar.month_abbr[x][0] for x in valid_months])

fig, ax = plt.subplots(dpi=200)

current_row = df_jj[df_jj["issued_date"].dt.year == 2025].iloc[0]

ax.annotate(
    f"  2025\n  RP = {current_row['mean_rp']:.1f} yrs",
    (2025, current_row["mean"]),
    ha="left",
    va="center",
    fontsize=8,
)

for rp, color in zip([3, 5], ["darkorange", "crimson"]):
    thresh = df_jj["mean"].quantile(1 / rp)
    ax.axhline(thresh, color=color)
    ax.annotate(
        f" {rp}-yr RP", (2027, thresh), va="center", ha="left", color=color
    )

df_jj.plot(x="year", y="mean", ax=ax, legend=False, color="k")

ax.plot(
    [2025],
    [current_row["mean"]],
    marker=".",
    color="k",
    markersize=10,
)

ax.set_title(
    f"South Sudan SEAS5 forecast (since {min_year})\n"
    f"Issued: {issued_month_str}, Valid: {valid_months_str}"
)
ax.set_xlabel("Year")
ax.set_ylabel("Mean daily precipitation,\n averaged over whole country (mm)")

ax.set_xlim(left=min_year, right=2027)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
```

```python

```
