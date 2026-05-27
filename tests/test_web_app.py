"""Integration tests for the Flask web application endpoints."""

import json
import os
import tempfile
import unittest

# Set up test environment before importing the app
os.environ["FLASK_DEBUG"] = "0"

import phone_log
import assistant
import voice_config
from web_app import app


class TestWebAppBase(unittest.TestCase):
    """Base class for web app tests with common setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        
        # Create temp files for data isolation
        self.tmp_data = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp_data.close()
        os.unlink(self.tmp_data.name)
        
        self.tmp_identity = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp_identity.close()
        os.unlink(self.tmp_identity.name)
        
        self.tmp_voice = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp_voice.close()
        os.unlink(self.tmp_voice.name)
        
        # Store original file paths
        self.original_data_file = phone_log.DATA_FILE
        self.original_identity_file = assistant.IDENTITY_FILE
        self.original_voice_file = voice_config.VOICE_CONFIG_FILE
        
        # Point to temp files
        phone_log.DATA_FILE = self.tmp_data.name
        assistant.IDENTITY_FILE = self.tmp_identity.name
        voice_config.VOICE_CONFIG_FILE = self.tmp_voice.name

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original file paths
        phone_log.DATA_FILE = self.original_data_file
        assistant.IDENTITY_FILE = self.original_identity_file
        voice_config.VOICE_CONFIG_FILE = self.original_voice_file
        
        # Clean up temp files
        for path in [self.tmp_data.name, self.tmp_identity.name, self.tmp_voice.name]:
            if os.path.exists(path):
                os.unlink(path)


class TestIndexRoute(TestWebAppBase):
    """Tests for the main index route."""

    def test_index_returns_200(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_index_contains_assistant_name(self):
        response = self.client.get("/")
        # Should contain default assistant name
        self.assertIn(b"Luna", response.data)


class TestChatAPI(TestWebAppBase):
    """Tests for the chat API endpoint."""

    def test_chat_endpoint_exists(self):
        response = self.client.post(
            "/api/chat",
            json={"message": "hello"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

    def test_chat_returns_json(self):
        response = self.client.post(
            "/api/chat",
            json={"message": "hi"},
            content_type="application/json"
        )
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn("reasoning", data)

    def test_chat_empty_message_error(self):
        response = self.client.post(
            "/api/chat",
            json={"message": ""},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_chat_missing_message_error(self):
        response = self.client.post(
            "/api/chat",
            json={},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)


class TestIdentityAPI(TestWebAppBase):
    """Tests for the identity API endpoints."""

    def test_get_identity(self):
        response = self.client.get("/api/identity")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("name", data)
        self.assertIn("role", data)

    def test_update_identity(self):
        response = self.client.put(
            "/api/identity",
            json={"name": "NewBot", "role": "Test Role"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["name"], "NewBot")
        self.assertEqual(data["role"], "Test Role")

    def test_update_identity_partial(self):
        response = self.client.put(
            "/api/identity",
            json={"name": "PartialUpdate"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["name"], "PartialUpdate")


class TestCallsAPI(TestWebAppBase):
    """Tests for the calls API endpoints."""

    def test_list_calls_empty(self):
        response = self.client.get("/api/calls")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, [])

    def test_add_call(self):
        response = self.client.post(
            "/api/calls",
            json={
                "contact_name": "Test Contact",
                "phone_number": "555-1234",
                "direction": "incoming",
                "duration_seconds": 120,
                "notes": "Test note"
            },
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data["contact_name"], "Test Contact")
        self.assertEqual(data["id"], 1)

    def test_add_call_invalid_data(self):
        response = self.client.post(
            "/api/calls",
            json={
                "contact_name": "",
                "phone_number": "555-1234",
                "direction": "incoming"
            },
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_list_calls_with_data(self):
        # Add a call first
        self.client.post(
            "/api/calls",
            json={
                "contact_name": "Alice",
                "phone_number": "555-1111",
                "direction": "incoming"
            },
            content_type="application/json"
        )
        
        response = self.client.get("/api/calls")
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["contact_name"], "Alice")

    def test_list_calls_filter_by_direction(self):
        # Add calls with different directions
        self.client.post("/api/calls", json={
            "contact_name": "A", "phone_number": "111", "direction": "incoming"
        }, content_type="application/json")
        self.client.post("/api/calls", json={
            "contact_name": "B", "phone_number": "222", "direction": "outgoing"
        }, content_type="application/json")
        
        response = self.client.get("/api/calls?direction=incoming")
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["contact_name"], "A")

    def test_delete_call(self):
        # Add a call
        add_response = self.client.post(
            "/api/calls",
            json={
                "contact_name": "ToDelete",
                "phone_number": "555-0000",
                "direction": "missed"
            },
            content_type="application/json"
        )
        call_id = json.loads(add_response.data)["id"]
        
        # Delete it
        delete_response = self.client.delete(f"/api/calls/{call_id}")
        self.assertEqual(delete_response.status_code, 200)
        
        # Verify it's gone
        list_response = self.client.get("/api/calls")
        data = json.loads(list_response.data)
        self.assertEqual(len(data), 0)

    def test_delete_nonexistent_call(self):
        response = self.client.delete("/api/calls/9999")
        self.assertEqual(response.status_code, 404)

    def test_update_notes(self):
        # Add a call
        add_response = self.client.post(
            "/api/calls",
            json={
                "contact_name": "NoteTest",
                "phone_number": "555-1111",
                "direction": "incoming"
            },
            content_type="application/json"
        )
        call_id = json.loads(add_response.data)["id"]
        
        # Update notes
        response = self.client.put(
            f"/api/calls/{call_id}/notes",
            json={"notes": "Updated note"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["notes"], "Updated note")

    def test_update_notes_nonexistent(self):
        response = self.client.put(
            "/api/calls/9999/notes",
            json={"notes": "test"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)

    def test_search_calls(self):
        # Add some calls
        self.client.post("/api/calls", json={
            "contact_name": "Alice Smith", "phone_number": "111", "direction": "incoming"
        }, content_type="application/json")
        self.client.post("/api/calls", json={
            "contact_name": "Bob Jones", "phone_number": "222", "direction": "outgoing"
        }, content_type="application/json")
        
        response = self.client.get("/api/calls/search?q=alice")
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["contact_name"], "Alice Smith")


class TestHistoryAPI(TestWebAppBase):
    """Tests for the conversation history API endpoints."""

    def test_get_history_empty(self):
        assistant.conversation.clear()
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, [])

    def test_get_history_after_chat(self):
        assistant.conversation.clear()
        self.client.post("/api/chat", json={"message": "hello"}, content_type="application/json")
        
        response = self.client.get("/api/history")
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)

    def test_clear_history(self):
        assistant.conversation.clear()
        self.client.post("/api/chat", json={"message": "test"}, content_type="application/json")
        
        response = self.client.delete("/api/history")
        self.assertEqual(response.status_code, 200)
        
        history_response = self.client.get("/api/history")
        data = json.loads(history_response.data)
        self.assertEqual(len(data), 0)


class TestPersonasAPI(TestWebAppBase):
    """Tests for the personas API endpoints."""

    def test_list_personas(self):
        response = self.client.get("/api/personas")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) >= 2)

    def test_set_persona_valid(self):
        response = self.client.post("/api/personas/coach_jv")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["name"], "Coach JV")

    def test_set_persona_invalid(self):
        response = self.client.post("/api/personas/nonexistent")
        self.assertEqual(response.status_code, 404)


class TestVoiceConfigAPI(TestWebAppBase):
    """Tests for the voice configuration API endpoints."""

    def test_get_voice_config(self):
        response = self.client.get("/api/voice/config")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("tts_provider", data)
        self.assertIn("humanization", data)

    def test_update_voice_config(self):
        response = self.client.put(
            "/api/voice/config",
            json={"tts_provider": "elevenlabs"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

    def test_humanize_text_endpoint(self):
        response = self.client.post(
            "/api/voice/humanize",
            json={"text": "I am going to help you"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("original", data)
        self.assertIn("humanized", data)

    def test_list_voice_clones_empty(self):
        # Clear any existing clones first
        config = voice_config.load_voice_config()
        config["cloned_voices"] = {}
        voice_config.save_voice_config(config)
        
        response = self.client.get("/api/voice/clones")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, {})

    def test_add_voice_clone(self):
        response = self.client.post(
            "/api/voice/clones",
            json={"name": "test_voice", "voice_id": "voice123"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

    def test_add_voice_clone_missing_fields(self):
        response = self.client.post(
            "/api/voice/clones",
            json={"name": "test_voice"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_remove_voice_clone(self):
        # Add first
        self.client.post(
            "/api/voice/clones",
            json={"name": "to_remove", "voice_id": "id123"},
            content_type="application/json"
        )
        
        # Remove
        response = self.client.delete("/api/voice/clones/to_remove")
        self.assertEqual(response.status_code, 200)

    def test_remove_nonexistent_voice_clone(self):
        response = self.client.delete("/api/voice/clones/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_set_elevenlabs_config(self):
        response = self.client.put(
            "/api/voice/elevenlabs",
            json={"api_key": "test_key", "voice_id": "test_voice"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
