Perfect idea. This is exactly the kind of file that saves future-you (and users) a lot of pain.

Below is a **drop-in `REPORT_SPECS.md`** that matches your code **line-by-line**, explains *why* the mappings exist, and documents CFTC quirks without opinion or speculation.

You can paste this directly into `REPORT_SPECS.md`.

---

# REPORT_SPECS.md

### CFTC COT Report Filename & Archive Mapping

This document explains how **CFTC Commitments of Traders (COT)** report types map to their corresponding **historical ZIP archive filenames** and why these mappings are required.

The CFTC uses **multiple naming conventions** across report types and time periods.
`cftc_cot.py` abstracts this complexity through the `REPORT_SPECS` configuration.

---

## Why `REPORT_SPECS` Exists

The CFTC does **not** expose a single, uniform API or filename scheme for historical COT data.

Key challenges:

* Different report families use **different filename prefixes**
* Some reports are published **per year**, others as **multi-year bundles**
* Naming conventions change across time
* File extensions are inconsistent (`.txt` files are often CSV-formatted)

`REPORT_SPECS` defines a **single source of truth** for building valid download URLs.

---

## Base URL Used

All historical archives are downloaded from:

```
https://www.cftc.gov/files/dea/history/
```

ZIP filenames are appended to this base path.

---

## ReportSpec Structure

Each report type is defined by a `ReportSpec`:

```python
@dataclass(frozen=True)
class ReportSpec:
    year_zip_prefix: str
    bundle_zip_filename: Optional[str] = None
```

### Fields

| Field                 | Description                                          |
| --------------------- | ---------------------------------------------------- |
| `year_zip_prefix`     | Prefix used to construct year-based ZIP filenames    |
| `bundle_zip_filename` | Optional multi-year ZIP filename (usually 2006–2016) |

---

## Supported Report Types & Mappings

### Traders in Financial Futures (TFF)

| Key                                   | Year ZIP Pattern         | Bundle ZIP                  |
| ------------------------------------- | ------------------------ | --------------------------- |
| `traders_in_financial_futures_fut`    | `fut_fin_txt_<YEAR>.zip` | `fin_fut_txt_2006_2016.zip` |
| `traders_in_financial_futures_futopt` | `com_fin_txt_<YEAR>.zip` | `fin_com_txt_2006_2016.zip` |

Examples:

```
fut_fin_txt_2026.zip
com_fin_txt_2024.zip
```

---

### Disaggregated Reports

| Key                    | Year ZIP Pattern            | Bundle ZIP                          |
| ---------------------- | --------------------------- | ----------------------------------- |
| `disaggregated_fut`    | `fut_disagg_txt_<YEAR>.zip` | `fut_disagg_txt_hist_2006_2016.zip` |
| `disaggregated_futopt` | `com_disagg_txt_<YEAR>.zip` | `com_disagg_txt_hist_2006_2016.zip` |

Examples:

```
fut_disagg_txt_2025.zip
com_disagg_txt_2026.zip
```

---

### Legacy Reports

Legacy reports predate the disaggregated format and use **shorter, non-descriptive prefixes**.

| Key             | Year ZIP Pattern      | Bundle ZIP                |
| --------------- | --------------------- | ------------------------- |
| `legacy_fut`    | `deacot<YEAR>.zip`    | `deacot1986_2016.zip`     |
| `legacy_futopt` | `deahistfo<YEAR>.zip` | `deahistfo_1995_2016.zip` |

Examples:

```
deacot2023.zip
deahistfo2024.zip
```

---

### Supplemental (Commodity Index Trader)

| Key                   | Year ZIP Pattern         | Bundle ZIP                  |
| --------------------- | ------------------------ | --------------------------- |
| `supplemental_futopt` | `dea_cit_txt_<YEAR>.zip` | `dea_cit_txt_2006_2016.zip` |

Examples:

```
dea_cit_txt_2026.zip
```

---

## How URLs Are Constructed

For year-based downloads:

```
<BASE_URL>/<year_zip_prefix><YEAR>.zip
```

Example:

```
https://www.cftc.gov/files/dea/history/fut_fin_txt_2026.zip
```

For bundled downloads:

```
<BASE_URL>/<bundle_zip_filename>
```

---

## ZIP Contents & File Selection

CFTC ZIP archives may contain:

* One or more `.txt` or `.csv` files
* Readme or metadata files

The downloader:

1. Filters for `.txt` and `.csv`
2. Selects the **largest file** (assumed to be the main dataset)
3. Reads it directly into memory

No assumptions are made about internal filenames.

---

## Stability & Maintenance Notes

* CFTC filenames are **not guaranteed stable**
* New report types may require new prefixes
* Structural ZIP changes may require updates to file-selection logic

When CFTC changes formats, **only `REPORT_SPECS` should need modification**.

---

## Non-Goals

* This mapping does not interpret data fields
* It does not normalize column names
* It does not validate report contents

Its sole purpose is **correct file retrieval**.

---

## References

* CFTC Historical Compressed Archives
  [https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm)

* CFTC COT Main Page
  [https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)


