"""Unit tests for the analytics module."""

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

import phone_log
import analytics


class TestAnalyticsBase(unittest.TestCase):
    """Base class for analytics tests with common setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.db = self.tmp.name

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.db):
            os.unlink(self.db)

    def _add_test_calls(self):
        """Add sample calls for testing."""
        phone_log.add_call("Alice", "555-1111", "incoming", 120, data_file=self.db)
        phone_log.add_call("Bob", "555-2222", "outgoing", 60, data_file=self.db)
        phone_log.add_call("Alice", "555-1111", "incoming", 180, data_file=self.db)
        phone_log.add_call("Charlie", "555-3333", "missed", None, data_file=self.db)


class TestGetCallStatistics(TestAnalyticsBase):
    """Tests for get_call_statistics function."""

    def test_empty_log(self):
        stats = analytics.get_call_statistics(self.db)
        self.assertEqual(stats["total_calls"], 0)
        self.assertEqual(stats["incoming"], 0)
        self.assertEqual(stats["outgoing"], 0)
        self.assertEqual(stats["missed"], 0)

    def test_with_calls(self):
        self._add_test_calls()
        stats = analytics.get_call_statistics(self.db)
        
        self.assertEqual(stats["total_calls"], 4)
        self.assertEqual(stats["incoming"], 2)
        self.assertEqual(stats["outgoing"], 1)
        self.assertEqual(stats["missed"], 1)

    def test_duration_stats(self):
        self._add_test_calls()
        stats = analytics.get_call_statistics(self.db)
        
        # Total: 120 + 60 + 180 = 360 seconds
        self.assertEqual(stats["total_duration_seconds"], 360)
        # Average: 360 / 3 = 120 (missed calls excluded)
        self.assertEqual(stats["average_duration_seconds"], 120.0)

    def test_top_contacts(self):
        self._add_test_calls()
        stats = analytics.get_call_statistics(self.db)
        
        top = stats["top_contacts"]
        self.assertTrue(len(top) > 0)
        # Alice has most calls (2)
        self.assertEqual(top[0]["name"], "Alice")
        self.assertEqual(top[0]["count"], 2)

    def test_longest_call(self):
        self._add_test_calls()
        stats = analytics.get_call_statistics(self.db)
        
        longest = stats["longest_call"]
        self.assertIsNotNone(longest)
        self.assertEqual(longest["duration_seconds"], 180)


class TestGetCallsPerDay(TestAnalyticsBase):
    """Tests for get_calls_per_day function."""

    def test_returns_list(self):
        result = analytics.get_calls_per_day(7, self.db)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 7)

    def test_structure(self):
        result = analytics.get_calls_per_day(7, self.db)
        for day in result:
            self.assertIn("date", day)
            self.assertIn("incoming", day)
            self.assertIn("outgoing", day)
            self.assertIn("missed", day)
            self.assertIn("total", day)

    def test_with_calls(self):
        self._add_test_calls()
        result = analytics.get_calls_per_day(30, self.db)
        
        # Today should have some calls
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_stats = next((d for d in result if d["date"] == today), None)
        
        if today_stats:
            self.assertTrue(today_stats["total"] > 0)


class TestGetContactSummary(TestAnalyticsBase):
    """Tests for get_contact_summary function."""

    def test_empty_log(self):
        result = analytics.get_contact_summary(self.db)
        self.assertEqual(result, [])

    def test_with_calls(self):
        self._add_test_calls()
        result = analytics.get_contact_summary(self.db)
        
        self.assertEqual(len(result), 3)  # Alice, Bob, Charlie
        
        # Alice should be first (most calls)
        alice = result[0]
        self.assertEqual(alice["name"], "Alice")
        self.assertEqual(alice["total_calls"], 2)
        self.assertEqual(alice["incoming"], 2)

    def test_structure(self):
        self._add_test_calls()
        result = analytics.get_contact_summary(self.db)
        
        for contact in result:
            self.assertIn("name", contact)
            self.assertIn("total_calls", contact)
            self.assertIn("incoming", contact)
            self.assertIn("outgoing", contact)
            self.assertIn("missed", contact)
            self.assertIn("total_duration", contact)
            self.assertIn("phone_numbers", contact)


class TestGetHourlyDistribution(TestAnalyticsBase):
    """Tests for get_hourly_distribution function."""

    def test_returns_24_hours(self):
        result = analytics.get_hourly_distribution(self.db)
        self.assertEqual(len(result), 24)

    def test_all_hours_present(self):
        result = analytics.get_hourly_distribution(self.db)
        for hour in range(24):
            self.assertIn(hour, result)

    def test_with_calls(self):
        self._add_test_calls()
        result = analytics.get_hourly_distribution(self.db)
        
        # Should have some non-zero values
        total = sum(result.values())
        self.assertEqual(total, 4)


class TestGetWeeklyTrends(TestAnalyticsBase):
    """Tests for get_weekly_trends function."""

    def test_returns_list(self):
        result = analytics.get_weekly_trends(4, self.db)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4)

    def test_structure(self):
        result = analytics.get_weekly_trends(4, self.db)
        for week in result:
            self.assertIn("week_start", week)
            self.assertIn("week_end", week)
            self.assertIn("total_calls", week)
            self.assertIn("incoming", week)
            self.assertIn("outgoing", week)
            self.assertIn("missed", week)


class TestGetCallDurationDistribution(TestAnalyticsBase):
    """Tests for get_call_duration_distribution function."""

    def test_returns_buckets(self):
        result = analytics.get_call_duration_distribution(self.db)
        expected_buckets = ["< 1 min", "1-5 min", "5-15 min", "15-30 min", "30-60 min", "> 1 hour"]
        for bucket in expected_buckets:
            self.assertIn(bucket, result)

    def test_with_calls(self):
        self._add_test_calls()
        result = analytics.get_call_duration_distribution(self.db)
        
        # 60s = 1-5 min, 120s = 1-5 min, 180s = 1-5 min
        self.assertEqual(result["1-5 min"], 3)


class TestSearchByDateRange(TestAnalyticsBase):
    """Tests for search_by_date_range function."""

    def test_empty_result(self):
        result = analytics.search_by_date_range("2020-01-01", "2020-01-31", self.db)
        self.assertEqual(result, [])

    def test_with_calls(self):
        self._add_test_calls()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        result = analytics.search_by_date_range(today, today, self.db)
        
        self.assertEqual(len(result), 4)

    def test_invalid_dates(self):
        result = analytics.search_by_date_range("invalid", "dates", self.db)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
