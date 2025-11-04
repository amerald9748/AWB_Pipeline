# Project Setup: AWB Batch Processor

## Project Overview
Create a comprehensive system for batch searching, downloading, and manipulating Air Way Bill (AWB) files and their corresponding Excel unloading plans. This system should handle multiple AWB formats, extract shipment data, perform accurate counting/aggregation, and generate reports.

## Project Context
### Business Domain
- **Industry**: Freight forwarding and logistics
- **Primary Use Case**: Processing unloading plans for Amazon FBA shipments
- **Data Source**: Local file system containing AWB folders with Excel manifests
- **Key Challenge**: Accurate counting and aggregation of shipment data across multiple warehouses

### AWB Format Standards
AWBs can appear in several formats:
- **Standard format**: MATU4631210, MATU4584485
- **Dash format**: 999-36253372
- **Customer number format**: FHL151-160

### File Structure
- **Base Path**: `D:\UnloadingPlans\拾谷SAGSC\Amazon\拾谷\`
- **File Types**: .xlsx, .xls, .zip (zipped folders)
- **Typical Folder Structure**: AWB folders contain manifests with shipment details

### Data Structure in Excel Files
Excel manifests typically contain:
- **运单号** (Tracking Number): Unique shipment identifier
- **客户单号** (Customer Order Number)
- **扩展单号** (Extended Number/FBA Shipment ID)
- **仓库代码** (Warehouse Code): e.g., YOW3, YXU1, YYZ4, YYZ7, YYZ9, YOO1, XYY1
- **PO Number**: Purchase order reference (sometimes missing)
- **收件人国家** (Recipient Country): Usually "CA" for Canada
- **件数** (Number of Cartons/Boxes)
- **实际重量(KG)** (Actual Weight in KG)
- **材积重** (Volumetric Weight)
- **体积(m³)** (Volume in cubic meters)

Manifests often have multiple sheets (e.g., "卡派" for truck dispatch, "UPS" for courier)

## Technical Requirements
### 1. Project Initialization
Create a Python project with the following structure:
```
awb-batch-processor/
├── config/
│   ├── settings.json          # Configuration file
│   └── mcp_servers.json        # MCP server configurations
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── awb_search.py           # AWB file search logic
│   ├── excel_processor.py      # Excel data extraction
│   ├── aggregator.py           # Data aggregation and counting
│   ├── reporter.py             # Report generation
│   └── utils.py                # Utility functions
├── data/
│   ├── input/                  # Input AWB lists
│   └── output/                 # Generated reports
├── logs/                       # Application logs
├── tests/                      # Unit tests
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
└── .gitignore
```

### 2. Configuration File (`config/settings.json`)
```json
{
  "project_info": {
    "name": "AWB Batch Processor",
    "version": "1.0.0",
    "description": "Automated system for searching, processing, and analyzing AWB unloading plans"
  },
  "paths": {
    "base_search_path": "D:\\UnloadingPlans\\拾谷SAGSC\\Amazon\\拾谷\",
    "input_directory": "./data/input",
    "output_directory": "./data/output",
    "log_directory": "./logs"
  },
  "file_patterns": {
    "excel_extensions": [".xlsx", ".xls"],
    "archive_extensions": [".zip"],
    "manifest_keywords": ["清单", "manifest", "list"]
  },
  "awb_formats": {
    "standard": "^[A-Z]{4}\d{7}$",
    "dash_format": "^\d{3}-\d{8}$",
    "customer_format": "^[A-Z]{3}\d{3}-\d{3}$"
  },
  "excel_columns": {
    "tracking_number": "运单号",
    "customer_order": "客户单号",
    "fba_shipment_id": "扩展单号",
    "warehouse_code": "仓库代码",
    "po_number": "PO Number",
    "country": "收件人国家",
    "carton_count": "件数",
    "actual_weight": "实际重量(KG)",
    "volumetric_weight": "材积重",
    "volume": "体积(m³)"
  },
  "warehouses": {
    "target_warehouses": ["YOW3", "YXU1", "YYZ4", "YYZ7", "YYZ9", "YOO1", "XYY1"],
    "primary_warehouse": "YOW3"
  },
  "processing": {
    "skip_empty_po": false,
    "validate_totals": true,
    "generate_summary": true,
    "export_format": "xlsx"
  },
  "reporting": {
    "include_missing_po": true,
    "include_warehouse_breakdown": true,
    "include_weight_analysis": true,
    "include_validation_errors": true
  }
}
```

### 3. MCP Server Configuration (`config/mcp_servers.json`)
```json
{
  "mcp_servers": {
    "excel_csv_mcp": {
      "name": "Excel/CSV MCP Server",
      "author": "ishayoyo",
      "repository": "https://github.com/ishayoyo/excel-mcp",
      "purpose": "Primary server for Excel data analysis with built-in COUNT, SUM, AVG operations",
      "features": [
        "Built-in analytics (SUM, AVG, COUNT, MIN, MAX)",
        "Advanced filtering with conditions",
        "Statistical analysis",
        "Optimized for large datasets",
        "Multi-format support (CSV, XLSX, XLS)"
      ],
      "installation": "npm install -g excel-csv-mcp",
      "priority": 1
    },
    "excel_mcp_server": {
      "name": "Excel MCP Server",
      "author": "haris-musa",
      "repository": "https://github.com/haris-musa/excel-mcp-server",
      "purpose": "Backup server for Excel manipulation and pivot table operations",
      "features": [
        "Pivot tables and data analysis",
        "Chart creation",
        "Advanced filtering",
        "Robust error handling"
      ],
      "installation": "npm install -g excel-mcp-server",
      "priority": 2
    },
    "everything_search_mcp": {
      "name": "Everything Search MCP",
      "author": "Built-in",
      "purpose": "Fast file system search using Everything SDK (Windows)",
      "features": [
        "Lightning-fast file search",
        "Wildcard and regex support",
        "Size and date filtering",
        "Path-based searching"
      ],
      "priority": 1
    },
    "filesystem_mcp": {
      "name": "Filesystem MCP",
      "author": "Built-in",
      "purpose": "File system operations for reading Excel files",
      "features": [
        "Read text and binary files",
        "Directory listing",
        "File metadata retrieval"
      ],
      "priority": 1
    }
  },
  "usage_notes": {
    "excel_processing": "Use excel_csv_mcp as primary for accurate counting and aggregation",
    "file_search": "Use everything_search_mcp for Windows file system searches",
    "fallback": "If excel_csv_mcp fails, fall back to excel_mcp_server",
    "validation": "Always validate count results manually for critical operations"
  }
}
```

### 4. Core Functionality Requirements
#### A. AWB Search Module (`awb_search.py`)
```python
# TODO: Implement AWB file search functionality
# - Accept list of AWBs (from CSV, Excel, or text file)
# - Use Everything MCP to search for AWB folders/files
# - Support multiple AWB format patterns (regex matching)
# - Handle Chinese characters in file paths
# - Return structured results with full file paths
# - Log search results and failures
```

#### B. Excel Processing Module (`excel_processor.py`)
```python
# TODO: Implement Excel data extraction
# - Use Excel/CSV MCP server for robust data operations
# - Identify manifest files (keywords: 清单, manifest, list)
# - Extract data from all sheets (卡派, UPS, etc.)
# - Parse column headers dynamically (handle variations)
# - Handle merged cells and empty rows
# - Extract formulas and calculated totals
# - Validate data integrity (compare manual totals with SUM formulas)
```

#### C. Data Aggregation Module (`aggregator.py`)
```python
# TODO: Implement accurate counting and aggregation
# - Count total FBA groups (shipment rows) per sheet
# - Sum carton counts across all sheets
# - Filter and count by warehouse code (e.g., YOW3)
# - Identify missing PO numbers
# - Calculate weight and volume totals
# - Cross-validate totals with Excel formulas
# - Handle edge cases (empty cells, merged rows, notes)
# - Use MCP server's built-in COUNT, SUM operations for accuracy
```

#### D. Report Generation Module (`reporter.py`)
```python
# TODO: Implement comprehensive reporting
# - Generate summary report for each AWB
# - Include warehouse-specific breakdowns
# - Highlight missing PO numbers
# - Create comparison tables (truck vs UPS)
# - Export to Excel with formatting
# - Generate batch summary for multiple AWBs
# - Include validation warnings and errors
```

### 5. Key Features to Implement
- **Batch Processing**: Accept multiple AWBs, process sequentially, and generate reports.
- **Data Validation**: Compare extracted totals with Excel formulas and flag discrepancies.
- **Error Handling**: Log failures and generate an error summary.
- **Reporting Output**: Generate detailed reports for each AWB.

### 6. Development Guidelines
- **Code Quality**: Use type hints, error handling, logging, and unit tests.
- **Performance**: Optimize for large files and use async operations.
- **Maintainability**: Follow PEP 8, use configuration files, and create modular components.

### 7. Dependencies to Include
```
# requirements.txt
openpyxl>=3.1.2
pandas>=2.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
loguru>=0.7.0
click>=8.1.0
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.0.0
flake8>=6.0.0
```

### 8. Initial TODO List
- **Phase 1**: Project Setup
- **Phase 2**: Core Development
- **Phase 3**: Reporting
- **Phase 4**: Testing & Refinement
- **Phase 5**: Documentation & Deployment

### Example Usage
```python
# Example 1: Process single AWB
from src.main import AWBProcessor

processor = AWBProcessor()
result = processor.process_awb("MATU4584485")
print(result.summary)

# Example 2: Batch process from CSV
awb_list = ["MATU4584485", "MATU4631210", "999-36253372"]
batch_results = processor.process_batch(awb_list)
processor.generate_batch_report(batch_results, "output/batch_report.xlsx")

# Example 3: Analyze specific warehouse
yow3_analysis = processor.analyze_warehouse("MATU4584485", "YOW3")
print(f"YOW3 Shipments: {yow3_analysis.fba_groups}")
print(f"YOW3 Cartons: {yow3_analysis.total_cartons}")
```

### Success Criteria
- **Accuracy**: Match manual verification.
- **Performance**: Process 10+ AWBs in under 5 minutes.
- **Reliability**: Handle 95%+ of AWB formats.
- **Usability**: Clear, actionable reports.
- **Maintainability**: Well-documented, testable code.
