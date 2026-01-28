# CFTC COT Downloader + Notes Scraper (`cftc_cot.py`)

A robust Python module for **downloading official CFTC Commitments of Traders (COT) report archives** and scraping the official **CFTC Explanatory Notes**.

This project is focused on **data acquisition and persistence only**.
No indicators, no signals, no analysis logic.

---

## Purpose

`cftc_cot.py` provides a reliable way to:

* Download **year-based** COT ZIP archives from CFTC servers
* Download **historical bundle ZIPs** (e.g. 2006–2016) where available
* Read the primary data file **directly from ZIPs in memory**
* Optionally cache raw ZIP files locally
* Scrape official **CFTC Explanatory Notes** for reference and documentation

Designed for **ETL pipelines, research backends, and data archiving workflows**.

---

## Key Design Principles

* ✅ No hard-coded filenames per year
* ✅ Works directly with official CFTC ZIP archives
* ✅ In-memory ZIP reading (no extraction clutter)
* ✅ Minimal transformation — source-of-truth data
* ✅ Explicit, predictable behavior

---

## Features

### Download COT data by year

* Downloads a single year for a selected report type
* Automatically identifies the main `.txt` / `.csv` file inside the ZIP
* Returns a `pandas.DataFrame`

### Download historical bundle archives

* Supports older multi-year ZIPs (e.g. 2006–2016) when available
* Same in-memory read behavior

### Download a year range

* Fetches multiple years and concatenates them into a single `DataFrame`

### Scrape official CFTC explanatory notes

* Scrapes definitions and explanations directly from `cftc.gov`
* Defensive parsing to handle page structure changes

---

### 📄 Report Naming & Archive Mapping

The CFTC uses **multiple filename conventions** across report types and historical periods.

All report-to-filename logic used by this project is documented in:

➡ **[`REPORT_SPECS.md`](./REPORT_SPECS.md)**

This file explains:

* Why different report types use different ZIP prefixes
* How year-based and bundled archives are constructed
* Which historical bundle files exist (e.g. 2006–2016)
* How the downloader selects the correct file inside each ZIP

If the CFTC changes naming conventions in the future, updates should be made **only in `REPORT_SPECS.md`**.

---
## Project Structure

```
cot/
│
├─ cftc_cot.py
├─ dataset/
│   ├─ fut_fin_txt_2025.zip
│   └─ fut_fin_txt_2026.zip
├─ README.md
└─ .gitignore
```

---

## Installation

### Requirements

* Python 3.9+
* pandas
* requests
* beautifulsoup4

```bash
pip install pandas requests beautifulsoup4
```

---

## Supported COT Report Types

Use one of the following values for `cot_report_type`:

| Key                                   | Description                                      |
| ------------------------------------- | ------------------------------------------------ |
| `traders_in_financial_futures_fut`    | Traders in Financial Futures (TFF), Futures Only |
| `traders_in_financial_futures_futopt` | TFF, Futures + Options Combined                  |
| `disaggregated_fut`                   | Disaggregated, Futures Only                      |
| `disaggregated_futopt`                | Disaggregated, Futures + Options Combined        |
| `legacy_fut`                          | Legacy, Futures Only                             |
| `legacy_futopt`                       | Legacy, Futures + Options Combined               |
| `supplemental_futopt`                 | Commodity Index Trader (CIT) Supplement          |

---

## Quick Start

### Download one year

```python
from cftc_cot import cot_download_year

df = cot_download_year(
    year=2026,
    cot_report_type="disaggregated_fut",
    store_zip=True,
    path="./dataset",
)

print(df.shape)
print(df.columns)
```

---

### Download a year range

```python
from cftc_cot import cot_download_year_range

df = cot_download_year_range(
    start_year=2024,
    end_year=2026,
    cot_report_type="traders_in_financial_futures_fut",
    store_zip=True,
    path="./dataset",
)
```

---

### Download a historical bundle (if available)

```python
from cftc_cot import cot_download_bundle

df_old = cot_download_bundle(
    cot_report_type="traders_in_financial_futures_fut",
    store_zip=True,
    path="./dataset",
)
```

---

### Scrape CFTC explanatory notes

```python
from cftc_cot import cot_explanatory_notes

notes = cot_explanatory_notes()
print(notes.head())
```

---

## ZIP Handling (Important)

* ZIP files are **downloaded into memory**
* The main data file is read **directly from the ZIP**
* No files are extracted unless explicitly requested
* If `store_zip=True`, ZIPs are cached locally

This avoids:

* filesystem clutter
* fragile filename assumptions
* unnecessary disk I/O

---

## Typical Usage Example

```python
df = cot_download_year_range(2018, 2026, "traders_in_financial_futures_fut")

df["Report_Date_as_YYYY-MM-DD"] = pd.to_datetime(
    df["Report_Date_as_YYYY-MM-DD"], errors="coerce"
)

nasdaq = df[
    df["Market_and_Exchange_Names"].str.contains("NASDAQ", case=False, na=False)
]
```

---

## Error Handling

### Unknown report type

```text
ValueError: Unknown cot_report_type
```

Use one of the supported report keys listed above.

---

### No data file found in ZIP

```text
ValueError: No .txt/.csv found in zip
```

Indicates a ZIP structure change or a corrupted download.

---

### HTTP errors

Possible causes:

* Year not published yet
* Temporary CFTC outage
* Rate limiting

Mitigation:

* Retry later
* Cache ZIPs locally
* Avoid rapid repeated calls

---

## Non-Goals

* ❌ No data normalization
* ❌ No positioning calculations
* ❌ No indicators or trading signals
* ❌ No opinionated transformations

This module is intentionally **infrastructure-only**.

---

## Disclaimer

This project downloads publicly available data from the CFTC website.
It provides convenience utilities only and does **not** provide trading advice.
Use at your own risk.

---
