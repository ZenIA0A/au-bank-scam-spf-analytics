"""Shared configuration: paths, source provenance and the bank peer group.

Every number used in the analysis comes either from a file in data/raw/ or from a
published figure recorded in SOURCES below (with its URL), so each output can be
traced back to where it came from.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
OUT = ROOT / "reports" / "tables"
DB = PROCESSED / "spf.duckdb"

IDR_XLSX = RAW / "idr_data_file_20261116.xlsx"
AFCA_CSV = RAW / "afca_datacube_banks.csv"
TSR_PDF = RAW / "targeting-scams-report-2025.pdf"

HALVES = ["2023 HY2", "2024 HY1", "2024 HY2", "2025 HY1", "2025 HY2", "2026 HY1"]
# Calendar half-years that make up each Australian financial year
FY_HALVES = {"FY2024": ["2023 HY2", "2024 HY1"],
             "FY2025": ["2024 HY2", "2025 HY1"],
             "FY2026": ["2025 HY2", "2026 HY1"]}

# Bank peer group. Keys are the licensee names as they appear in the ASIC IDR file.
# 'afca' lists the AFCA Datacube member names that sit under the same licence,
# because AFCA reports some divisions separately while ASIC IDR does not
# (for example St George, Bank of Melbourne and BankSA are divisions of Westpac).
BANKS = {
    "COMMONWEALTH BANK OF AUSTRALIA": {"short": "CBA", "tier": "Major bank",
        "afca": ["Commonwealth Bank of Australia", "Bank of Western Australia Limited"]},
    "WESTPAC BANKING CORPORATION": {"short": "Westpac", "tier": "Major bank",
        "afca": ["Westpac Banking Corporation", "St George Bank", "Bank of Melbourne",
                 "BankSA (a division of Westpac Banking Corporation)"]},
    "NATIONAL AUSTRALIA BANK LIMITED": {"short": "NAB", "tier": "Major bank",
        "afca": ["National Australia Bank Limited"]},
    "AUSTRALIA AND NEW ZEALAND BANKING GROUP LIMITED": {"short": "ANZ", "tier": "Major bank",
        "afca": ["Australia and New Zealand Banking Group Limited"]},
    "MACQUARIE BANK LIMITED": {"short": "Macquarie", "tier": "Other bank",
        "afca": ["Macquarie Bank Limited"]},
    "ING BANK (AUSTRALIA) LIMITED": {"short": "ING", "tier": "Other bank",
        "afca": ["ING Bank (Australia) Limited"]},
    "BANK OF QUEENSLAND LIMITED": {"short": "BOQ", "tier": "Other bank",
        "afca": ["Bank of Queensland Limited"]},
    "BENDIGO AND ADELAIDE BANK LIMITED": {"short": "Bendigo", "tier": "Other bank",
        "afca": ["Bendigo and Adelaide Bank Limited"]},
    "HSBC BANK AUSTRALIA LIMITED": {"short": "HSBC", "tier": "Other bank",
        "afca": ["HSBC Bank Australia Limited"]},
    "NORFINA LIMITED": {"short": "Norfina (ex-Suncorp Bank)", "tier": "Other bank",
        "afca": ["Norfina Limited"]},
    "AMP BANK LIMITED": {"short": "AMP Bank", "tier": "Other bank",
        "afca": ["AMP Bank Limited"]},
    "BANK AUSTRALIA LIMITED": {"short": "Bank Australia", "tier": "Other bank",
        "afca": ["Bank Australia Limited"]},
    "REVOLUT PAYMENTS AUSTRALIA PTY LTD": {"short": "Revolut", "tier": "Digital/neo",
        "afca": ["Revolut Payments Australia Pty Ltd"]},
}
MAJORS = [k for k, v in BANKS.items() if v["tier"] == "Major bank"]

SCAM_CATEGORY = "Scams/fraud"
SCAM_VICTIM_ISSUE = "Victim of scam"

# Published figures used as model inputs (all quoted from the source named).
SOURCES = {
    "tsr_2025": "NASC, Targeting Scams Report 2025 - https://www.scamwatch.gov.au/system/files/targeting-scams-report-2025.pdf",
    "asic_idr": "ASIC IDR data file (published 16 Nov 2026) - https://download.asic.gov.au/files/idr/idr_data_file_20261116.xlsx",
    "afca_datacube": "AFCA Datacube, Compare firms, Primary business = Bank, accessed 22 Nov 2026 - https://data.afca.org.au/compare-firms/",
    "afca_fees": "AFCA Complaint Fee Guide - https://afca.org.au/media/1875/download",
    "spf_asic": "ASIC, Scams Prevention Framework - https://www.asic.gov.au/regulatory-resources/scams/scams-prevention-framework",
    "spf_idr_paper": "Treasury IDR Position Paper (May 2026), summarised by Ashurst / Clayton Utz / Corrs",
}

# Targeting Scams Report 2025 figures (Tables 1-3 and Appendix 1)
TSR = {
    "combined_loss_by_year": {2021: 1.8e9, 2022: 3.1e9, 2023: 2.7e9, 2024: 2.03e9, 2025: 2.18e9},
    "afcx_2025": {"reports": 202_943, "reports_with_loss": 199_666, "loss": 842.3e6},
    "afcx_2024": {"reports": 169_184, "reports_with_loss": 163_860, "loss": 812.3e6},
    "scamwatch_2025": {"reports": 200_675, "reports_with_loss": 28_202, "loss": 334.8e6, "median_loss": 400},
    "scamwatch_2024": {"reports": 249_448, "reports_with_loss": 22_408, "loss": 318.8e6, "median_loss": 500},
    "combined_loss_by_type_2025": {"Investment": 837.7e6, "Payment redirection": 166.8e6,
        "Romance": 139.9e6, "Phishing": 97.6e6, "Remote access": 69.9e6, "Other": 872.1e6},
    "combined_loss_by_type_2024": {"Investment": 945.0e6, "Payment redirection": 152.6e6,
        "Romance": 156.8e6, "Phishing": 84.5e6, "Remote access": 106.0e6, "Other": 582.3e6},
    "scamwatch_contact_loss_2025": {"Online": 158_504_957, "Phone call": 72_477_723, "Email": 57_877_574,
        "In person": 25_255_402, "Text message": 17_977_491, "Mail": 2_738_406},
    "scamwatch_contact_reports_with_loss_2025": {"Online": 19_169, "Email": 4_329, "Phone call": 2_012,
        "Text message": 1_603, "In person": 870, "Mail": 218},
    "scamwatch_payment_loss_2025": {"Cryptocurrency/DCE": 121.3e6, "Bank transfer": 118.1e6,
        "Cash": 10.0e6, "Credit card": 9.1e6, "Other gift card": 5.8e6},
    "scamwatch_65plus_2025": {"loss": 88.8e6, "share_of_loss": 0.265, "share_of_population": 0.172, "median_loss": 716},
}

# AFCA complaint fees (ex GST), FY2024-25 schedule from the AFCA Complaint Fee Guide.
# AFCA applied a 3.5% increase from 1 July 2025, so the model multiplies these by AFCA_FY26_UPLIFT.
AFCA_FY26_UPLIFT = 1.035
AFCA_FEES = {"registration_referral": 96.19, "case_mgmt_fast_track": 1141.48,
             "case_mgmt_standard": 2238.07, "decision": 9304.0}
