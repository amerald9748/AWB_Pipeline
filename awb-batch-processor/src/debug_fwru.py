import pandas as pd
import openpyxl
import os

file_path = r"D:\Automation_Workspace\Downloaded_AWBs\FWRU0085703.xlsx"

print(f"Testing {os.path.basename(file_path)}")

# print("\n--- Method 1: Pandas Iteration ---")
# try:
#     xl = pd.ExcelFile(file_path, engine='openpyxl')
#     print(f"Sheets: {xl.sheet_names}")
#     for sheet in xl.sheet_names:
#         print(f"Reading {sheet}...")
#         try:
#             df = pd.read_excel(file_path, sheet_name=sheet, engine='openpyxl')
#             print(f"  Success: {len(df)} rows")
#         except Exception as e:
#             print(f"  FAILED {sheet}: {e}")
# except Exception as e:
#     print(f"Failed to open ExcelFile: {e}")

print("\n--- Method 2: Openpyxl Read-Only Conversion (Robust) ---")
try:
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    for sheet in wb.sheetnames:
        print(f"Processing {sheet}...")
        ws = wb[sheet]
        
        rows = []
        success_count = 0
        error_count = 0
        
        try:
            # We must use iter_rows(values_only=True) to avoid cell object creation which might trigger validation?
            # ws.values does that.
            iterator = ws.values
            
            # Manual Header Detection
            # Scan first 20 rows
            potential_headers = []
            try:
                for _ in range(20):
                    potential_headers.append(next(iterator))
            except StopIteration:
                pass
            except Exception as e:
                print(f"  Scan interrupted: {e}")
            
            # Find best row
            best_idx = 0
            max_matches = 0
            # Mock lookup keys from debug_check.py
            lookup_keys = ["PCS", "CTNS", "箱数", "件数", "箱数/件数", "CARTON COUNT", "WEIGHT", "KGS", "GW", "重量", "DESTINATION", "FC", "FBA", "PO"]
            
            for i, row in enumerate(potential_headers):
                if not row: continue
                matches = 0
                row_strs = [str(x).strip().upper() for x in row if x is not None]
                for key in lookup_keys:
                    if key in row_strs:
                        matches += 1
                if matches > max_matches:
                    max_matches = matches
                    best_idx = i
            
            print(f"  Best Header Row: {best_idx} (Matches: {max_matches})")
            
            headers = potential_headers[best_idx]
            # Add remaining potential rows to data
            # The iterator is already advanced by 20.
            # We need to yield rows from potential_headers[best_idx+1:] first
            
            # Restart iterator approach is hard with generator.
            # But we saved the scanned rows in 'potential_headers'.
            # So start 'rows' list with these.
            
            # Actually, rows list should start with headers? 
            # Df needs headers separate.
            
            # We will process rows from potential_headers[best_idx+1:] + iterator
            
            buffered_rows = potential_headers[best_idx+1:]
            
            # Now consume iterator
            while True:
                try:
                    row = next(iterator)
                    buffered_rows.append(row)
                    success_count += 1
                except StopIteration:
                    break
                except Exception as e:
                    error_count += 1
                    # print(f"  Fatal Row Error? {e}")
                    break
            
            rows = [headers] + buffered_rows
        except Exception as e:
            print(f"  Iterator setup failed: {e}")

        if rows:
            df = pd.DataFrame(rows[1:], columns=rows[0])
            print(f"  Recovered: {len(df)} rows. Errors: {error_count}")
            
            # Simple Column Mapping and Sum
            # Mock mapping
            lookup = {"PCS": "BOX_COUNT", "CTNS": "BOX_COUNT", "箱数": "BOX_COUNT", "件数": "BOX_COUNT", 
                      "箱数/件数": "BOX_COUNT", "CARTON COUNT": "BOX_COUNT"}
            
            new_cols = {}
            for c in df.columns:
                c_str = str(c).strip().upper()
                if c_str in lookup:
                    new_cols[c] = lookup[c_str]
            df = df.rename(columns=new_cols)
            
            if 'BOX_COUNT' in df.columns:
                 df['BOX_COUNT'] = pd.to_numeric(df['BOX_COUNT'], errors='coerce').fillna(0)
            
            # Destination Mapping and Filter
            dest_col = None
            if 'DESTINATION_FC' in df.columns:
                dest_col = 'DESTINATION_FC'
            
            if dest_col:
                # Filter
                targets = {"YYZ4", "YOW3", "YXU1", "YOO1", "YYZ7", "YYZ9", "XYY1"}
                df[dest_col] = df[dest_col].astype(str).str.strip().str.upper()
                df = df[df[dest_col].apply(lambda x: any(t in x for t in targets))]
                
                if not df.empty:
                    total = df['BOX_COUNT'].sum()
                    print(f"  Valid Box Count (Target Dests): {total}")
                else:
                    print("  No rows matched target destinations")
            else:
                 print("  No DESTINATION_FC/FC column found")
        else:
            print("  No data recovered")
            
except Exception as e:
    print(f"Failed Method 2: {e}")
