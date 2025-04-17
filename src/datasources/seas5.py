from typing import List, Literal

import pandas as pd

from src.utils import blob_utils, db_utils


def load_seas5(pcode: str = "SS"):
    engine = db_utils.get_engine("prod")
    query = "SELECT * FROM public.seas5 WHERE pcode = :pcode"
    df = pd.read_sql(
        query,
        engine,
        params={"pcode": pcode},
        parse_dates=["valid_date", "issued_date"],
    )
    return df


def load_seas5_multiple_pcodes(pcodes: List[str]):
    engine = db_utils.get_engine("prod")

    # Build the SQL query with the correct number of placeholders
    placeholders = ", ".join(["%s"] * len(pcodes))
    query = f"SELECT * FROM public.seas5 WHERE pcode IN ({placeholders})"

    # Wrap pcodes in a tuple, which is what's expected for positional arguments
    with engine.connect() as conn:
        df = pd.read_sql(
            query,
            conn,
            params=tuple(pcodes),
            parse_dates=["valid_date", "issued_date"],
        )

    return df


def load_seas5_raster(
    issued_date: str, lt: int, stage: Literal["dev", "prod"] = "prod"
):
    blob_name = f"seas5/monthly/processed/precip_em_i{issued_date}_lt{lt}.tif"
    return blob_utils.open_blob_cog(
        blob_name=blob_name, stage=stage, container_name="raster"
    )
