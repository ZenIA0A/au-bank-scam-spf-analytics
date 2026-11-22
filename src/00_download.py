"""Step 0 - Download the two public source files (run once).

The ASIC IDR workbook (62 MB) is not stored in git; this script fetches it and the NASC
report. The AFCA Datacube has no export, so its FY2025-26 bank table is kept in
data/raw/afca_datacube_banks.csv (transcribed on 22 Nov 2026).

Run:  python src/00_download.py
"""
import urllib.request

from config import IDR_XLSX, RAW, TSR_PDF

FILES = {
    IDR_XLSX: "https://download.asic.gov.au/files/idr/idr_data_file_20261116.xlsx",
    TSR_PDF: "https://www.scamwatch.gov.au/system/files/targeting-scams-report-2025.pdf",
}

RAW.mkdir(parents=True, exist_ok=True)
for path, url in FILES.items():
    if path.exists():
        print(f"exists  {path.name}")
        continue
    print(f"fetch   {url}")
    urllib.request.urlretrieve(url, path)
    print(f"saved   {path.name} ({path.stat().st_size/1e6:.1f} MB)")
