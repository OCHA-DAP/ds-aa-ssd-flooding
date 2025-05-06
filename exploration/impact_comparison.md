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
import statsmodels.api as sm

from src.constants import *
from src.datasources import era5, seas5
from src.utils.timeseries import detrend_column
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
adm_name
```

## Load data

### Exposure

```python
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
df_exp_yearly["max_prev"] = df_exp_yearly["max"].shift()
df_exp_yearly["mean_prev"] = df_exp_yearly["mean"].shift()
```

```python
window = 3
df_exp_yearly[f"mean_roll{window}"] = (
    df_exp_yearly["mean"].rolling(window).mean()
)
df_exp_yearly[f"max_diff_mean_roll{window}"] = (
    df_exp_yearly["max"] / df_exp_yearly[f"mean_roll{window}"]
)
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
issued_month = 5
issued_mo_str = calendar.month_abbr[issued_month]
df_seas5_imo = df_seas5_all[
    df_seas5_all["issued_date"].dt.month == issued_month
]
```

```python
valid_months_override = [7, 8, 9]
df_seas5_imo = df_seas5_imo[
    df_seas5_imo["valid_date"].dt.month.isin(valid_months_override)
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
df_seas5_yearly = detrend_column(df_seas5_yearly, col="mean", max_index=2024)
# df_seas5_yearly = detrend_column(
#     df_seas5_yearly, col="mean", min_index=2000, max_index=2024
# )
```

```python
ax = df_seas5_yearly.set_index("valid_date").plot()
ax.set_title("seas5")
```

```python
df_seas5_yearly
```

```python
df_seas5_monthwise = df_seas5_imo.copy()
df_seas5_monthwise["valid_month"] = df_seas5_monthwise["valid_date"].dt.month
df_seas5_monthwise["valid_year"] = df_seas5_monthwise["valid_date"].dt.year
df_seas5_monthwise = df_seas5_monthwise.pivot(
    index="valid_year", columns="valid_month", values="mean"
)
df_seas5_monthwise = df_seas5_monthwise.rename(
    columns={x: f"mean_seas5_mo{x}" for x in df_seas5_monthwise.columns}
).reset_index()
df_seas5_monthwise
```

### ERA5

Load and filter ERA5 data to same `valid_months` as SEAS5.

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
# df_era5_yearly = detrend_column(df_era5_yearly, "mean", min_index=2000)
```

```python
ax = df_era5_yearly.set_index("valid_date").plot()
ax.set_title("era5")
```

```python
df_era5_yearly
```

#### Month-wise

```python
df_era5
```

```python
[x for x in df_era5_monthwise]
```

```python
df_era5_monthwise = df_era5[df_era5["valid_date"].dt.year < 2025].copy()
df_era5_monthwise["valid_month"] = df_era5_monthwise["valid_date"].dt.month
df_era5_monthwise["valid_year"] = df_era5_monthwise["valid_date"].dt.year
df_era5_monthwise = df_era5_monthwise.pivot(
    index="valid_year", columns="valid_month", values="mean"
)
df_era5_monthwise = df_era5_monthwise.rename(
    columns={x: f"mean_era5_mo{x}" for x in df_era5_monthwise.columns}
).reset_index()
for col in df_era5_monthwise:
    if col == "valid_year":
        continue
    df_era5_monthwise = detrend_column(
        df_era5_monthwise, col, index_col="valid_year"
    )
```

```python
df_era5_monthwise.merge(
    df_exp_yearly.rename(columns={"valid_date": "valid_year"})
).corr()["mean_diff_exp"][
    [x for x in df_era5_monthwise if "detrended" in x]
].plot(
    kind="bar"
)
```

```python
df_era5_monthwise.set_index("valid_year").shift().reset_index().merge(
    df_exp_yearly.rename(columns={"valid_date": "valid_year"})
).corr()["mean_diff_exp"][
    [x for x in df_era5_monthwise if "detrended" in x]
].plot(
    kind="bar"
)
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
# Ensure Start Year is the index
df_emdat_yearly = df_emdat_yearly.set_index("Start Year")

# Reindex to fill in all years 2000–2024
df_emdat_yearly = df_emdat_yearly.reindex(range(2000, 2025), fill_value=0)

# Reset index if you want to plot with "Start Year" as a column
df_emdat_yearly = df_emdat_yearly.reset_index().rename(
    columns={"index": "Start Year"}
)
df_emdat_yearly["Total Affected"] = df_emdat_yearly["Total Affected"].astype(
    int
)
```

```python
df_emdat_yearly
```

```python
df_emdat_yearly.plot(x="Start Year", y="Total Affected", kind="bar")
```

```python
df_emdat_yearly
```

```python
df_era5_monthwise.merge(
    df_emdat_yearly.rename(columns={"Start Year": "valid_year"})
).corr()["Total Affected"][
    [x for x in df_era5_monthwise if "detrended" in x]
].plot(
    kind="bar"
)
```

```python
df_era5_monthwise.set_index("valid_year").shift().reset_index().merge(
    df_emdat_yearly.rename(columns={"Start Year": "valid_year"})
).corr()["Total Affected"][
    [x for x in df_era5_monthwise if "detrended" in x]
].plot(
    kind="bar"
)
```

## Combine

```python
df_compare_full = (
    df_exp_yearly.merge(
        df_era5_yearly.rename(
            columns={
                "mean": "mean_era5",
                "mean_detrended": "mean_era5_detrended",
            }
        ),
        how="outer",
    )
    .merge(
        df_seas5_yearly,
        how="outer",
    )
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
        how="outer",
    )
).rename(columns={"valid_date": "year"})
df_compare_full["cerf"] = df_compare_full["year"].isin(CERF_YEARS)
df_compare = df_compare_full[
    (df_compare_full["year"] < 2025) & (df_compare_full["year"] >= 2000)
].copy()
df_compare
```

```python
df_compare_full
```

## Analysis

### Correlations

```python
df_compare.set_index("year").corr()
```

```python
df_compare_full.set_index("year").corr()[
    [x for x in df_compare_full.columns if "5" in x]
]
```

```python
df_compare.set_index("year").corr()[
    [x for x in df_compare_full.columns if "5" in x]
]
```

```python
# quick F1 comparison between raw and detrended
dicts = []
df_compare_metrics = df_compare_full.copy()

for rp in [2, 3, 5, 10]:
    for trend in ["", "_detrended"]:
        for col in [f"mean_seas5{trend}", f"mean_era5{trend}"]:
            df_compare_metrics[f"{col}_bool"] = df_compare_metrics[
                col
            ] >= df_compare_metrics[col].quantile(1 - 1 / rp)
        p = df_compare_metrics[f"mean_seas5{trend}_bool"].sum()
        pp = df_compare_metrics[f"mean_era5{trend}_bool"].sum()
        tp = (
            df_compare_metrics[
                [f"mean_era5{trend}_bool", f"mean_seas5{trend}_bool"]
            ]
            .all(axis=1)
            .sum()
        )
        tpr = tp / p
        dicts.append(
            {
                "rp": rp,
                "tpr": tpr,
                "trend": "raw" if trend == "" else "detrended",
            }
        )

df_plot_metrics = pd.DataFrame(dicts)
ax = df_plot_metrics.pivot(index="rp", columns="trend", values="tpr")[
    ["raw", "detrended"]
].plot()
ax.set_ylim(0, 1)
ax.set_ylabel("TPR/PPV/F1")
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

### Plotting

```python
def plot_comparison(df, xcol, ycol, sizecol=None, labels=None, rotation=0):
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
            rotation=rotation,
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
plot_comparison(
    df_compare,
    "max_diff_mean_roll3_exp",
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
    df_compare_full,
    "mean_seas5",
    "mean_era5",
)

current_pred = df_compare_full.set_index("year").loc[2025, "mean_seas5"]
ax.axvline(
    current_pred,
    color="mediumorchid",
    linestyle="--",
)
```

```python
fig, ax = plot_comparison(
    df_compare_full,
    "mean_seas5_detrended",
    "mean_era5_detrended",
)

current_pred = df_compare_full.set_index("year").loc[
    2025, "mean_seas5_detrended"
]
ax.axvline(
    current_pred,
    color="mediumorchid",
    linestyle="--",
)
```

```python
fig, ax = plot_comparison(
    df_compare,
    "mean_seas5_detrended",
    "mean_era5_detrended",
    sizecol="total_affected",
)

current_pred = df_compare_full.set_index("year").loc[
    2025, "mean_seas5_detrended"
]
ax.axvline(
    current_pred,
    color="mediumorchid",
    linestyle="--",
)
ax.annotate(
    "2025 forecast",
    (current_pred, df_compare["mean_era5_detrended"].min()),
    rotation=90,
    va="bottom",
    ha="right",
    color="mediumorchid",
)

ax.set_title(
    f"Detrended observations vs. forecast ({adm_name}, {valid_mo_str})"
)
ax.set_ylabel(f"Observed mean daily rainfall, detrended (mm) [ERA5]")
ax.set_xlabel(
    f"Forecasted mean daily rainfall, detrended, issued {issued_mo_str} (mm) [SEAS5]"
)
```

## Modeling

```python
df_modeling = df_compare_full.copy()
# df_modeling = df_modeling[
#     (df_modeling["year"] >= 2006) & (df_modeling["year"] < 2025)
# ]
df_modeling["year_dummy"] = (df_modeling["year"] >= 2019).astype(int)
```

```python
df_modeling.loc[df_modeling["year"] == 2025, "mean_diff_exp"] = np.nan
```

```python
# Select inputs and output
input_cols = ["year_dummy", "mean_seas5"]
# input_cols = ["min_exp", "mean_seas5"]
output_col = "total_affected"
X = df_modeling[input_cols]
y = df_modeling[output_col]

# Drop rows with missing values
df_clean = pd.concat([X, y], axis=1).dropna()
X = df_clean[input_cols]
y = df_clean[output_col]

# Add constant for intercept
X = sm.add_constant(X)

# Fit linear regression model
model = sm.OLS(y, X).fit()

# Show summary
print(model.summary())

df_modeling["reg_pred"] = model.predict(
    sm.add_constant(df_modeling[input_cols])
)
```

```python
df_modeling.corr()["total_affected"].plot(kind="bar")
```

```python
ycol = output_col
xcol = "reg_pred"
fig, ax = plot_comparison(
    df_modeling,
    xcol,
    ycol,
    rotation=45,
)
current_pred = df_modeling.set_index("year").loc[2025, xcol]
ax.axvline(
    current_pred,
    color="mediumorchid",
    linestyle="--",
)
ax.annotate(
    "2025 prediction",
    (current_pred, 0.5e6),
    rotation=90,
    va="top",
    ha="right",
    color="mediumorchid",
)
ax.axvline(0, color="grey", linewidth=0.5, linestyle="--")
ax.axhline(0, color="grey", linewidth=0.5, linestyle="--")
ax.plot([-2e6, 2e6], [-2e6, 2e6], color="grey", linewidth=1, linestyle="--")
ax.annotate(
    "45°",
    (1.5e6, 1.5e6),
    color="grey",
    rotation=45,
    fontstyle="italic",
    va="bottom",
    ha="left",
)
ax.set_ylim([-0.2e6, 1.5e6])
ax.set_xlim([-0.2e6, 1.5e6])

ax.set_ylabel("Actual total affected [EM-DAT]")
ax.set_xlabel("Predicted total affected [regression model]")

ax.set_title("Regression model impact predictions\n")
ax.text(
    0.5,
    1.04,
    # "Variables: Apr SEAS5 forecast, ≥2019 dummy",
    "Variables: Apr SEAS5 forecast, min. exposure during year",
    transform=ax.transAxes,
    ha="center",
    va="top",
)
```

```python

```
