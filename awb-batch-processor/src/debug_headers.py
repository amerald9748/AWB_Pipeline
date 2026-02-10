import pandas as pd
import openpyxl
import os

file_path = r"D:\Automation_Workspace\Downloaded_AWBs\FWRU0085703.xlsx"

try:
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb["EAST"]
    
    rows = []
    iterator = ws.values
    while True:
        try:
            row = next(iterator)
            rows.append(row)
        except StopIteration:
            break
        except Exception:
            pass
    
    print(f"Total rows read: {len(rows)}")
    
    # Find Header
    # Simple scan
    best_idx = 0
    max_len = 0
    for i in range(min(20, len(rows))):
        row = rows[i]
        valid_cells = [x for x in row if x]
        if len(valid_cells) > max_len:
            max_len = len(valid_cells)
            best_idx = i
            
    print(f"Header Row (est {best_idx}): {rows[best_idx]}")
    
    print("\n--- Last 5 Rows ---")
    for row in rows[-5:]:
        print(row)
        
except Exception as e:
    print(e)
