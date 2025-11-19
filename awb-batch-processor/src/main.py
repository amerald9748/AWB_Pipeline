from awb_search import find_awb_file
from utils import get_logger, parse_aggregated_info

logger = get_logger(__name__, r'D:\Automation_Workspace\AWB_Pipeline\awb-batch-processor\logs\main.log')

def main():
    """
    Main function to run the AWB processing pipeline.
    """
    # List of AWBs that should definitely be found (true positives)
    # Format: "CUSTOMER_CODE-AWB-DB_ID"
    true_positives_aggregated = [
        "HPAT-250358-695-55361316-41634",
        "MJ-25-TEMU6301732-37591",
        "JJT-US25125-CAIU5824057-41866",
        "JJT-94-TIIU7556737-40603",
        "KQ-298-CCLU7412212-32915"
    ]

    # List of test AWBs (unknown if they exist)
    test_awbs_aggregated = [
        "UNKNOWN-OOCU5878901-11",
        "TT-TT-46-12",
        "AG-AGAT-250080-13", # Using AG from the map
        "HPAT-HP-1096-14", # Using HPAT from the map
        "UNKNOWN-8F5LZ250929104E-15",
        "LX-LX10166221-16", # Using LX from the map
        "HPAT-HPAT-250358-17",
        "UNKNOWN-ZIMUSHH31621387-18",
    ]

    # Process true positives first
    logger.info("Starting search for true positive AWBs...")
    for aggregated_string in true_positives_aggregated:
        pipeline_input = parse_aggregated_info(aggregated_string)
        awb = pipeline_input.get('awb')
        awb_file_paths = find_awb_file(pipeline_input)
        if awb_file_paths:
            logger.info(f"✓ Found file(s) for AWB '{awb}': {awb_file_paths}")
        else:
            logger.error(f"✗ No file found for AWB '{awb}' - THIS SHOULD NOT HAPPEN")

    logger.info("\nStarting search for test AWBs...")
    for aggregated_string in test_awbs_aggregated:
        pipeline_input = parse_aggregated_info(aggregated_string)
        awb = pipeline_input.get('awb')
        awb_file_paths = find_awb_file(pipeline_input)
        if awb_file_paths:
            logger.info(f"Found file(s) for test AWB '{awb}': {awb_file_paths}")
        else:
            logger.info(f"No file found for test AWB '{awb}'")


if __name__ == "__main__":
    main()
