"""Unit tests for the export module."""

import os
import tempfile
import unittest
import csv
import io
import json

import phone_log
import export


class TestExportBase(unittest.TestCase):
    """Base class for export tests with common setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.db = self.tmp.name
        
        # Add sample data
        phone_log.add_call("Alice", "555-1111", "incoming", 120, "Test note", data_file=self.db)
        phone_log.add_call("Bob", "555-2222", "outgoing", 60, data_file=self.db)
        phone_log.add_call("Charlie", "555-3333", "missed", None, data_file=self.db)

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.db):
            os.unlink(self.db)


class TestExportToCSV(TestExportBase):
    """Tests for export_to_csv function."""

    def test_returns_string(self):
        result = export.export_to_csv(data_file=self.db)
        self.assertIsInstance(result, str)

    def test_has_header(self):
        result = export.export_to_csv(data_file=self.db)
        lines = result.strip().split('\n')
        header = lines[0]
        self.assertIn("id", header)
        self.assertIn("contact_name", header)
        self.assertIn("phone_number", header)
        self.assertIn("direction", header)

    def test_has_data_rows(self):
        result = export.export_to_csv(data_file=self.db)
        lines = result.strip().split('\n')
        # Header + 3 data rows
        self.assertEqual(len(lines), 4)

    def test_includes_notes(self):
        result = export.export_to_csv(data_file=self.db, include_notes=True)
        self.assertIn("notes", result)
        self.assertIn("Test note", result)

    def test_excludes_notes(self):
        result = export.export_to_csv(data_file=self.db, include_notes=False)
        header = result.split('\n')[0]
        self.assertNotIn("notes", header)

    def test_csv_parseable(self):
        result = export.export_to_csv(data_file=self.db)
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        self.assertEqual(len(rows), 3)

    def test_custom_calls_list(self):
        calls = [{"id": 1, "contact_name": "Test", "phone_number": "111", 
                  "direction": "incoming", "timestamp": "2024-01-01", "duration_seconds": 30}]
        result = export.export_to_csv(calls=calls)
        self.assertIn("Test", result)


class TestExportToJSON(TestExportBase):
    """Tests for export_to_json function."""

    def test_returns_string(self):
        result = export.export_to_json(data_file=self.db)
        self.assertIsInstance(result, str)

    def test_valid_json(self):
        result = export.export_to_json(data_file=self.db)
        data = json.loads(result)
        self.assertIn("calls", data)
        self.assertIn("total_records", data)
        self.assertIn("exported_at", data)

    def test_has_correct_count(self):
        result = export.export_to_json(data_file=self.db)
        data = json.loads(result)
        self.assertEqual(data["total_records"], 3)
        self.assertEqual(len(data["calls"]), 3)

    def test_pretty_format(self):
        result = export.export_to_json(data_file=self.db, pretty=True)
        self.assertIn("\n", result)  # Has newlines

    def test_compact_format(self):
        result = export.export_to_json(data_file=self.db, pretty=False)
        lines = result.strip().split('\n')
        self.assertEqual(len(lines), 1)  # Single line


class TestExportToHTML(TestExportBase):
    """Tests for export_to_html function."""

    def test_returns_string(self):
        result = export.export_to_html(data_file=self.db)
        self.assertIsInstance(result, str)

    def test_valid_html_structure(self):
        result = export.export_to_html(data_file=self.db)
        self.assertIn("<!DOCTYPE html>", result)
        self.assertIn("<html", result)
        self.assertIn("</html>", result)
        self.assertIn("<table>", result)
        self.assertIn("</table>", result)

    def test_contains_data(self):
        result = export.export_to_html(data_file=self.db)
        self.assertIn("Alice", result)
        self.assertIn("Bob", result)
        self.assertIn("555-1111", result)

    def test_custom_title(self):
        result = export.export_to_html(data_file=self.db, title="My Custom Report")
        self.assertIn("My Custom Report", result)

    def test_has_styling(self):
        result = export.export_to_html(data_file=self.db)
        self.assertIn("<style>", result)
        self.assertIn("</style>", result)


class TestGenerateSummaryReport(TestExportBase):
    """Tests for generate_summary_report function."""

    def test_returns_string(self):
        result = export.generate_summary_report(self.db)
        self.assertIsInstance(result, str)

    def test_contains_statistics(self):
        result = export.generate_summary_report(self.db)
        self.assertIn("Total Calls", result)
        self.assertIn("Incoming", result)
        self.assertIn("Outgoing", result)
        self.assertIn("Missed", result)

    def test_contains_top_contacts(self):
        result = export.generate_summary_report(self.db)
        self.assertIn("TOP CONTACTS", result)
        self.assertIn("Alice", result)

    def test_empty_log_message(self):
        # Remove all calls
        os.unlink(self.db)
        result = export.generate_summary_report(self.db)
        self.assertIn("No call records found", result)


class TestImportFromCSV(TestExportBase):
    """Tests for import_from_csv function."""

    def setUp(self):
        """Set up with empty database."""
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.db = self.tmp.name

    def test_basic_import(self):
        csv_content = """contact_name,phone_number,direction
Alice,555-1111,incoming
Bob,555-2222,outgoing"""
        
        result = export.import_from_csv(csv_content, self.db)
        
        self.assertEqual(result["imported"], 2)
        self.assertEqual(result["total_errors"], 0)

    def test_import_with_notes(self):
        csv_content = """contact_name,phone_number,direction,notes
Alice,555-1111,incoming,Test note"""
        
        export.import_from_csv(csv_content, self.db)
        calls = phone_log.get_all(self.db)
        
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["notes"], "Test note")

    def test_import_with_duration(self):
        csv_content = """contact_name,phone_number,direction,duration_seconds
Alice,555-1111,incoming,120"""
        
        export.import_from_csv(csv_content, self.db)
        calls = phone_log.get_all(self.db)
        
        self.assertEqual(calls[0]["duration_seconds"], 120)

    def test_import_missing_fields(self):
        csv_content = """contact_name,phone_number
Alice,555-1111"""
        
        result = export.import_from_csv(csv_content, self.db)
        
        self.assertEqual(result["imported"], 0)
        self.assertEqual(result["total_errors"], 1)

    def test_import_invalid_direction(self):
        csv_content = """contact_name,phone_number,direction
Alice,555-1111,invalid"""
        
        result = export.import_from_csv(csv_content, self.db)
        
        self.assertEqual(result["total_errors"], 1)


class TestExportImportRoundTrip(TestExportBase):
    """Tests for exporting and re-importing data."""

    def test_csv_roundtrip(self):
        # Export current data
        csv_content = export.export_to_csv(data_file=self.db)
        
        # Create new database
        tmp2 = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp2.close()
        os.unlink(tmp2.name)
        
        try:
            # Import into new database
            result = export.import_from_csv(csv_content, tmp2.name)
            
            # Verify counts match
            original = phone_log.get_all(self.db)
            imported = phone_log.get_all(tmp2.name)
            
            self.assertEqual(len(imported), len(original))
        finally:
            if os.path.exists(tmp2.name):
                os.unlink(tmp2.name)


if __name__ == "__main__":
    unittest.main()
