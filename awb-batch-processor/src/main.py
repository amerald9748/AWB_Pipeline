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
