from typing import List, Literal

import pandas as pd

from src.utils import blob_utils, db_utils


def load_seas5(pcode: str = "SS"):
    engine = db_utils.get_engine("prod")
    query = f"SELECT * FROM public.seas5 WHERE pcode = '{pcode}' "
    df = pd.read_sql(query, engine, parse_dates=["valid_date", "issued_date"])
    return df


def load_seas5_multiple_pcodes(pcodes: List[str]):
    engine = db_utils.get_engine("prod")
    query = f"SELECT * FROM public.seas5 WHERE pcode IN {tuple(pcodes)} "
    df = pd.read_sql(query, engine, parse_dates=["valid_date", "issued_date"])
    return df


def load_seas5_raster(
    issued_date: str, lt: int, stage: Literal["dev", "prod"] = "prod"
):
    blob_name = f"seas5/monthly/processed/precip_em_i{issued_date}_lt{lt}.tif"
    return blob_utils.open_blob_cog(
        blob_name=blob_name, stage=stage, container_name="raster"
    )
