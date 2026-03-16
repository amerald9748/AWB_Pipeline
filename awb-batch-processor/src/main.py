import sys
import os
import argparse
import logging
import csv
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add project root and src to path to ensure modules can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, project_root)

from nutcloud.pipeline import process_awb
from nutcloud.pipeline import process_awb
from consolidation import run_consolidation


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def smart_cleanup(output_dir, allowed_awbs):
    """
    Removes files in output_dir that do not correspond to any AWB in allowed_awbs.
    Preserves Master_Consolidated_FBA.xlsx.
    """
    if not os.path.exists(output_dir):
         return
         
    logger.info(f"Performing Smart Cleanup in {output_dir}...")
    allowed_set = set(str(a).strip() for a in allowed_awbs)
    
    deleted_count = 0
    for filename in os.listdir(output_dir):
        # Skip Master File
        if "Master_Consolidated" in filename:
            continue
            
        file_path = os.path.join(output_dir, filename)
        if not os.path.isfile(file_path):
            continue
            
        # Check if file matches any allowed AWB
        # Pipeline names files as {AWB}.xlsx
        name_no_ext = os.path.splitext(filename)[0]
        
        if name_no_ext not in allowed_set:
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Could not delete {filename}: {e}")
                
    logger.info(f"Cleanup complete. Removed {deleted_count} files.")

def process_batch(file_path: str, output_dir: str):
    """
    Process a batch of AWBs from a text file.
    """
    if not os.path.exists(file_path):
        logger.error(f"Input file not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        awbs = [line.strip() for line in f if line.strip()]

    total = len(awbs)
    
    # Smart Cleanup
    smart_cleanup(output_dir, awbs)
    
    logger.info(f"Starting batch processing for {total} AWBs...")
    logger.info(f"Input file: {file_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("-" * 40)

    results = []
    
    for i, awb in enumerate(awbs, 1):
        logger.info(f"[{i}/{total}] Processing AWB: {awb}")
        try:
            result = process_awb(awb, output_dir)
            
            # Ensure result is a dict
            if isinstance(result, bool):
                 result = {
                     'success': result, 
                     'file': None, 
                     'error': "Legacy boolean return" if not result else None
                 }
                 
            results.append({
                'AWB': awb,
                'Success': result.get('success', False),
                'File': result.get('file', 'N/A'),
                'Error': result.get('error', '')
            })
        except Exception as e:
            logger.error(f"Error processing AWB {awb}: {e}")
            results.append({
                'AWB': awb,
                'Success': False,
                'File': 'N/A',
                'Error': str(e)
            })



    logger.info("Batch processing phase completed.")
    return True

def main():
    parser = argparse.ArgumentParser(description="NutCloud Grey Hat API Client & Consolidator")
    
    # Input group: either single AWB, file list, or just consolidation
    group = parser.add_mutually_exclusive_group()
    group.add_argument("awb", nargs='?', help="Single AWB Number to search and download")
    
    # Load settings from .env with fallback defaults
    default_input = os.getenv("INPUT_LIST_PATH", "batch_input.txt")
    default_output = os.getenv("OUTPUT_DIR", "./output")
    
    parser.add_argument("-f", "--file", default=default_input, help=f"Path to text file containing list of AWBs (default: {default_input})")
    parser.add_argument("--output", default=default_output, help=f"Output directory (default: {default_output}) for downloads")
    
    # Consolidation args
    parser.add_argument("--consolidate", action="store_true", help="Run consolidation after processing (or alone if no AWB input provided)")
    parser.add_argument("--consolidate_output", default="Master_Consolidated_FBA.xlsx", help="Filename for consolidated report")
    
    # Filtering args
    parser.add_argument("--include-ups", action="store_true", help="Include UPS/Courier shipments (default: Exclude)")
    parser.add_argument("--destinations", help="Comma-separated list of warehouses to include (e.g. 'YYZ4,YOW3') or 'ALL'")

    args = parser.parse_args()
    
    # 1. Processing Phase
    processed_any = False
    if args.file:
        success = process_batch(args.file, args.output)
        processed_any = True
    if args.awb:
        logger.info("=" * 40)
        logger.info(f"Starting pipeline for single AWB: {args.awb}")
        logger.info(f"Output directory: {args.output}")
        logger.info("=" * 40)
        
        result = process_awb(args.awb, args.output)
        
        success = result.get('success') if isinstance(result, dict) else result
        
        if success:
            print("Pipeline completed successfully.")
            if isinstance(result, dict) and result.get('file'):
                 print(f"File saved to: {result['file']}")
        else:
            print("Pipeline failed.")
            if isinstance(result, dict) and result.get('error'):
                 print(f"Error: {result['error']}")
        processed_any = True
    
    # 2. Consolidation Phase
    if args.consolidate:
        # If we didn't process any files but consolidate is requested, we just run consolidation on the output dir
        # If we DID process files, we also run consolidation on that updated dir
        
        # Determine strict input directory for consolidation
        # If user processed files, we assume they want to consolidate the RESULTS (args.output)
        # If user just ran --consolidate, they must ensure args.output has files.
        con_input = args.output
        con_output = os.path.join(args.output, args.consolidate_output)
        
        print(f"Starting consolidation in {con_input} -> {con_output}")
        
        # Parse destinations list
        dest_list = None
        if args.destinations:
            if args.destinations.strip().upper() == 'ALL':
                dest_list = 'ALL'
            else:
                dest_list = [d.strip().upper() for d in args.destinations.split(',') if d.strip()]

        if run_consolidation(con_input, con_output, include_ups=args.include_ups, target_destinations_override=dest_list):
            print("Consolidation finished.")
        else:
            print("Consolidation finished with potential warnings or empty result.")
            
    if not processed_any and not args.consolidate:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
