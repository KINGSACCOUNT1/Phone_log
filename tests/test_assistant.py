"""Unit tests for the assistant module - intent recognition and response generation."""

import os
import tempfile
import unittest
from unittest.mock import patch

import assistant
import phone_log


class TestIntentRecognition(unittest.TestCase):
    """Tests for the recognize_intent function."""

    def test_greeting_intent_hi(self):
        intent, entities, confidence = assistant.recognize_intent("hi")
        self.assertEqual(intent, "greeting")
        self.assertEqual(confidence, assistant.CONFIDENCE_HIGH)

    def test_greeting_intent_hello(self):
        intent, entities, confidence = assistant.recognize_intent("hello there!")
        self.assertEqual(intent, "greeting")

    def test_greeting_intent_good_morning(self):
        intent, entities, confidence = assistant.recognize_intent("good morning")
        self.assertEqual(intent, "greeting")

    def test_list_calls_intent(self):
        intent, entities, confidence = assistant.recognize_intent("show my calls")
        self.assertEqual(intent, "list_calls")
        self.assertEqual(confidence, assistant.CONFIDENCE_HIGH)

    def test_list_calls_intent_variations(self):
        variations = [
            "list all calls",
            "display my phone calls",
            "get my records",
            "view calls",
            "what calls do i have",
        ]
        for text in variations:
            intent, _, _ = assistant.recognize_intent(text)
            self.assertEqual(intent, "list_calls", f"Failed for: {text}")

    def test_search_calls_intent(self):
        intent, entities, confidence = assistant.recognize_intent("search for Alice")
        self.assertEqual(intent, "search_calls")
        # Entity may be lowercased
        self.assertIn("alice", entities[0].lower() if entities else "")

    def test_search_calls_intent_with_name(self):
        intent, entities, _ = assistant.recognize_intent("find calls from Bob")
        self.assertEqual(intent, "search_calls")
        # Entity may be lowercased
        self.assertTrue(any("bob" in str(e).lower() for e in entities))

    def test_delete_call_intent(self):
        intent, entities, confidence = assistant.recognize_intent("delete call 5")
        self.assertEqual(intent, "delete_call")
        self.assertEqual(entities[0], "5")

    def test_delete_call_intent_variations(self):
        intent, entities, _ = assistant.recognize_intent("remove record 123")
        self.assertEqual(intent, "delete_call")
        self.assertEqual(entities[0], "123")

    def test_stats_intent(self):
        intent, _, confidence = assistant.recognize_intent("how many calls do I have")
        self.assertEqual(intent, "stats")

    def test_stats_intent_variations(self):
        variations = [
            "count calls",
            "give me statistics",
            "call stats",
            "total records",
        ]
        for text in variations:
            intent, _, _ = assistant.recognize_intent(text)
            self.assertEqual(intent, "stats", f"Failed for: {text}")

    def test_help_intent(self):
        intent, _, _ = assistant.recognize_intent("what can you do")
        self.assertEqual(intent, "help")

    def test_help_intent_variations(self):
        variations = ["help", "commands", "how do i use this"]
        for text in variations:
            intent, _, _ = assistant.recognize_intent(text)
            self.assertEqual(intent, "help", f"Failed for: {text}")

    def test_identity_intent(self):
        intent, _, _ = assistant.recognize_intent("who are you")
        self.assertEqual(intent, "identity")

    def test_identity_intent_variations(self):
        variations = ["what is your name", "tell me about yourself", "introduce yourself"]
        for text in variations:
            intent, _, _ = assistant.recognize_intent(text)
            self.assertEqual(intent, "identity", f"Failed for: {text}")

    def test_full_name_intent(self):
        intent, _, _ = assistant.recognize_intent("what is your full name")
        self.assertEqual(intent, "full_name")

    def test_add_call_intent(self):
        intent, _, _ = assistant.recognize_intent("add a new call")
        self.assertEqual(intent, "add_call")

    def test_add_call_intent_variations(self):
        variations = [
            "log a call",
            "record phone call",
            "i had a call with john",
            "i received a call",
        ]
        for text in variations:
            intent, _, _ = assistant.recognize_intent(text)
            self.assertEqual(intent, "add_call", f"Failed for: {text}")

    def test_unknown_intent(self):
        intent, _, confidence = assistant.recognize_intent("random gibberish xyz")
        self.assertEqual(intent, "unknown")
        self.assertEqual(confidence, assistant.CONFIDENCE_LOW)

    def test_case_insensitive(self):
        intent1, _, _ = assistant.recognize_intent("SHOW MY CALLS")
        intent2, _, _ = assistant.recognize_intent("show my calls")
        self.assertEqual(intent1, intent2)


class TestResponseGeneration(unittest.TestCase):
    """Tests for the generate_response function."""

    def setUp(self):
        """Set up test fixtures."""
        self.tmp_data = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp_data.close()
        os.unlink(self.tmp_data.name)  # Start with no file
        
        self.tmp_identity = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp_identity.close()
        os.unlink(self.tmp_identity.name)

    def tearDown(self):
        """Clean up test files."""
        for path in [self.tmp_data.name, self.tmp_identity.name]:
            if os.path.exists(path):
                os.unlink(path)

    def test_greeting_response(self):
        result = assistant.generate_response("hi")
        self.assertEqual(result["action_taken"], "greeted_user")
        self.assertIn("reasoning", result)
        self.assertIn("response", result)

    def test_help_response_contains_capabilities(self):
        result = assistant.generate_response("help")
        self.assertEqual(result["action_taken"], "showed_help")
        self.assertIn("Add a call", result["response"])
        self.assertIn("View calls", result["response"])
        self.assertIn("Search", result["response"])

    def test_identity_response(self):
        result = assistant.generate_response("who are you")
        self.assertEqual(result["action_taken"], "introduced_self")
        # Should contain assistant name
        identity = assistant.load_identity()
        self.assertIn(identity["name"], result["response"])

    def test_list_calls_empty(self):
        with patch.object(phone_log, "get_all", return_value=[]):
            result = assistant.generate_response("show my calls")
            self.assertEqual(result["action_taken"], "listed_calls")
            self.assertIn("don't have any calls", result["response"])

    def test_list_calls_with_data(self):
        mock_calls = [
            {"id": 1, "contact_name": "Alice", "direction": "incoming"},
            {"id": 2, "contact_name": "Bob", "direction": "outgoing"},
        ]
        with patch.object(phone_log, "get_all", return_value=mock_calls):
            result = assistant.generate_response("show my calls")
            self.assertEqual(result["action_taken"], "listed_calls")
            self.assertEqual(result["data"], mock_calls)

    def test_search_calls_with_query(self):
        mock_calls = [{"id": 1, "contact_name": "Alice", "direction": "incoming"}]
        with patch.object(phone_log, "search", return_value=mock_calls):
            result = assistant.generate_response("find calls from Alice")
            self.assertEqual(result["action_taken"], "searched_calls")

    def test_search_calls_no_results(self):
        with patch.object(phone_log, "search", return_value=[]):
            result = assistant.generate_response("search for XYZ123")
            self.assertEqual(result["action_taken"], "searched_calls")
            self.assertIn("No calls found", result["response"])

    def test_stats_response(self):
        mock_calls = [
            {"id": 1, "direction": "incoming"},
            {"id": 2, "direction": "incoming"},
            {"id": 3, "direction": "outgoing"},
            {"id": 4, "direction": "missed"},
        ]
        with patch.object(phone_log, "get_all", return_value=mock_calls):
            result = assistant.generate_response("how many calls")
            self.assertEqual(result["action_taken"], "showed_stats")
            self.assertEqual(result["data"]["total"], 4)
            self.assertEqual(result["data"]["incoming"], 2)
            self.assertEqual(result["data"]["outgoing"], 1)
            self.assertEqual(result["data"]["missed"], 1)

    def test_add_call_response(self):
        result = assistant.generate_response("add a call")
        self.assertEqual(result["action_taken"], "prompted_add_call")
        self.assertIn("Contact name", result["response"])

    def test_delete_call_success(self):
        with patch.object(phone_log, "delete_call", return_value=True):
            result = assistant.generate_response("delete call 5")
            self.assertEqual(result["action_taken"], "deleted_call")
            self.assertIn("Deleted", result["response"])

    def test_delete_call_not_found(self):
        with patch.object(phone_log, "delete_call", return_value=False):
            result = assistant.generate_response("delete call 999")
            self.assertEqual(result["action_taken"], "delete_failed")
            self.assertIn("couldn't find", result["response"])

    def test_unknown_intent_response(self):
        result = assistant.generate_response("xyz random text")
        self.assertEqual(result["action_taken"], "asked_clarification")
        self.assertIn("not quite sure", result["response"])


class TestIdentityManagement(unittest.TestCase):
    """Tests for identity load/save/update functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_file = assistant.IDENTITY_FILE
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        assistant.IDENTITY_FILE = self.tmp.name

    def tearDown(self):
        """Restore original and clean up."""
        assistant.IDENTITY_FILE = self.original_file
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_load_identity_default(self):
        identity = assistant.load_identity()
        self.assertEqual(identity["name"], assistant.DEFAULT_IDENTITY["name"])
        self.assertEqual(identity["role"], assistant.DEFAULT_IDENTITY["role"])

    def test_save_and_load_identity(self):
        identity = {"name": "Test", "role": "Tester", "personality": "cool"}
        assistant.save_identity(identity)
        loaded = assistant.load_identity()
        self.assertEqual(loaded["name"], "Test")
        self.assertEqual(loaded["role"], "Tester")

    def test_update_identity_partial(self):
        assistant.save_identity(assistant.DEFAULT_IDENTITY.copy())
        updated = assistant.update_identity(name="NewName")
        self.assertEqual(updated["name"], "NewName")
        # Other fields should remain
        self.assertEqual(updated["role"], assistant.DEFAULT_IDENTITY["role"])

    def test_update_identity_all_fields(self):
        assistant.save_identity(assistant.DEFAULT_IDENTITY.copy())
        updated = assistant.update_identity(
            name="Custom",
            role="Custom Role",
            personality="serious",
            greeting="Yo!",
            voice="male",
        )
        self.assertEqual(updated["name"], "Custom")
        self.assertEqual(updated["role"], "Custom Role")
        self.assertEqual(updated["personality"], "serious")
        self.assertEqual(updated["greeting"], "Yo!")
        self.assertEqual(updated["voice"], "male")


class TestConversationManager(unittest.TestCase):
    """Tests for the ConversationManager class."""

    def test_add_exchange(self):
        manager = assistant.ConversationManager()
        manager.add_exchange("hello", "hi there!")
        history = manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["user"], "hello")
        self.assertEqual(history[0]["assistant"], "hi there!")

    def test_history_limit(self):
        manager = assistant.ConversationManager(max_history=3)
        for i in range(5):
            manager.add_exchange(f"user{i}", f"assistant{i}")
        history = manager.get_history()
        self.assertEqual(len(history), 3)
        # Should keep the last 3
        self.assertEqual(history[0]["user"], "user2")
        self.assertEqual(history[2]["user"], "user4")

    def test_clear_history(self):
        manager = assistant.ConversationManager()
        manager.add_exchange("test", "response")
        manager.clear()
        self.assertEqual(len(manager.get_history()), 0)

    def test_get_history_returns_copy(self):
        manager = assistant.ConversationManager()
        manager.add_exchange("test", "response")
        history1 = manager.get_history()
        history2 = manager.get_history()
        self.assertIsNot(history1, history2)


class TestChatFunction(unittest.TestCase):
    """Tests for the main chat function."""

    def test_chat_returns_result(self):
        result = assistant.chat("hi")
        self.assertIn("reasoning", result)
        self.assertIn("response", result)
        self.assertIn("action_taken", result)

    def test_chat_adds_to_history(self):
        assistant.conversation.clear()
        assistant.chat("hello")
        history = assistant.conversation.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["user"], "hello")


if __name__ == "__main__":
    unittest.main()
