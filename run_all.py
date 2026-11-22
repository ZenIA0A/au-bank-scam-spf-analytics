"""Rebuild everything from the raw files: python run_all.py"""
import runpy
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
sys.path.insert(0, str(SRC))
for step in ["00_download", "01_ingest", "02_quality_checks", "03_analysis", "04_spf_model", "05_prioritisation"]:
    print(f"\n=== {step} ===")
    try:
        runpy.run_path(str(SRC / f"{step}.py"), run_name="__main__")
    except SystemExit as e:
        if e.code:
            sys.exit(f"{step} failed (exit {e.code})")
print("\nDone. Tables in reports/tables, charts in reports/figures.")
