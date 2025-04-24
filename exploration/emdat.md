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

# EMDAT
<!-- markdownlint-disable MD013 -->

```python
%load_ext jupyter_black
%load_ext autoreload
%autoreload 2
```

```python
import ocha_stratus as stratus

from src.constants import *
```

```python
blob_name = f"{PROJECT_PREFIX}/raw/emdat/emdat_ssd_flooding_2025-04-17.csv"
```

```python
df = stratus.load_csv_from_blob(blob_name)
```

```python
df.dtypes
```

```python
df["Start Month"]
```

All start months seem to be late enough that flooding corresponds to current year as opposed to previous year.

```python
df.groupby("Start Year")["Total Affected"].sum().plot(kind="bar")
```
