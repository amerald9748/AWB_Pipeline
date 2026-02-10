import pandas as pd
import openpyxl

file_path = r"D:\Automation_Workspace\Downloaded_AWBs\OOCU6287202.xlsx"

print(f"Reading {file_path}")
try:
    import json
    df = pd.read_excel(file_path, header=None, nrows=10, engine='openpyxl')
    for i, row in df.iterrows():
        if i == 5:
            full = [str(x) if pd.notna(x) else None for x in row.tolist()]
            print(f"Row {i} Part 1: {json.dumps(full[:5])}")
            print(f"Row {i} Part 2: {json.dumps(full[5:])}")
except Exception as e:
    print(f"Error: {e}")
