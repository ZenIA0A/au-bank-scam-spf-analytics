"""Helpers: open the DuckDB database with the bank mapping tables and SQL views loaded."""
import duckdb
import pandas as pd

from config import BANKS, DB, ROOT


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(DB), read_only=read_only)
    if not read_only:
        bank_map = pd.DataFrame([{"firm_name": k, "short": v["short"], "tier": v["tier"]}
                                 for k, v in BANKS.items()])
        afca_map = pd.DataFrame([{"short": v["short"], "afca_name": a}
                                 for v in BANKS.values() for a in v["afca"]])
        con.register("bm", bank_map)
        con.register("am", afca_map)
        con.execute("CREATE OR REPLACE TABLE bank_map AS SELECT * FROM bm")
        con.execute("CREATE OR REPLACE TABLE bank_afca_map AS SELECT * FROM am")
        con.execute((ROOT / "sql" / "views.sql").read_text())
    return con


def q(con, sql: str) -> pd.DataFrame:
    return con.execute(sql).df()
