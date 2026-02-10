import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import shutil
from src.consolidation import run_consolidation

def create_dummy_files(input_dir):
    if os.path.exists(input_dir):
        shutil.rmtree(input_dir)
    os.makedirs(input_dir)
    
    # File 1: Valid
    df1 = pd.DataFrame({
        'FBA NO.': ['FBA111', 'FBA222'],
        'PO#': ['PO1', 'PO2'],
        'PCS': [10, 20],
        'KGS': [100, 200],
        'AMAZON': ['YOW3', 'YYZ4'], # Both in target
        'EXTRA': ['Noise', 'Noise']
    })
    df1.to_excel(os.path.join(input_dir, "test1.xlsx"), index=False)
    
    # File 2: Partial valid, some rows rejected by destination
    df2 = pd.DataFrame({
        'SHIPMENT ID': ['FBA333', 'FBA444'],
        'REFERENCE ID': ['PO3', 'PO4'],
        'CARTON COUNT': [30, 40],
        'WEIGHT': [300, 400],
        'DESTINATION': ['XYY1', 'BAD_DEST'], # XYY1 is valid, BAD_DEST is not
    })
    df2.to_excel(os.path.join(input_dir, "test2.xlsx"), index=False)
    
    # File 3: Invalid columns
    df3 = pd.DataFrame({
        'WRONG': ['Data'],
        'COLUMNS': ['Here']
    })
    df3.to_excel(os.path.join(input_dir, "test3.xlsx"), index=False)

def verify_output(output_file):
    if not os.path.exists(output_file):
        print("FAIL: Output file not created.")
        return
        
    df = pd.read_excel(output_file)
    print("Consolidated DataFrame:")
    print(df)
    
    # Expectations:
    # FBA111 (YOW3) -> Keep
    # FBA222 (YYZ4) -> Keep
    # FBA333 (XYY1) -> Keep
    # FBA444 (BAD_DEST) -> Drop
    # test3 -> Drop (no columns)
    
    count = len(df)
    if count == 3:
        print("PASS: Correct number of rows (3).")
    else:
        print(f"FAIL: Expected 3 rows, got {count}.")
        
    expected_cols = {'SOURCE_FILE', 'FBA_ID', 'PO_NUMBER', 'DESTINATION_FC', 'BOX_COUNT', 'WEIGHT_KG'}
    if set(df.columns) == expected_cols:
        print("PASS: Columns are standardized correctly.")
    else:
        print(f"FAIL: Columns mismatch. Got {df.columns}")

if __name__ == "__main__":
    input_dir = "./tests/data_input"
    output_file = "./tests/data_output/master_test.xlsx"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print("Creating dummy files...")
    create_dummy_files(input_dir)
    
    print("Running consolidation...")
    run_consolidation(input_dir, output_file)
    
    print("Verifying...")
    verify_output(output_file)
