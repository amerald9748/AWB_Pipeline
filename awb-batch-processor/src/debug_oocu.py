import pandas as pd
import openpyxl
import os
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Full Configuration
# Load from settings.json slightly manually for debug or mock it
TARGET_DESTINATIONS = {"YYZ4", "YOW3", "YXU1", "YOO1", "YYZ7", "YYZ9", "XYY1", "YYZ1", "YYZ3", "YHM1", "YGK1", "YOW1"}

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

def read_excel_robust(filepath, sheet_name, lookup_map):
    try:
        # Standard Read
        return pd.read_excel(filepath, sheet_name=sheet_name, engine='openpyxl', dtype=str)
    except Exception as e:
        print(f"Standard read failed: {e}")
        # Fallback
        try:
            wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
            ws = wb[sheet_name]
            iterator = ws.values
            
            potential_headers = []
            try:
                for _ in range(20):
                    potential_headers.append(next(iterator))
            except StopIteration:
                pass
            
            best_idx = 0
            max_matches = 0
            
            if lookup_map:
                for i, row in enumerate(potential_headers):
                    if not row: continue
                    row_strs = [str(x).strip().upper() for x in row if x is not None]
                    matches = 0
                    for alias in lookup_map.keys():
                        if alias in row_strs:
                            matches += 1
                    if matches > max_matches:
                        max_matches = matches
                        best_idx = i
            
            headers = potential_headers[best_idx]
            rows = [headers] + potential_headers[best_idx+1:]
            
            while True:
                try:
                    row = next(iterator)
                    rows.append(row)
                except StopIteration:
                    break
                except Exception:
                    break
            
            if len(rows) > 1:
                return pd.DataFrame(rows[1:], columns=rows[0])
            return None

        except Exception as e:
            print(f"Fallback failed: {e}")
            return None

def analyze(filepath):
    print(f"--- Analyzing {os.path.basename(filepath)} ---")
    
    try:
        xl = pd.ExcelFile(filepath, engine='openpyxl')
        print(f"Sheets: {xl.sheet_names}")
        
        valid_dfs = []

        for sheet in xl.sheet_names:
            print(f"\nProcessing Sheet: {sheet}")
            
            df = read_excel_robust(filepath, sheet, LOOKUP_MAP)
            
            if df is None or df.empty:
                print("  Failed to read or empty")
                continue

            # Standardize
            new_columns = {}
            for col in df.columns:
                col_clean = str(col).strip().upper()
                if col_clean in LOOKUP_MAP:
                    new_columns[col] = LOOKUP_MAP[col_clean]
            df = df.rename(columns=new_columns)
            
            print(f"  Columns: {df.columns.tolist()}")
            
            # Check required columns
            required_cols = list(COLUMN_MAPPING.keys())
            available_cols = [c for c in required_cols if c in df.columns]
            if not available_cols:
                 print("  No mapped columns found")
                 continue
            df = df[available_cols]

            if 'BOX_COUNT' in df.columns:
                df['BOX_COUNT'] = pd.to_numeric(df['BOX_COUNT'], errors='coerce').fillna(0)
            
            # Destination Filter
            if 'DESTINATION_FC' in df.columns:
                 df['DESTINATION_FC'] = df['DESTINATION_FC'].ffill()
                 df['DESTINATION_FC'] = df['DESTINATION_FC'].astype(str).str.strip().str.upper()
                 
                 print(f"  Unique Destinations: {df['DESTINATION_FC'].unique()}")
                 
                 count_before = df['BOX_COUNT'].sum() if 'BOX_COUNT' in df.columns else 0
                 print(f"  Gross Box Count: {count_before}")

                 def is_valid(val):
                     for t in TARGET_DESTINATIONS:
                         if t in val: return True
                     return False
                 
                 df_filtered = df[df['DESTINATION_FC'].apply(is_valid)]
                 
                 count_after = df_filtered['BOX_COUNT'].sum() if 'BOX_COUNT' in df_filtered.columns else 0
                 print(f"  Net Box Count (Dest Filtered): {count_after}")
                 
                 if count_after > 0:
                     valid_dfs.append((sheet, df_filtered))
            else:
                 print("  No DESTINATION_FC column")
                 # Some sheets might rely on external header context or single dest?
                 # Pipeline usually requires DESTINATION_FC

        # Prioritization Check
        priority_keywords = ["EAST", "加东", "LTL"]
        has_priority = False
        for s, _ in valid_dfs:
            if any(pk in str(s).upper() for pk in priority_keywords):
                has_priority = True
                break
        
        print(f"\nHas Priority Sheet: {has_priority}")
        
    except Exception as e:
        print(f"Fatal Parsing Error: {e}")

if __name__ == "__main__":
    analyze(r"D:\Automation_Workspace\Downloaded_AWBs\OOCU6287202.xlsx")
