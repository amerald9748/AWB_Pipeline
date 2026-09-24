# AWB_Pipeline
Starting with some AWB codes, grab their corresponding container FBA product information (stored in a Nutcloud database) and perform ETL to host them in a google sheet for a subsequent step.

## Currently Achieved Functions
- **Nutcloud Integration**: Successfully connects to Nutcloud via session cookies to search, browse, and download AWB Excel files (`src/nutcloud/client.py`).
- **Batch Processing**: A CLI tool (`src/main.py`) processes single or batch lists of AWBs, handling downloads and caching intelligently (`smart_cleanup`).
- **Data Consolidation**: Merges and cleans downloaded Excel files into a `Master_Consolidated_FBA.xlsx` file, applying intelligent heuristics to find header rows and filter by destination FC and delivery methods (`src/consolidation.py`).
- **Delivery Analysis**: Analyzes the consolidated data for delivery methods (e.g., Truck vs UPS) and aggregates box counts (`src/analyze_delivery.py`).
