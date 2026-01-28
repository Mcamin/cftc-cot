import io
import zipfile
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add src to sys.path to import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cftc_cot.cftc_cot import (
    _ensure_dir,
    _pick_data_file_from_zip,
    _read_cot_file_from_zip,
    cot_download_year,
    cot_download_bundle,
    cot_download_year_range,
    cot_explanatory_notes,
    REPORT_SPECS
)

def create_mock_zip(files_content):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for name, content in files_content.items():
            zf.writestr(name, content)
    return buf.getvalue()

def test_ensure_dir(tmp_path):
    path = tmp_path / "test_dir"
    returned_path = _ensure_dir(path)
    assert path.exists()
    assert returned_path == path.resolve()

def test_pick_data_file_from_zip():
    # Test case: multiple files, should pick the largest .txt/.csv
    files = {
        "readme.txt": "short",
        "data.csv": "this is a longer piece of data",
        "other.txt": "medium length data"
    }
    zip_bytes = create_mock_zip(files)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        picked = _pick_data_file_from_zip(zf)
        assert picked == "data.csv"

    # Test case: no .txt/.csv
    files_no_data = {"image.png": "binary"}
    zip_bytes_no_data = create_mock_zip(files_no_data)
    with zipfile.ZipFile(io.BytesIO(zip_bytes_no_data)) as zf:
        with pytest.raises(ValueError, match="No .txt/.csv found"):
            _pick_data_file_from_zip(zf)

def test_read_cot_file_from_zip():
    csv_content = "col1,col2\n1,2\n3,4"
    zip_bytes = create_mock_zip({"data.csv": csv_content})
    df = _read_cot_file_from_zip(zip_bytes)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 2)
    assert list(df.columns) == ["col1", "col2"]

@patch("cftc_cot.cftc_cot._http_get_bytes")
def test_cot_download_year(mock_get, tmp_path):
    csv_content = "date,val\n2023-01-01,10"
    zip_bytes = create_mock_zip({"data.csv": csv_content})
    mock_get.return_value = zip_bytes
    
    dataset_path = tmp_path / "dataset"
    df = cot_download_year(2023, path=dataset_path, store_zip=True)
    
    assert isinstance(df, pd.DataFrame)
    assert (dataset_path / "fut_fin_txt_2023.zip").exists()
    mock_get.assert_called_once()
    assert "fut_fin_txt_2023.zip" in mock_get.call_args[0][0]

@patch("cftc_cot.cftc_cot._http_get_bytes")
def test_cot_download_bundle(mock_get, tmp_path):
    csv_content = "date,val\n2010-01-01,10"
    zip_bytes = create_mock_zip({"data.csv": csv_content})
    mock_get.return_value = zip_bytes
    
    df = cot_download_bundle(path=tmp_path)
    assert isinstance(df, pd.DataFrame)
    mock_get.assert_called_once()
    assert "fin_fut_txt_2006_2016.zip" in mock_get.call_args[0][0]

    # Test invalid report type
    with pytest.raises(ValueError, match="Unknown cot_report_type"):
        cot_download_bundle(cot_report_type="invalid")

@patch("cftc_cot.cftc_cot.cot_download_year")
def test_cot_download_year_range(mock_download):
    df1 = pd.DataFrame({"val": [1]})
    df2 = pd.DataFrame({"val": [2]})
    mock_download.side_effect = [df1, df2]
    
    df = cot_download_year_range(2021, 2022)
    assert len(df) == 2
    assert mock_download.call_count == 2

@patch("cftc_cot.cftc_cot._http_get_bytes")
def test_cot_explanatory_notes(mock_get):
    html = """
    <html>
        <body>
            <div class="ckeditor-accordion">
                <dt>Title 1</dt>
                <dd>Explanation 1</dd>
                <dt>Title 2</dt>
                <dd>Explanation 2</dd>
            </div>
        </body>
    </html>
    """
    mock_get.return_value = html.encode("utf-8")
    
    df = cot_explanatory_notes()
    assert len(df) == 2
    assert df.iloc[0]["section"] == "title_1"
    assert df.iloc[0]["text"] == "Explanation 1"

@patch("cftc_cot.cftc_cot._http_get_bytes")
def test_cot_explanatory_notes_fallback(mock_get):
    html = "<html><main>Fallback Text</main></html>"
    mock_get.return_value = html.encode("utf-8")
    
    df = cot_explanatory_notes()
    assert len(df) == 1
    assert df.iloc[0]["section"] == "full_page_fallback"
    assert "Fallback Text" in df.iloc[0]["text"]
