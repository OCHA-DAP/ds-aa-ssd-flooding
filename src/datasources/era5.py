from typing import List

import pandas as pd

from src.utils import db_utils


def load_era5(pcode: str = "SS"):
    engine = db_utils.get_engine("prod")
    query = f"SELECT * FROM public.era5 WHERE pcode = '{pcode}' "
    df = pd.read_sql(query, engine, parse_dates=["valid_date"])
    return df


def load_era5_multiple_pcodes(pcodes: List[str]):
    engine = db_utils.get_engine("prod")
    query = f"SELECT * FROM public.era5 WHERE pcode IN {tuple(pcodes)} "
    df = pd.read_sql(query, engine, parse_dates=["valid_date"])
    return df
