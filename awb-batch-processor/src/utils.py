
import os
import tempfile
import logging

CUSTOMER_CODE_TO_AWB_MAP = {
    "JH": "加海",
    "JJT": "加境通",
    "JHT": "聚货通",
    "JY": "聚友",
    "LY": "联宇劲港",
    "MJ": "千亚麦佳",
    "AG": "深圳安圭(AG)",
    "SZBDT": "深圳八达通",
    "DDD": "深圳滴答滴",
    "FHL": "深圳丰货囵(FHL)",
    "HPLT": "深圳皓鹏(HPLT)",
    "HPAT": "深圳皓鹏(HPLT)",
    "KQ": "深圳凯琦",
    "LX": "深圳陆行(LX)",
    "YM": "深圳英美",
    "MQ": "美琦",
    "MT": "深圳美通(MT)",
    "TT": "天图"
}

def get_logger(name: str, log_file: str, level=logging.DEBUG):
    """
    Creates and configures a logger.

    Args:
        name: The name of the logger.
        log_file: The file to write logs to.
        level: The logging level.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(log_file)
    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger

def check_read_write_permissions(directory: str) -> bool:
    """
    Checks if the script has read and write permissions for a given directory.

    Args:
        directory: The directory to check.

    Returns:
        True if permissions are granted, False otherwise.
    """
    try:
        # Create a temporary file in the specified directory
        temp_file_path = os.path.join(directory, "temp_permission_test.tmp")
        with open(temp_file_path, "w") as f:
            f.write("test")

        # Read from the temporary file
        with open(temp_file_path, "r") as f:
            content = f.read()

        # Clean up the temporary file
        os.remove(temp_file_path)

        return content == "test"
    except (IOError, OSError):
        return False

def parse_aggregated_info(aggregated_string: str) -> dict:
    """
    Splits an aggregated information string into customer code and AWB.

    Args:
        aggregated_string: A string in the format "CUSTOMER_CODE-AWB-DB_ID".

    Returns:
        A dictionary with "customer_code" and "awb" as keys.
    """
    parts = aggregated_string.rsplit('-', 2) # Split by the last two hyphens
    
    if len(parts) == 3:
        customer_code = parts[0]
        awb = parts[1]
        # db_id = parts[2] # Not needed for return
    elif len(parts) == 2: # Case where there might be no customer code or AWB is missing
        customer_code = parts[0]
        awb = parts[1]
    else: # Fallback for unexpected formats
        customer_code = aggregated_string
        awb = "" # Or handle as error/None
        
    return {"customer_code": customer_code, "awb": awb}
