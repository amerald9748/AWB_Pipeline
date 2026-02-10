import pytest
from src.nutcloud.scoring import score_nutstore_file, find_best_file_match

def test_score_nutstore_file_exact_match():
    item = {"name": "CXDU2205700.pdf", "path": "/path/CXDU2205700.pdf"}
    score = score_nutstore_file(item, "CXDU2205700")
    assert score >= 0.3

def test_score_nutstore_file_rejects_cipl():
    item = {"name": "CXDU2205700_CI&PL.xlsx", "path": "/path/CXDU2205700_CI&PL.xlsx"}
    score = score_nutstore_file(item, "CXDU2205700")
    assert score == 0.0

def test_score_nutstore_file_keywords():
    item = {"name": "Unloading Plan.xlsx", "path": "/path/Unloading Plan.xlsx"}
    score = score_nutstore_file(item, "CXDU2205700")
    # +0.2 for "plan", +0.1 for xlsx
    assert score >= 0.3

def test_find_best_file_match_priority():
    items = [
        {"name": "random_file.txt", "path": "/path/random_file.txt", "isDir": False},
        {"name": "CXDU2205700_Invoice.pdf", "path": "/path/CXDU2205700_Invoice.pdf", "isDir": False},
        {"name": "Other.xlsx", "path": "/path/Other.xlsx", "isDir": False}
    ]
    best = find_best_file_match(items, "CXDU2205700")
    assert best["name"] == "CXDU2205700_Invoice.pdf"

def test_find_best_file_match_chinese_keyword():
    items = [
        {"name": "random.txt", "path": "/path/random.txt", "isDir": False},
        {"name": "派送清单.xlsx", "path": "/path/派送清单.xlsx", "isDir": False}
    ]
    best = find_best_file_match(items, "CXDU2205700")
    assert best["name"] == "派送清单.xlsx"
