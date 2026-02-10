import pytest
import json
import os
from src.excel_processor import ExcelProcessor

# Define a fixture for the ExcelProcessor
@pytest.fixture
def excel_processor():
    # Assuming the test is run from the project root or a similar setup
    # Adjust config_path as necessary for the test environment
    return ExcelProcessor(config_path='config/settings.json')

def test_excel_processor_init(excel_processor):
    assert excel_processor.config is not None
    assert "excel_columns" in excel_processor.config
    assert "manifest_keywords" in excel_processor.config['file_patterns']

def test_normalize_column_name(excel_processor):
    # Test with a direct match
    assert excel_processor._normalize_column_name("运单号") == "tracking_number"
    # Test with a case variation (if your config supports it)
    # The current config has direct string values, so case variation might not work as expected
    # without further modification to the _normalize_column_name logic to handle lists of variations.
    # For now, let's assume exact match based on the current _normalize_column_name implementation.
    assert excel_processor._normalize_column_name("件数") == "carton_count"
    assert excel_processor._normalize_column_name("PO Number") == "po_number"
    # Test with an unknown column name
    assert excel_processor._normalize_column_name("Unknown Column") == "Unknown Column"

def test_extract_data(excel_processor):
    dummy_file_path = "D:/UnloadingPlans/拾谷SAGSC/Amazon/拾谷/MATU4584485/MATU4584485_清单.xlsx"
    extracted_data = excel_processor.extract_data(dummy_file_path)

    assert isinstance(extracted_data, dict)
    assert "卡派" in extracted_data
    assert "UPS" in extracted_data

    # Validate data for "卡派" sheet
    kappa_data = extracted_data['卡派']
    assert "data" in kappa_data
    assert "formulas" in kappa_data
    assert "original_headers" in kappa_data
    assert "normalized_headers" in kappa_data

    assert len(kappa_data['data']) == 2
    assert kappa_data['data'][0]['tracking_number'] == "MATU4584485"
    assert kappa_data['data'][0]['carton_count'] == 10
    assert kappa_data['data'][1]['warehouse_code'] == "YYZ4"
    assert kappa_data['formulas']['件数_SUM'] == 15

    # Validate data for "UPS" sheet
    ups_data = extracted_data['UPS']
    assert len(ups_data['data']) == 1
    assert ups_data['data'][0]['tracking_number'] == "MATU4631210"
    assert ups_data['data'][0]['carton_count'] == 20
    assert ups_data['data'][0]['po_number'] == "PO123"
    assert ups_data['formulas']['件数_SUM'] == 20


def test_config_not_found():
    with pytest.raises(FileNotFoundError):
        ExcelProcessor(config_path='non_existent_config.json')


def test_invalid_json_config(tmp_path):
    invalid_json_file = tmp_path / "invalid_config.json"
    invalid_json_file.write_text("{this is not valid json}")
    with pytest.raises(json.JSONDecodeError):
        ExcelProcessor(config_path=str(invalid_json_file))
