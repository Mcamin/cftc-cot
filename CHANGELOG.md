# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2026-01-29

### Added
- Local caching mechanism in `cot_download_year` and `cot_download_bundle`. The functions now check if the ZIP file already exists locally before downloading.
- Logic to always download the current year's data in `cot_download_year`, bypassing the cache to ensure the latest updates are retrieved.
- `datetime` import to handle current year detection.

## [0.1.2] - 2026-01-28

### Fixed
- Improved directory handling with `_ensure_dir` to ensure the download path exists before operations.
- Enhanced robustness in `cot_download_year` and `cot_download_bundle` by determining the full output path before checking cache.

## [0.1.2] - 2026-01-27

### Added
- Initial implementation of the CFTC COT downloader.
- Scraper for COT explanatory notes.
- Support for multiple report types (Financial Futures, Disaggregated, etc.).
- Unit tests for core functionality.
