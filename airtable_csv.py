import os
from airtable import Airtable
import csv
import io
import json
from typing import Optional
from sqlite_storage import SQLiteStorage

class AirtableCSVManager:
    def __init__(self, base_id, table_name, api_key, sqlite_storage: Optional[SQLiteStorage] = None):
        self.base_id = base_id
        self.table_name = table_name
        self.api_key = api_key
        self.sqlite_storage = sqlite_storage

    # Fetch data from Airtable and store in SQLite using csv writer
    def update_csv_from_airtable(self):
        airtable = Airtable(self.base_id, self.table_name, self.api_key)
        records = airtable.get_all()
        if not records:
            return None

        fieldnames = set()
        for record in records:
            fieldnames.update(record['fields'].keys())
        fieldnames = list(fieldnames)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            # Ensure row doesnt have a comma
            record = self.record_comma_check(record)
            # Write the record to CSV
            writer.writerow(record['fields'])

        csv_data = output.getvalue()
        output.close()

        # Store in SQLite only
        if self.sqlite_storage:
            self.sqlite_storage.import_csv_rows(self.table_name, csv_data)

        return f"Successfully updated DB from Airtable for table {self.table_name}."


    def get_row(self, column_containing_reference: str, reference_value: str):
        if self.sqlite_storage:
            return self.sqlite_storage.find_row_by_column(self.table_name, column_containing_reference, reference_value)
        return None

    def get_value_by_row_and_column(self, column_containing_reference: str, reference_value: str, target_column: str):
        if self.sqlite_storage:
            return self.sqlite_storage.find_value_by_row_and_column(self.table_name, column_containing_reference, reference_value, target_column)
        return None

    def execute_sql_query(self, sql_query: str):
        """
        Execute an arbitrary SQL query on this table using the SQLite backend.
        Returns a list of dicts (rows) or None if not available.
        """
        if self.sqlite_storage:
            return self.sqlite_storage.execute_sql_query(self.table_name, sql_query)
        return None

    @staticmethod
    def record_comma_check(record) -> bool:
        """
        Check if the CSV data contains commas in any field.
        Wraps fields with commas in double quotes.
        """
        for key in record['fields']:
            if isinstance(record['fields'][key], str):
                if ',' in record['fields'][key]:
                    # Wrap in double quotes to handle commas
                    record['fields'][key] = record['fields'][key].replace('"', '""')
        return record