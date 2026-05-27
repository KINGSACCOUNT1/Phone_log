"""Unit tests for the phone_log core module."""

import os
import tempfile
import unittest

import phone_log


class TestAddCall(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)  # start with no file (empty log)
        self.db = self.tmp.name

    def tearDown(self):
        if os.path.exists(self.db):
            os.unlink(self.db)

    def test_add_incoming_call(self):
        entry = phone_log.add_call("Alice", "555-1234", "incoming", 90, data_file=self.db)
        self.assertEqual(entry["contact_name"], "Alice")
        self.assertEqual(entry["phone_number"], "555-1234")
        self.assertEqual(entry["direction"], "incoming")
        self.assertEqual(entry["duration_seconds"], 90)
        self.assertEqual(entry["id"], 1)

    def test_add_missed_call_no_duration(self):
        entry = phone_log.add_call("Bob", "555-5678", "missed", data_file=self.db)
        self.assertIsNone(entry["duration_seconds"])
        self.assertEqual(entry["direction"], "missed")

    def test_add_outgoing_call_with_notes(self):
        entry = phone_log.add_call("Carol", "555-9999", "outgoing", 300, "follow-up", data_file=self.db)
        self.assertEqual(entry["notes"], "follow-up")

    def test_ids_are_unique_and_incrementing(self):
        e1 = phone_log.add_call("A", "111", "incoming", data_file=self.db)
        e2 = phone_log.add_call("B", "222", "outgoing", data_file=self.db)
        e3 = phone_log.add_call("C", "333", "missed", data_file=self.db)
        self.assertEqual(e1["id"], 1)
        self.assertEqual(e2["id"], 2)
        self.assertEqual(e3["id"], 3)

    def test_invalid_direction_raises(self):
        with self.assertRaises(ValueError):
            phone_log.add_call("X", "000", "unknown", data_file=self.db)

    def test_empty_name_raises(self):
        with self.assertRaises(ValueError):
            phone_log.add_call("", "000", "incoming", data_file=self.db)

    def test_empty_number_raises(self):
        with self.assertRaises(ValueError):
            phone_log.add_call("X", "", "incoming", data_file=self.db)

    def test_negative_duration_raises(self):
        with self.assertRaises(ValueError):
            phone_log.add_call("X", "000", "incoming", -5, data_file=self.db)


class TestGetAll(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.db = self.tmp.name

    def tearDown(self):
        if os.path.exists(self.db):
            os.unlink(self.db)

    def test_get_all_empty(self):
        self.assertEqual(phone_log.get_all(data_file=self.db), [])

    def test_get_all_returns_most_recent_first(self):
        phone_log.add_call("A", "1", "incoming", data_file=self.db)
        phone_log.add_call("B", "2", "outgoing", data_file=self.db)
        entries = phone_log.get_all(data_file=self.db)
        # Most recent call was "B" (added second)
        self.assertEqual(entries[0]["contact_name"], "B")
        self.assertEqual(entries[1]["contact_name"], "A")


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.db = self.tmp.name
        phone_log.add_call("Alice Johnson", "555-1000", "incoming", data_file=self.db)
        phone_log.add_call("Bob Smith", "555-2000", "outgoing", data_file=self.db)
        phone_log.add_call("Alice Cooper", "555-3000", "missed", data_file=self.db)

    def tearDown(self):
        if os.path.exists(self.db):
            os.unlink(self.db)

    def test_search_by_name(self):
        results = phone_log.search("alice", data_file=self.db)
        self.assertEqual(len(results), 2)
        names = {r["contact_name"] for r in results}
        self.assertIn("Alice Johnson", names)
        self.assertIn("Alice Cooper", names)

    def test_search_by_number(self):
        results = phone_log.search("555-2000", data_file=self.db)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["contact_name"], "Bob Smith")

    def test_search_case_insensitive(self):
        self.assertEqual(
            phone_log.search("BOB", data_file=self.db),
            phone_log.search("bob", data_file=self.db),
        )

    def test_search_no_match(self):
        self.assertEqual(phone_log.search("zzz", data_file=self.db), [])

    def test_search_empty_query_returns_empty(self):
        self.assertEqual(phone_log.search("", data_file=self.db), [])


class TestDelete(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.db = self.tmp.name
        self.entry = phone_log.add_call("Dave", "555-4000", "incoming", data_file=self.db)

    def tearDown(self):
        if os.path.exists(self.db):
            os.unlink(self.db)

    def test_delete_existing(self):
        result = phone_log.delete_call(self.entry["id"], data_file=self.db)
        self.assertTrue(result)
        self.assertEqual(phone_log.get_all(data_file=self.db), [])

    def test_delete_nonexistent_returns_false(self):
        result = phone_log.delete_call(9999, data_file=self.db)
        self.assertFalse(result)

    def test_remaining_entries_intact_after_delete(self):
        phone_log.add_call("Eve", "555-5000", "outgoing", data_file=self.db)
        phone_log.delete_call(self.entry["id"], data_file=self.db)
        entries = phone_log.get_all(data_file=self.db)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["contact_name"], "Eve")


class TestUpdateNotes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.db = self.tmp.name
        self.entry = phone_log.add_call("Frank", "555-6000", "incoming", notes="old note", data_file=self.db)

    def tearDown(self):
        if os.path.exists(self.db):
            os.unlink(self.db)

    def test_update_notes_existing(self):
        updated = phone_log.update_notes(self.entry["id"], "new note", data_file=self.db)
        self.assertIsNotNone(updated)
        self.assertEqual(updated["notes"], "new note")

    def test_update_notes_nonexistent_returns_none(self):
        result = phone_log.update_notes(9999, "anything", data_file=self.db)
        self.assertIsNone(result)

    def test_update_notes_persisted(self):
        phone_log.update_notes(self.entry["id"], "persisted", data_file=self.db)
        entries = phone_log.get_all(data_file=self.db)
        self.assertEqual(entries[0]["notes"], "persisted")


class TestFormatDuration(unittest.TestCase):
    def test_none(self):
        self.assertEqual(phone_log.format_duration(None), "-")

    def test_seconds_only(self):
        self.assertEqual(phone_log.format_duration(45), "45s")

    def test_minutes_and_seconds(self):
        self.assertEqual(phone_log.format_duration(150), "2m 30s")

    def test_hours_minutes_seconds(self):
        self.assertEqual(phone_log.format_duration(3661), "1h 1m 1s")

    def test_zero(self):
        self.assertEqual(phone_log.format_duration(0), "0s")


if __name__ == "__main__":
    unittest.main()
