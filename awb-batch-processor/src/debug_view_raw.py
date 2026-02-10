import pandas as pd
import os

file_path = r"D:\Automation_Workspace\Downloaded_AWBs\CXDU1865571.xlsx"
print(f"Reading {file_path}")

try:
    df = pd.read_excel(file_path, sheet_name=0, header=None, nrows=10, engine='openpyxl')
    print("--- First 10 Rows ---")
    print(df.to_string())
    
    print("\n--- Sheet Names ---")
    xl = pd.ExcelFile(file_path, engine='openpyxl')
    print(xl.sheet_names)
except Exception as e:
    print(f"Error: {e}")
