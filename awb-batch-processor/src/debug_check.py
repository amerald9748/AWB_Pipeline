import pandas as pd
import os
import logging
import warnings

# Suppress warnings
warnings.simplefilter("ignore")

# Mock Configuration (copied from settings.json for standalone run)
TARGET_DESTINATIONS = {
  "YYZ4", "YOW3", "YXU1", "YOO1", "YYZ7", "YYZ9", "XYY1" # Add any others if needed
}

COLUMN_MAPPING = {
    "BOX_COUNT": ["PCS", "CTNS", "箱数/件数", "箱数", "件数", "CARTON", "CARTONS", "CARTON COUNT"],
    "WEIGHT_KG": ["KGS", "GW", "重量", "实际重量(KG)", "WEIGHT", "G.W.", "G.W"],
    "DESTINATION_FC": ["FC", "目的地", "AMAZON", "收件人", "收件方", "SHIP TO", "DESTINATION", "派送目的地", "仓库代码"],
    "FBA_ID": ["FBA_ID", "FBA NO", "FBA NO.", "AMAZON REFEENCE ID", "REF ID", "扩展单号", "SHIPMENT ID", "FBA SHIPMENT ID"],
    "PO_NUMBER": ["PO", "PO NO", "PO NO.", "PURCHASE ORDER", "PO#", "PO NUMBER", "客户单号"],
    "DELIVERY_METHOD": ["卡派", "UPS", "DELIVERY METHOD", "派送方式", "渠道", "TRANSPROTATION STYLE"]
}

# Reverse lookup
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
            if matches > max_matches:
                max_matches = matches
                best_row = i
        if max_matches >= 2:
            return best_row
        return 0
    except Exception as e:
        print(f"Header Scan Error: {e}")
        return 0

def log_count(filename, count):
    with open("counts.txt", "a", encoding="utf-8") as f:
        f.write(f"{filename}: {count}\n")

def run_debug(test_file):
    filename = os.path.basename(test_file)
    try:
        xl = pd.ExcelFile(test_file, engine='openpyxl')
        valid_dfs = []

        for sheet in xl.sheet_names:
            header_row = find_header_row(test_file, LOOKUP_MAP, sheet_name=sheet)
            df = pd.read_excel(test_file, sheet_name=sheet, engine='openpyxl', header=header_row, dtype=str)
            
            new_columns = {}
            for col in df.columns:
                col_clean = str(col).strip().upper()
                if col_clean in LOOKUP_MAP:
                    new_columns[col] = LOOKUP_MAP[col_clean]
            df = df.rename(columns=new_columns)
            
            available_cols = [c for c in COLUMN_MAPPING.keys() if c in df.columns]
            if not available_cols:
                continue
                
            df = df[available_cols]

            if 'BOX_COUNT' in df.columns:
                df['BOX_COUNT'] = pd.to_numeric(df['BOX_COUNT'], errors='coerce').fillna(0)
            
            if 'DESTINATION_FC' in df.columns:
                 df['DESTINATION_FC'] = df['DESTINATION_FC'].ffill()
                 df['DESTINATION_FC'] = df['DESTINATION_FC'].astype(str).str.strip().str.upper()
                 
                 def is_valid(val):
                     for t in TARGET_DESTINATIONS:
                         if t in val: return True
                     return False
                 
                 df = df[df['DESTINATION_FC'].apply(is_valid)]
                 
            if df.empty:
                continue

            valid_dfs.append((sheet, df))

        # Prioritization Check
        priority_keywords = ["EAST", "加东"]
        has_priority = False
        for s, _ in valid_dfs:
            if any(pk in str(s).upper() for pk in priority_keywords):
                has_priority = True
                break
        
        final_dfs = []
        if has_priority:
            for s, df in valid_dfs:
                if any(pk in str(s).upper() for pk in priority_keywords):
                     final_dfs.append(df)
        else:
            final_dfs = [df for _, df in valid_dfs]
            
        if final_dfs:
            final_df = pd.concat(final_dfs, ignore_index=True)
            total = final_df['BOX_COUNT'].sum()
            log_count(filename, total)
        else:
            log_count(filename, 0)

    except Exception as e:
        log_count(filename, f"Error: {e}")

if __name__ == "__main__":
    if os.path.exists("counts.txt"):
        os.remove("counts.txt")
        
    file1 = r"D:\Automation_Workspace\Downloaded_AWBs\CXDU1865571.xlsx"
    file2 = r"D:\Automation_Workspace\Downloaded_AWBs\FWRU0085703.xlsx"
    
    if os.path.exists(file1):
        run_debug(file1)
    
    if os.path.exists(file2):
        run_debug(file2)
