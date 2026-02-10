import pandas as pd
import openpyxl
import os
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock Mapping
COLUMN_MAPPING = {
    "BOX_COUNT": ["PCS", "CTNS", "箱数/件数", "箱数", "件数", "CARTON", "CARTONS", "CARTON COUNT"],
    "WEIGHT_KG": ["KGS", "GW", "重量", "实际重量(KG)", "WEIGHT", "G.W.", "G.W"],
    "DESTINATION_FC": ["FC", "目的地", "AMAZON", "收件人", "收件方", "SHIP TO", "DESTINATION", "派送目的地", "仓库代码"],
    "FBA_ID": ["FBA_ID", "FBA NO", "FBA NO.", "AMAZON REFEENCE ID", "REF ID", "扩展单号", "SHIPMENT ID", "FBA SHIPMENT ID"],
    "PO_NUMBER": ["PO", "PO NO", "PO NO.", "PURCHASE ORDER", "PO#", "PO NUMBER", "客户单号"],
    "DELIVERY_METHOD": ["卡派", "UPS", "DELIVERY METHOD", "派送方式", "渠道", "TRANSPROTATION STYLE"]
}
LOOKUP_MAP = {}
for code, aliases in COLUMN_MAPPING.items():
    for alias in aliases:
        LOOKUP_MAP[alias.upper()] = code

def find_header_row(filepath, lookup_map, max_scan_rows=20, sheet_name=0):
    try:
        df_scan = pd.read_excel(filepath, sheet_name=sheet_name, engine='openpyxl', header=None, nrows=max_scan_rows, dtype=str)
        
        best_row = 0
        max_matches = 0
        
        for i, row in df_scan.iterrows():
            row_values = [str(x).strip().upper() for x in row.values]
            matches = 0
            for alias in lookup_map.keys():
                if alias in row_values:
                    matches += 1
            
            print(f"Row {i} matches: {matches} -> {row_values}")
            
            if matches > max_matches:
                max_matches = matches
                best_row = i
        
        print(f"Best Row: {best_row} with {max_matches} matches")
        
        if max_matches >= 2:
            return best_row
        return 0
        
    except Exception as e:
        print(f"Failed: {e}")
        return 0

def read_excel_robust(filepath, sheet_name, header_row=None, lookup_map=None):
    try:
        # Standard Read
        return pd.read_excel(filepath, sheet_name=sheet_name, engine='openpyxl', header=header_row, dtype=str)
    except Exception as e:
        print(f"Read failed: {e}")
        return None

file_path = r"D:\Automation_Workspace\Downloaded_AWBs\OOCU6287202.xlsx"
header_row = find_header_row(file_path, LOOKUP_MAP, sheet_name=0)
print(f"Found Header Row: {header_row}")

if header_row > 0:
    df = read_excel_robust(file_path, sheet_name=0, header_row=header_row, lookup_map=LOOKUP_MAP)
    
    # Rename columns
    new_columns = {}
    for col in df.columns:
        col_clean = str(col).strip().upper()
        if col_clean in LOOKUP_MAP:
             new_columns[col] = LOOKUP_MAP[col_clean]
    df = df.rename(columns=new_columns)

    # Check for duplicates (fix logic)
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]

    if 'DESTINATION_FC' in df.columns:
        df['DESTINATION_FC'] = df['DESTINATION_FC'].ffill()
        df['DESTINATION_FC'] = df['DESTINATION_FC'].astype(str).str.strip().str.upper()
        
        print("--- All Destinations + Box Count ---")
        TARGET_DESTINATIONS = {"YYZ4", "YOW3", "YXU1", "YOO1", "YYZ7", "YYZ9", "XYY1", "YYZ1", "YYZ3", "YHM1", "YGK1", "YOW1"}
        
        print("--- Rows Dropped by Dest Filter ---")
        for i, row in df.iterrows():
            dest = row.get('DESTINATION_FC', '')
            box = row.get('BOX_COUNT', 0)
            
            # Check validity
            valid = False
            for t in TARGET_DESTINATIONS:
                 if t in str(dest):
                     valid = True
                     break
            
            if not valid:
                print(f"Row {i}: Dest='{dest}' Box={box} FBA='{row.get('FBA_ID')}'")



