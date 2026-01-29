"""
cftc_cot.py — robust CFTC COT downloader + explanatory-note scraper

Sources:
- Historical Compressed (report zips and naming): https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm
- COT landing page (report notes + methodology): https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
"""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Union

import pandas as pd
import requests
from bs4 import BeautifulSoup


# -----------------------------
# Configuration / Mappings
# -----------------------------

CFTC_DEA_HISTORY_BASE = "https://www.cftc.gov/files/dea/history/"

@dataclass(frozen=True)
class ReportSpec:
    """
    Defines how to build the zip filename for a given report type.

    NOTE:
    The CFTC has multiple historical naming schemes. The reliable approach:
    - For year-based downloads: use the 'dea/history/<prefix><year>.zip' pattern.
    - For bundled archives like '2006-2016 (Text)': use the known historical bundle zips.
    """
    # Year-based zip prefix, e.g. "fut_fin_txt_" -> fut_fin_txt_2026.zip
    year_zip_prefix: str
    # Optional bundle zip filename for older "2006-2016 (Text)" packages
    bundle_zip_filename: Optional[str] = None


REPORT_SPECS = {
    # Traders in Financial Futures (TFF)
    "traders_in_financial_futures_fut": ReportSpec(
        year_zip_prefix="fut_fin_txt_",
        bundle_zip_filename="fin_fut_txt_2006_2016.zip",
    ),
    "traders_in_financial_futures_futopt": ReportSpec(
        year_zip_prefix="com_fin_txt_",
        bundle_zip_filename="fin_com_txt_2006_2016.zip",
    ),

    # Disaggregated
    "disaggregated_fut": ReportSpec(
        year_zip_prefix="fut_disagg_txt_",
        bundle_zip_filename="fut_disagg_txt_hist_2006_2016.zip",
    ),
    "disaggregated_futopt": ReportSpec(
        year_zip_prefix="com_disagg_txt_",
        bundle_zip_filename="com_disagg_txt_hist_2006_2016.zip",
    ),

    # Legacy & Supplemental (Legacy naming differs; still accessible by year in practice)
    "legacy_fut": ReportSpec(
        year_zip_prefix="deacot",
        bundle_zip_filename="deacot1986_2016.zip",
    ),
    "legacy_futopt": ReportSpec(
        year_zip_prefix="deahistfo",
        bundle_zip_filename="deahistfo_1995_2016.zip",
    ),
    "supplemental_futopt": ReportSpec(
        year_zip_prefix="dea_cit_txt_",
        bundle_zip_filename="dea_cit_txt_2006_2016.zip",
    ),
}


# -----------------------------
# Helpers
# -----------------------------

def _ensure_dir(path: Union[str, Path]) -> Path:
    p = Path(path).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p

def _http_get_bytes(url: str, timeout: int = 60) -> bytes:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content

def _pick_data_file_from_zip(zf: zipfile.ZipFile) -> str:
    """
    Choose the best candidate file in the zip.
    Prefer .txt or .csv. Ignore readme/notes if present.
    """
    names = [n for n in zf.namelist() if not n.endswith("/")]
    # Prefer txt/csv
    candidates = [n for n in names if n.lower().endswith((".txt", ".csv"))]
    if not candidates:
        raise ValueError(f"No .txt/.csv found in zip. Files: {names[:20]}")
    # If multiple, choose the largest (usually the main dataset)
    def size(n):  # uncompressed size
        return zf.getinfo(n).file_size
    candidates.sort(key=size, reverse=True)
    return candidates[0]

def _read_cot_file_from_zip(zip_bytes: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        target = _pick_data_file_from_zip(zf)
        raw = zf.read(target)
    # Most CFTC files are comma-delimited (despite .txt)
    return pd.read_csv(io.BytesIO(raw), low_memory=False)

def _save_zip(zip_bytes: bytes, out_path: Path) -> None:
    out_path.write_bytes(zip_bytes)


# -----------------------------
# Public API
# -----------------------------

def cot_download_year(
    year: int,
    cot_report_type: str = "traders_in_financial_futures_fut",
    store_zip: bool = True,
    path: Union[str, Path] = "./dataset",
    timeout: int = 60,
) -> pd.DataFrame:
    """
    Download ONE YEAR of COT data for a given report type and return as DataFrame.

    This builds URLs like:
      https://www.cftc.gov/files/dea/history/<prefix><year>.zip

    Examples:
      - TFF futures-only 2026: fut_fin_txt_2026.zip
      - Disaggregated futures-only 2026: fut_disagg_txt_2026.zip

    The mapping is aligned with the CFTC "Historical Compressed" page listings.
    """
    if cot_report_type not in REPORT_SPECS:
        raise ValueError(f"Unknown cot_report_type '{cot_report_type}'. Valid: {sorted(REPORT_SPECS)}")

    spec = REPORT_SPECS[cot_report_type]
    zip_name = f"{spec.year_zip_prefix}{year}.zip"
    url = f"{CFTC_DEA_HISTORY_BASE}{zip_name}"

    out_dir = _ensure_dir(path)
    out_path = out_dir / zip_name

    current_year = datetime.now().year
    is_current_year = (year == current_year)

    if out_path.exists() and not is_current_year:
        zip_bytes = out_path.read_bytes()
    else:
        zip_bytes = _http_get_bytes(url, timeout=timeout)
        if store_zip:
            _save_zip(zip_bytes, out_path)

    return _read_cot_file_from_zip(zip_bytes)


def cot_download_bundle(
    cot_report_type: str = "traders_in_financial_futures_fut",
    store_zip: bool = True,
    path: Union[str, Path] = "./dataset",
    timeout: int = 60,
) -> pd.DataFrame:
    """
    Download the older bulk '2006-2016' style bundle (if available for that report type)
    and return as DataFrame.

    These bundle files are linked on the CFTC "Historical Compressed" page.
    """
    if cot_report_type not in REPORT_SPECS:
        raise ValueError(f"Unknown cot_report_type '{cot_report_type}'. Valid: {sorted(REPORT_SPECS)}")

    spec = REPORT_SPECS[cot_report_type]
    if not spec.bundle_zip_filename:
        raise ValueError(f"No bundle_zip_filename configured for report type '{cot_report_type}'")

    url = f"{CFTC_DEA_HISTORY_BASE}{spec.bundle_zip_filename}"

    out_dir = _ensure_dir(path)
    out_path = out_dir / spec.bundle_zip_filename

    if out_path.exists():
        zip_bytes = out_path.read_bytes()
    else:
        zip_bytes = _http_get_bytes(url, timeout=timeout)
        if store_zip:
            _save_zip(zip_bytes, out_path)

    return _read_cot_file_from_zip(zip_bytes)


def cot_download_year_range(
    start_year: int,
    end_year: int,
    cot_report_type: str = "traders_in_financial_futures_fut",
    store_zip: bool = True,
    path: Union[str, Path] = "./dataset",
    timeout: int = 60,
) -> pd.DataFrame:
    """
    Download a year range (inclusive) and return a concatenated DataFrame.
    """
    if start_year > end_year:
        raise ValueError("start_year must be <= end_year")

    frames = []
    for y in range(start_year, end_year + 1):
        frames.append(
            cot_download_year(
                year=y,
                cot_report_type=cot_report_type,
                store_zip=store_zip,
                path=path,
                timeout=timeout,
            )
        )
    return pd.concat(frames, ignore_index=True)


def cot_explanatory_notes() -> pd.DataFrame:
    """
    Scrape the CFTC COT "Explanatory Notes" page for key definitions.

    Returns a DataFrame with:
      - section: normalized topic key
      - title: section title
      - text: extracted explanation text

    Note: page structure can change; this function is defensive.
    """
    url = "https://www.cftc.gov/MarketReports/CommitmentsofTraders/ExplanatoryNotes/index.htm"
    html = _http_get_bytes(url, timeout=60)
    soup = BeautifulSoup(html, "html.parser")

    container = soup.find(class_="ckeditor-accordion")
    if not container:
        # Fallback: capture all text from main content area
        main = soup.find("main") or soup
        text = re.sub(r"\s+", " ", main.get_text(" ", strip=True))
        return pd.DataFrame([{
            "section": "full_page_fallback",
            "title": "Explanatory Notes (fallback)",
            "text": text
        }])

    # Collect dt/dd pairs
    rows = []
    for dt in container.find_all("dt"):
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue
        title = dt.get_text(" ", strip=True)
        text = dd.get_text(" ", strip=True)
        section = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        rows.append({"section": section, "title": title, "text": text})

    return pd.DataFrame(rows, columns=["section", "title", "text"])
