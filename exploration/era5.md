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

# ERA5

Exploring ERA5 data

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
from src.datasources import era5
```

```python
pcode = "SS"
```

```python
df_era5 = era5.load_era5(pcode=pcode)
```

```python
df_era5.dtypes
```

```python
df_era5[df_era5["valid_date"].dt.year < 2025].groupby(
    df_era5["valid_date"].dt.month
)["mean"].mean().plot(kind="bar")
```

```python
df_era5[
    (df_era5["valid_date"].dt.year < 2025)
    & (df_era5["valid_date"].dt.month.isin([7, 8, 9]))
].groupby(df_era5["valid_date"].dt.year)["mean"].mean().plot(kind="bar")
```

```python

```
