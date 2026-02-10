import pandas as pd
import os
import json
import logging
import openpyxl
from concurrent.futures import ProcessPoolExecutor
import warnings

# Suppress openpyxl styling warnings for speed
warnings.simplefilter("ignore")

logger = logging.getLogger(__name__)

class ConsolidationPipeline:
    def __init__(self, config_path=None):
        if not config_path:
            # Default to relative path from this file
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
            
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
        self.column_mapping = self.config['excel_columns']
        self.target_destinations = set(self.config['target_destinations'])
        
        # Build reverse lookup map for O(1) access
        self.lookup_map = {}
        for standard_col, aliases in self.column_mapping.items():
            for alias in aliases:
                self.lookup_map[alias.upper()] = standard_col

    def get_effective_config(self, include_ups=False, target_destinations_override=None):
        """
        Returns a config dict for the worker to use.
        """
        destinations = self.target_destinations
        if target_destinations_override:
            if target_destinations_override == 'ALL':
                destinations = None # No filtering
            else:
                destinations = set(target_destinations_override)
        
        # Get exclude keywords from settings, or empty if include_ups is True
        exclude_keywords = []
        if not include_ups:
            exclude_keywords = self.config.get('delivery_methods', {}).get('exclude_keywords', [])
            
        return {
            'target_destinations': destinations,
            'exclude_delivery_keywords': exclude_keywords,
            'column_mapping': self.column_mapping,
            'lookup_map': self.lookup_map
        }

    def standardize_headers(self, df):
        """
        Iterates through the dataframe columns and renames them 
        based on the COLUMN_MAPPING dictionary.
        """
        new_columns = {}
        for col in df.columns:
            col_clean = str(col).strip().upper()
            if col_clean in self.lookup_map:
                new_columns[col] = self.lookup_map[col_clean]
                
        return df.rename(columns=new_columns)

    def process_single_file(self, filepath):
        """
        The Worker Unit: Reads, Cleans, Filters, and Tags one file.
        """
        filename = os.path.basename(filepath)
        try:
            # Read file - using 'openpyxl' engine. 
            # We treat everything as string initially to avoid type inference issues with IDs
            df = pd.read_excel(filepath, engine='openpyxl', dtype=str) 
            
            # 1. Standardize Headers
            df = self.standardize_headers(df)
            
            # 2. Check for Essential Columns
            # We relax the requirement to have match at least ONE essential column (e.g. FBA_ID) to consider it valid?
            # Or strictly follow the user logic: "required_cols = list(COLUMN_MAPPING.keys())" ?
            # User draft said: "required_cols = list(COLUMN_MAPPING.keys()) ... if not available_cols: return None"
            # It checked "available_cols = [col for col in required_cols if col in df.columns]"
            # So as long as *some* columns match, it proceeded. Let's stick to that.
            
            required_cols = list(self.column_mapping.keys())
            available_cols = [col for col in required_cols if col in df.columns]
            
            if not available_cols:
                logger.debug(f"Skipping {filename}: No standard columns found.")
                return None
                
            # Select only standard columns to drop extra noise
            df = df[available_cols]
            
            # 3. Filter by Destination
            if 'DESTINATION_FC' in df.columns:
                # Clean destination column (trim whitespace)
                df['DESTINATION_FC'] = df['DESTINATION_FC'].astype(str).str.strip().str.upper()
                # Filter rows where destination is in target set
                df = df[df['DESTINATION_FC'].isin(self.target_destinations)]
            
            # If empty after filtering, return None (or empty df)
            if df.empty:
                return None

            # 4. Add Source Tag
            df['SOURCE_FILE'] = filename
            
            return df

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            return None

    def consolidate(self, input_dir: str, output_file: str):
        """
        Main consolidation runner.
        """
        logger.info(f"Starting consolidation from {input_dir}...")
        
        # Get list of all excel files
        all_files = []
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if file.lower().endswith(('.xlsx', '.xls')):
                    all_files.append(os.path.join(root, file))
        
        if not all_files:
            logger.warning("No Excel files found to consolidate.")
            return False

        logger.info(f"Found {len(all_files)} files. Spooling up processors...")

        # --- PARALLEL EXECUTION ---
        results = []
        # Wrapper to allow pickling instance method if needed, or just iterate directly
        # ProcessPoolExecutor with instance methods can be tricky in some python versions/platforms.
        # But 'process_single_file' uses self.lookup_map, so it needs the instance.
        # We can pass the config or lookup map to a static method to be safe, 
        # or just rely on 'fork' start method on linux, but this is Windows.
        # For safety on Windows, it's better to use a top-level function or ensure serialization works.
        # Let's try synchronous for debugging or use a static helper if needed. 
        # For now, let's use a simple loop or standard map if not too heavy, 
        # or define a top-level worker that takes the params.
        
        # Given the "High-Velocity" requirement, parallel is preferred.
        # Let's define a standalone helper to avoid pickling the whole class.
        
        lookup_map = self.lookup_map
        target_destinations = self.target_destinations
        column_keys = list(self.column_mapping.keys())
        
        # We'll use a local helper or list comprehension for now to ensure it works on Windows
        # without complex serialization issues of the class instance.
        # Or simply run sequentially if 'high-velocity' isn't compromised too much by python GIL/overhead for <100 files.
        # If user explicitly asked for ProcessPoolExecutor, I should implement it carefully.
        
        # To make it work with ProcessPoolExecutor on Windows:
        # The worker function must be picklable (top-level). 
        # So I will move the worker logic outside or use a trick.
        
        # For simplicity and robustness in this tool call, I'll use sequential processing first 
        # unless files > 100. Or I can define the function globally in this file.
        pass # see below implementation in global scope

def find_header_row(filepath, lookup_map, max_scan_rows=20, sheet_name=0):
    """
    Scans the first N rows to find the most likely header row 
    based on the number of matching columns in lookup_map.
    """
    try:
        engine = 'openpyxl'
        if filepath.lower().endswith('.xls'):
            engine = 'xlrd'
            
        # Read headerless
        df_scan = pd.read_excel(filepath, sheet_name=sheet_name, engine=engine, header=None, nrows=max_scan_rows, dtype=str)
        
        best_row = 0
        max_matches = 0
        
        for i, row in df_scan.iterrows():
            row_values = [str(x).strip().upper() for x in row.values]
            matches = 0
            for alias in lookup_map.keys():
                if alias in row_values:
                    matches += 1
            
            # Heuristic: If we find > 2 matches, it's a strong candidate. 
            # We want the one with MAX matches.
            if matches > max_matches:
                max_matches = matches
                best_row = i
        
        # If we found reasonable matches, use that row. Otherwise default to 0.
        if max_matches >= 2:
            return best_row
        return 0
        
    except Exception as e:
        logger.warning(f"Failed to scan headers for {os.path.basename(filepath)}: {e}")
        return 0

def read_excel_robust(filepath, sheet_name, header_row=None, lookup_map=None):
    """
    Attempts to read Excel sheet using pandas. 
    If it fails (e.g. openpyxl validation error), falls back to manual openpyxl read-only iteration.
    """
    is_xls = filepath.lower().endswith('.xls')
    engine = 'xlrd' if is_xls else 'openpyxl'
    
    try:
        # Standard Read
        return pd.read_excel(filepath, sheet_name=sheet_name, engine=engine, header=header_row, dtype=str)
    except Exception as e:
        logger.warning(f"Standard read failed for {os.path.basename(filepath)} sheet {sheet_name}: {e}. Attempting robust fallback.")
        
        # Fallback: Manual Openpyxl Read-Only (ONLY for .xlsx)
        if is_xls:
            logger.error("Cannot perform openpyxl robust fallback on .xls file.")
            return None
            
        try:
            wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
            if sheet_name not in wb.sheetnames:
                return None
            ws = wb[sheet_name]
            iterator = ws.values
            
            # 1. Header Detection (Manual)
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
                    # row is a tuple
                    row_strs = [str(x).strip().upper() for x in row if x is not None]
                    matches = 0
                    for alias in lookup_map.keys():
                        if alias in row_strs:
                            matches += 1
                    if matches > max_matches:
                        max_matches = matches
                        best_idx = i
            
            # Start rows list with the header
            headers = potential_headers[best_idx]
            
            # Add buffered rows after header
            rows = [headers] + potential_headers[best_idx+1:]
            
            # 2. Iterate remaining rows safely
            error_count = 0
            while True:
                try:
                    row = next(iterator)
                    rows.append(row)
                except StopIteration:
                    break
                except Exception as e:
                    error_count += 1
                    # Fatal error for this row/stream, try to break or continue?
                    # Usually openpyxl iterator errors are fatal for the stream.
                    break
            
            if len(rows) > 1:
                logger.info(f"Robust recovery: {len(rows)-1} rows from {sheet_name}. Errors: {error_count}")
                return pd.DataFrame(rows[1:], columns=rows[0])
            return None

        except Exception as fallback_e:
            logger.error(f"Robust fallback failed: {fallback_e}")
            return None

# --- Global Worker for ProcessPool ---
def _worker(args):
    filepath, worker_config = args

    lookup_map = worker_config['lookup_map']
    target_destinations = worker_config['target_destinations']
    exclude_delivery_keywords = worker_config.get('exclude_delivery_keywords', [])
    required_keys = list(worker_config['column_mapping'].keys())


    filename = os.path.basename(filepath)
    filename_no_ext = os.path.splitext(filename)[0]
    
    try:
        is_xls = filepath.lower().endswith('.xls')
        engine = 'xlrd' if is_xls else 'openpyxl'
        
        if is_xls:
             # Use pandas to get sheet names for xls, as openpyxl fails
             xl_file = pd.ExcelFile(filepath, engine='xlrd')
             sheet_names = xl_file.sheet_names
        else:
             xl = pd.ExcelFile(filepath, engine='openpyxl')
             sheet_names = xl.sheet_names
             
        valid_dfs = []
        
        for sheet in sheet_names:
            try:
                # 1. Dynamic Header Detection per sheet
                header_row = find_header_row(filepath, lookup_map, sheet_name=sheet)
                
                # 2. Read with detected header
                # dtype=str to preserve IDs, but we will convert metrics later
                # Use robust reader
                df = read_excel_robust(filepath, sheet_name=sheet, header_row=header_row, lookup_map=lookup_map)
                
                if df is None:
                    continue
                
                # 3. Standardize Headers
                new_columns = {}
                for col in df.columns:
                    col_clean = str(col).strip().upper()
                    if col_clean in lookup_map:
                        new_columns[col] = lookup_map[col_clean]
                df = df.rename(columns=new_columns)
                
                # Check for duplicate columns (e.g. multiple aliases mapped to same target)
                if df.columns.duplicated().any():
                    logger.warning(f"{filename} Sheet={sheet}: Duplicate columns found: {df.columns[df.columns.duplicated()].tolist()}. Keeping first.")
                    df = df.loc[:, ~df.columns.duplicated()]
                
                # 4. Filter empty/noise columns if needed, check requirements
                available_cols = [c for c in required_keys if c in df.columns]
                if not available_cols:
                    continue
                    
                df = df[available_cols]
                
                # 5. Type Conversion for Metrics
                if 'BOX_COUNT' in df.columns:
                    df['BOX_COUNT'] = pd.to_numeric(df['BOX_COUNT'], errors='coerce').fillna(0)
                    
                if 'WEIGHT_KG' in df.columns:
                    df['WEIGHT_KG'] = pd.to_numeric(df['WEIGHT_KG'], errors='coerce').fillna(0)

                # Heuristic: Remove "Total" row if present (Sum == 2 * Max)
                # This handles cases where a summary row exists and gets captured (often with ffilled destination)
                if 'BOX_COUNT' in df.columns and len(df) > 2:
                    boxes = df['BOX_COUNT']
                    total_box = boxes.sum()
                    max_box = boxes.max()
                    
                    if total_box > 0 and max_box > 0:
                        # Check if Total is ~ 2 * Max (allow small float error)
                        if abs(total_box - 2 * max_box) < 0.1:
                            logger.info(f"Sheet {sheet} in {filename}: Detected 'Total' row with {max_box} boxes. Removing it.")
                            
                            # Remove the row(s) with max_box
                            # Use logic to remove only if looks like total? (e.g. check duplicate maxes?)
                            # Usually Total row is unique or last. 
                            # Safe approach: Remove ALL rows matching max_box? 
                            # Risky if a real shipment equals the total (impossible). 
                            # If a real shipment equals the SUM of all others? (Total = 2 * Max).
                            # If valid rows: [100, 100]. Sum=200. Max=100. Total=2*Max.
                            # Should NOT remove.
                            # So logic "Total == 2 * Max" ONLY holds if there is a SEPARATE Total row.
                            # If [100, 100, 200]. Sum=400. Max=200. Total=2*Max. Remove 200. Correct.
                            # If [100, 100]. Sum=200. Max=100. Total=2*Max. Remove 100? NO.
                            # We should remove ONLY if there is ONE max value?
                            # Or if the max value appears once?
                            
                            max_rows = df[df['BOX_COUNT'] == max_box]
                            if len(max_rows) == 1:
                                df = df[df['BOX_COUNT'] != max_box]
                            else:
                                logger.warning(f"Sheet {sheet}: Ambiguous Total row (Max appears {len(max_rows)} times). Skipping removal.")
    
            # 6. Clean MISCELLANEOUS_NOTES if present
                if 'MISCELLANEOUS_NOTES' in df.columns:
                    df['MISCELLANEOUS_NOTES'] = df['MISCELLANEOUS_NOTES'].astype(str)
                    df['MISCELLANEOUS_NOTES'] = df['MISCELLANEOUS_NOTES'].replace({'nan': '', 'None': ''})
                    df['MISCELLANEOUS_NOTES'] = df['MISCELLANEOUS_NOTES'].str.strip()
    
                # 6. Filter by Destination
                if 'DESTINATION_FC' in df.columns and target_destinations is not None:
                    count_before = len(df)
                    # Handle Merged Cells: Forward Fill destination values
                    df['DESTINATION_FC'] = df['DESTINATION_FC'].ffill()
                    
                    df['DESTINATION_FC'] = df['DESTINATION_FC'].astype(str).str.strip().str.upper()
                    
                    # Partial Match Logic
                    def is_valid_dest(val):
                        for target in target_destinations:
                            if target in val:
                                return True
                        return False
                        
                    df = df[df['DESTINATION_FC'].apply(is_valid_dest)]
                    
                # 7. Filter by Delivery Method (Exclude UPS/Courier)
                if 'DELIVERY_METHOD' in df.columns and exclude_delivery_keywords:
                    def is_not_ups(val):
                        s = str(val).upper()
                        return not any(k in s for k in exclude_delivery_keywords)
                    
                    df = df[df['DELIVERY_METHOD'].apply(is_not_ups)]

                if df.empty:
                    continue

                valid_dfs.append((sheet, df))
                
            except Exception as e:
                logger.warning(f"Error processing sheet {sheet} in {filename}: {e}")
                continue

        if not valid_dfs:
            return None
            
        # --- Sheet Prioritization Logic ---
        # 1. Check for high priority (East Coast specific for Canada warehouse targets)
        priority_keywords = ["EAST", "加东", "LTL"]
        
        # 2. Check for secondary priority (General truck/loading plan keywords)
        secondary_keywords = ["TRUCK", "卡派", "卡车", "UNLOADING", "清单", "PLAN"]

        # Filter valid_dfs to identify which ones match which priority
        high_priority_matches = []
        secondary_priority_matches = []
        
        for s, df in valid_dfs:
            s_upper = str(s).upper()
            if any(pk in s_upper for pk in priority_keywords):
                high_priority_matches.append(df)
            elif any(sk in s_upper for sk in secondary_keywords):
                secondary_priority_matches.append(df)
        
        final_dfs = []
        if high_priority_matches:
            logger.info(f"File {filename}: High priority sheets found. Selecting them.")
            final_dfs = high_priority_matches
        elif secondary_priority_matches:
            logger.info(f"File {filename}: Secondary priority sheets found. Selecting them.")
            final_dfs = secondary_priority_matches
        else:
            # Fallback: Select ONLY the first valid sheet to avoid noise like "Sheet2"
            if valid_dfs:
                s_name, df = valid_dfs[0]
                logger.info(f"File {filename}: No priority match. Selecting first valid sheet: {s_name}")
                final_dfs = [df]
            
        if not final_dfs:
            return None
            
        final_df = pd.concat(final_dfs, ignore_index=True)
        final_df['SOURCE_FILE'] = filename_no_ext
        return final_df
        
    except Exception as e:
        # print(f"Error {filename}: {e}")
        return None

def run_consolidation(input_dir, output_file, config_path=None, include_ups=False, target_destinations_override=None):
    pipeline = ConsolidationPipeline(config_path)
    
    # Get config for workers
    worker_config = pipeline.get_effective_config(include_ups, target_destinations_override)
    
    all_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.xlsx', '.xls')):
                # Exclude temp files and the output file itself
                if file.startswith('~$') or file == os.path.basename(output_file) or 'Master_Consolidated' in file:
                    continue
                all_files.append(os.path.join(root, file))
                
    if not all_files:
        logger.warning(f"No files found in {input_dir}")
        return
        
    logger.info(f"Processing {len(all_files)} files...")
    
    logger.info(f"Processing {len(all_files)} files...")
    
    # Prepare args for worker
    worker_args = [
        (f, worker_config) 
        for f in all_files
    ]
    
    clean_frames = []
    with ProcessPoolExecutor() as executor:
        results = executor.map(_worker, worker_args)
        for res in results:
            if res is not None and not res.empty:
                clean_frames.append(res)
                
    if clean_frames:
        logger.info("Merging datasets...")
        master_df = pd.concat(clean_frames, ignore_index=True)
        
        # Final Format Polish
        # Use configured output columns or default if missing
        cols_order = pipeline.config.get('processing', {}).get('output_columns', [
            'SOURCE_FILE', 'FBA_ID', 'PO_NUMBER', 'DESTINATION_FC', 'DELIVERY_METHOD', 'BOX_COUNT', 'WEIGHT_KG'
        ])
        
        # Ensure we only ask for columns that actually exist in our data
        final_cols = []
        for c in cols_order:
            if c in master_df.columns:
                final_cols.append(c)
            # Optional: We could add missing columns with empty values if strict adherence is required,
            # but for now, we just skip them to avoid KeyErrors.
            
        master_df = master_df[final_cols]
        
        master_df.to_excel(output_file, index=False)
        logger.info(f"SUCCESS: Consolidated {len(master_df)} rows into {output_file}")
        return True
    else:
        logger.warning("No matching data found in files after processing.")
        return False
