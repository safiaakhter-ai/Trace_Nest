"""Tests for TraceNest's database and CSV export functions."""

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
from export_alerts import write_alerts_csv


class TestAlertStorage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.data_dir = Path(self.temp_dir.name)
        patcher = patch.object(database, "_data_directory", return_value=self.data_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_saved_alert_can_be_read_back(self):
        database.initialize_database()
        database.log_event("CPU", "WARNING", "High CPU usage detected: 91.0%")
        rows = database.get_alert_history()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1:], ("WARNING", "High CPU usage detected: 91.0%"))
        self.assertTrue(database.database_path().exists())

    def test_history_limit(self):
        for n in range(3):
            database.log_event("RAM", "WARNING", f"Test alert {n}")
        self.assertEqual(len(database.get_alert_history(limit=2)), 2)

    def test_export_creates_utf8_csv(self):
        output_path = self.data_dir / "alerts.csv"
        rows = [("2026-10-18 12:34:56", "WARNING", "High CPU usage: 91%")]
        count = write_alerts_csv(output_path, rows)
        self.assertEqual(count, 1)
        with output_path.open("r", encoding="utf-8-sig", newline="") as handle:
            data = list(csv.reader(handle))
        self.assertEqual(data[0], ["Time", "Severity", "Alert Message"])
        self.assertEqual(data[1], list(rows[0]))


if __name__ == "__main__":
    unittest.main()
