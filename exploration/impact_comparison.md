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

# Impact comparison
<!-- markdownlint-disable MD013 -->

Check that:

- rainfall is good predictor of flood extent
- flood extent is good predictor of impact
- CERF/CBPF allocations are well-matched with impact

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import calendar

import ocha_stratus as stratus
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from src.constants import *
from src.datasources import era5, seas5
```

## Load data

### Exposure

```python
pcode = "SS"
query = f"SELECT * FROM app.floodscan_exposure WHERE pcode = '{pcode}'"
```

```python
df_exp_daily = pd.read_sql(
    query, stratus.get_engine(stage="prod"), parse_dates=["valid_date"]
)
```

```python
df_exp_yearly = (
    df_exp_daily.groupby(df_exp_daily["valid_date"].dt.year)["sum"]
    .agg(["mean", "max", "min"])
    .reset_index()
)
df_exp_yearly["max_diff"] = df_exp_yearly["max"] - df_exp_yearly["min"]
df_exp_yearly["mean_diff"] = df_exp_yearly["mean"] - df_exp_yearly["min"]
```

```python
df_exp_yearly.set_index("valid_date").plot()
```

```python
df_exp_yearly = df_exp_yearly.rename(
    columns={
        x: f"{x}_exp"
        for x in df_exp_yearly.columns
        if x != "valid_date" and "exp" not in x
    }
)
```

```python
df_exp_yearly
```

### SEAS5

Load and filter SEAS5 data to specific `issued_month`.

```python
df_seas5_all = seas5.load_seas5(pcode=pcode)
```

```python
issued_month = 4
issued_mo_str = calendar.month_abbr[issued_month]
df_seas5_imo = df_seas5_all[
    df_seas5_all["issued_date"].dt.month == issued_month
]
```

```python
valid_months = sorted(df_seas5_imo["valid_date"].dt.month.unique())
valid_mo_str = "".join([calendar.month_abbr[x][0] for x in valid_months])
valid_mo_str
```

```python
df_seas5_yearly = (
    df_seas5_imo.groupby(df_seas5_imo["valid_date"].dt.year)["mean"]
    .mean()
    .reset_index()
)
```

```python
def detrend_column(
    df: pd.DataFrame, col: str, index_col: str = "valid_date"
) -> pd.DataFrame:
    """
    Detrend a column in a DataFrame using linear regression (via NumPy).

    Parameters:
    -----------
    df : pd.DataFrame
        The input DataFrame. Must contain a datetime column.
    col : str
        The name of the column to detrend.
    time_col : str
        The name of the datetime column. Default is "valid_date".

    Returns:
    --------
    pd.DataFrame
        Copy of the input DataFrame with a new column: <col>_detrended
    """
    df_sorted = df.sort_values(index_col).copy()

    # Convert datetime to numeric (days since min)
    x = df_sorted[index_col]
    y = df_sorted[col].values

    # Linear regression fit
    A = np.vstack([x, np.ones_like(x)]).T
    a, b = np.linalg.lstsq(A, y, rcond=None)[0]

    trend = a * x + b
    detrended = y - trend
    detrended += y.mean()  # Shift to preserve original mean

    df_sorted[f"{col}_detrended"] = detrended

    return df_sorted
```

```python
df_seas5_yearly = detrend_column(df_seas5_yearly, col="mean")
```

```python
df_seas5_yearly.set_index("valid_date").plot()
```

```python
df_seas5_yearly
```

### ERA5

Load and filter ERA5 data to same `valid_month`

```python
df_era5 = era5.load_era5(pcode=pcode)
```

```python
df_era5_yearly = (
    df_era5[df_era5["valid_date"].dt.month.isin(valid_months)]
    .groupby(df_era5["valid_date"].dt.year)["mean"]
    .mean()
    .reset_index()
)
df_era5_yearly = df_era5_yearly[df_era5_yearly["valid_date"] < 2025]
```

```python
df_era5_yearly = detrend_column(df_era5_yearly, "mean")
```

```python
df_era5_yearly.set_index("valid_date").plot()
```

### EM-DAT

```python
blob_name = f"{PROJECT_PREFIX}/raw/emdat/emdat_ssd_flooding_2025-04-17.csv"
df_emdat_events = stratus.load_csv_from_blob(blob_name)
```

```python
df_emdat_yearly = (
    df_emdat_events.groupby("Start Year")["Total Affected"].sum().reset_index()
)
```

```python
df_emdat_yearly.plot(x="Start Year", y="Total Affected", kind="bar")
```

## Combine

```python
df_compare = (
    df_exp_yearly.merge(
        df_era5_yearly.rename(
            columns={
                "mean": "mean_era5",
                "mean_detrended": "mean_era5_detrended",
            }
        )
    )
    .merge(df_seas5_yearly)
    .rename(
        columns={
            "mean": "mean_seas5",
            "mean_detrended": "mean_seas5_detrended",
        }
    )
    .merge(
        df_emdat_yearly.rename(
            columns={
                "Start Year": "valid_date",
                "Total Affected": "total_affected",
            }
        ),
        how="left",
    )
).rename(columns={"valid_date": "year"})
df_compare = df_compare[
    (df_compare["year"] < 2025) & (df_compare["year"] >= 2006)
]
df_compare["cerf"] = df_compare["year"].isin(CERF_YEARS)
df_compare = df_compare.fillna(0)
df_compare
```

```python
df_compare.set_index("year").corr()
```

```python
df_compare.set_index("year").corr()["total_affected"].plot(kind="bar")
```

```python
df_compare.set_index("year").corr()["mean_diff_exp"].plot(kind="bar")
```

```python
df_compare.set_index("year").corr()["cerf"].plot(kind="bar")
```

```python
def plot_comparison(df, xcol, ycol, sizecol=None, labels=None):
    df = df.copy()
    fig, ax = plt.subplots(dpi=200, figsize=(7, 7))

    # Replace NaN sizes with a small value
    if sizecol is None:
        sizes = np.full(len(df), 0)
    else:
        sizes = df[sizecol].fillna(0) / df[sizecol].max() * 1000

    # Set colors based on cerf
    df["color"] = df["cerf"].map({True: "crimson", False: "royalblue"})

    scatter = ax.scatter(
        df[xcol], df[ycol], s=sizes, c=df["color"], alpha=0.5, edgecolor="none"
    )

    # Annotate year on each point
    for year, row in df.set_index("year").iterrows():
        ax.annotate(
            str(year),
            (row[xcol], row[ycol]),
            fontsize=8,
            ha="center",
            va="center",
            color=row["color"],
        )

    if labels is None:
        ax.set_xlabel(xcol)
        ax.set_ylabel(ycol)
        ax.set_title("")
    else:
        ax.set_xlabel(labels["x"])
        ax.set_ylabel(labels["y"])
        ax.set_title(labels["title"])

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    return fig, ax
```

```python
plot_comparison(
    df_compare,
    "mean_diff_exp",
    "total_affected",
    labels={
        "x": "Average adjusted flood exposure during year [Floodscan]",
        "y": "Total people affected during year [EM-DAT]",
        "title": "Impact vs. exposure comparison",
    },
)
```

```python
fig, ax = plot_comparison(
    df_compare,
    "mean_era5",
    "mean_diff_exp",
    sizecol="total_affected",
    labels={
        "x": "Mean daily observed rainfall (mm) [ERA5]",
        "y": "Average adjusted flood exposure during year [Floodscan]",
        "title": "Exposure vs. observed rainfall comparison",
    },
)
```

```python
df_seas5_yearly.set_index("valid_date").loc[2025]["mean"]
```

```python
fig, ax = plot_comparison(
    df_compare,
    "mean_seas5",
    "mean_diff_exp",
    sizecol="total_affected",
    labels={
        "x": f"Forecasted mean daily rainfall, issued {issued_mo_str} (mm) [SEAS5]",
        "y": "Average adjusted flood exposure during year [Floodscan]",
        "title": f"Exposure vs. forecasted rainfall comparison ({valid_mo_str})",
    },
)

current_val = df_seas5_yearly.set_index("valid_date").loc[2025]["mean"]

ax.axvline(
    current_val,
    color="mediumorchid",
    linestyle="--",
)
ax.annotate(
    "2025 forecast",
    (current_val, df_compare["mean_diff_exp"].max()),
    rotation=90,
    va="top",
    ha="right",
    color="mediumorchid",
)
```

```python
fig, ax = plot_comparison(
    df_compare,
    "mean_seas5",
    "mean_era5",
)
```

```python
fig, ax = plot_comparison(
    df_compare,
    "mean_seas5_detrended",
    "mean_era5_detrended",
)
```

```python

```
