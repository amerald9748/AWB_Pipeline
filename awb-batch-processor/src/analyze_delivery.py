import pandas as pd
import os

file_path = r'D:\Automation_Workspace\Downloaded_AWBs\Master_Consolidated_FBA.xlsx'
if os.path.exists(file_path):
    df = pd.read_excel(file_path)
    print("--- Delivery Method Analysis ---")
    if 'DELIVERY_METHOD' in df.columns:
        print(df['DELIVERY_METHOD'].value_counts())
        
        # Check for keywords like '卡派' (Truck) vs '快递' or 'UPS'
        truck_keywords = ['卡派', 'TRUCK', 'LTL', '卡车']
        ups_keywords = ['UPS', '快递', 'COURIER']
        
        def categorize(val):
            val = str(val).upper()
            if any(k in val for k in truck_keywords): return "TRUCK"
            if any(k in val for k in ups_keywords): return "UPS"
            return "OTHER/UNKNOWN"
            
        df['CATEGORY'] = df['DELIVERY_METHOD'].apply(categorize)
        print("\nSum by Category:")
        print(df.groupby('CATEGORY')['BOX_COUNT'].sum())
    else:
        print("DELIVERY_METHOD column not found.")
    
    print(f"\nTotal Boxes: {df['BOX_COUNT'].sum()}")
else:
    print(f"File not found: {file_path}")
