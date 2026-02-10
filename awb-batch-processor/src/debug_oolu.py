import pandas as pd
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.consolidation import find_header_row, ConsolidationPipeline

def debug_file(filepath):
    print(f"\n--- Debugging {os.path.basename(filepath)} ---")
    if not os.path.exists(filepath):
        print("File not found.")
        return

    pipeline = ConsolidationPipeline()
    lookup_map = pipeline.lookup_map
    
    xl = pd.ExcelFile(filepath, engine='openpyxl')
    for sheet in xl.sheet_names:
        print(f"\n[Sheet: {sheet}]")
        header_row = find_header_row(filepath, lookup_map, sheet_name=sheet)
        print(f"Detected Header Row: {header_row}")
        
        try:
            df = pd.read_excel(filepath, sheet_name=sheet, header=header_row, dtype=str)
            print(f"Columns (Raw): {df.columns.tolist()[:10]}...") 
            
            # Standardize
            new_cols = {}
            for col in df.columns:
                clean = str(col).strip().upper()
                if clean in lookup_map:
                    new_cols[col] = lookup_map[clean]
            df = df.rename(columns=new_cols)
            
            print(f"Mapped Columns: {[c for c in df.columns if c in lookup_map.values()]}")
            
            if 'DESTINATION_FC' in df.columns:
                 # FFill test
                 df['DESTINATION_FC'] = df['DESTINATION_FC'].ffill()
                 vals = df['DESTINATION_FC'].unique()
                 print(f"Destinations (ffilled): {vals[:10]}")
                 
            if 'BOX_COUNT' in df.columns:
                 count = pd.to_numeric(df['BOX_COUNT'], errors='coerce').fillna(0).sum()
                 print(f"Total Box Count: {count}")
            else:
                 print("BOX_COUNT not found.")
                 
        except Exception as e:
            print(f"Error reading sheet: {e}")

if __name__ == "__main__":
    debug_file(r"D:\Automation_Workspace\Downloaded_AWBs\OOLU5394711.xlsx")
