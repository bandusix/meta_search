
from exporters.csv_exporter import CSVExporter

try:
    exporter = CSVExporter(db_path='spider_v2.db')
    exporter.export_all(export_type='full')
except Exception as e:
    print(f"Export failed: {e}")
