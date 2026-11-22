"""Step 1 - Ingest the raw ASIC IDR workbook and the AFCA Datacube extract into DuckDB.

* Reads every sheet of the ASIC IDR file as text (so nothing is silently coerced),
  then casts counts to integers, '98.33%' strings to fractions, and money to floats.
* Writes typed tables to data/processed/spf.duckdb and records a SHA-256 checksum and
  row count for each source in data/processed/provenance.json.

Run:  python src/01_ingest.py
"""
import hashlib
import json
import re
from datetime import datetime, timezone

import duckdb
import pandas as pd

from config import AFCA_CSV, DB, IDR_XLSX, PROCESSED

SHEETS = {
    "Firm-level Metrics": "idr_firm",
    "Product Dimension": "idr_product",
    "Issue Dimension": "idr_issue",
    "Outcome Dimension": "idr_outcome",
    "Product & Issue Relationship": "idr_product_issue",
    "Product & Outcome Relationship": "idr_product_outcome",
    "Issue & Outcome Relationship": "idr_issue_outcome",
}


def snake(col: str) -> str:
    col = col.strip().lower().replace("%", "pct").replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "_", col).strip("_")


def pct_to_frac(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.str.rstrip("%"), errors="coerce") / 100


def type_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: snake(c) for c in df.columns})
    for c in df.columns:
        if c.startswith("pct_"):
            df[c] = pct_to_frac(df[c])
        elif c in {"complaint_count", "count_of_closed_complaints"}:
            df[c] = pd.to_numeric(df[c], errors="raise").astype("Int64")
        elif c in {"median_time_taken", "average_monetary_remedy", "median_monetary_remedy"}:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.rename(columns={"calendar_half_year": "half"})
    return df


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))
    prov = {"built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "sources": {}}

    raw = pd.read_excel(IDR_XLSX, sheet_name=list(SHEETS), dtype=str)
    for sheet, table in SHEETS.items():
        df = type_frame(raw[sheet])
        con.register("df", df)
        con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM df")
        con.unregister("df")
        print(f"{table:22s} {len(df):>8,} rows  {df['half'].nunique()} half-years")
        prov["sources"][table] = {"file": IDR_XLSX.name, "sheet": sheet, "rows": len(df)}
    prov["sources"]["idr_file_sha256"] = sha256(IDR_XLSX)

    afca = pd.read_csv(AFCA_CSV)
    con.register("afca", afca)
    con.execute("CREATE OR REPLACE TABLE afca_banks AS SELECT * FROM afca")
    prov["sources"]["afca_banks"] = {"file": AFCA_CSV.name, "rows": len(afca),
                                     "sha256": sha256(AFCA_CSV),
                                     "method": "Transcribed from AFCA Datacube 'Compare firms' table, "
                                               "Primary business = Bank, FY2025 and FY2026"}
    print(f"{'afca_banks':22s} {len(afca):>8,} rows")

    (PROCESSED / "provenance.json").write_text(json.dumps(prov, indent=2))
    con.close()


if __name__ == "__main__":
    main()
