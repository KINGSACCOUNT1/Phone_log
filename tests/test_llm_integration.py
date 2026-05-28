"""Tests for LLM Integration module."""

import unittest
import json
from unittest.mock import patch, MagicMock
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import llm_integration


class TestLLMConfig(unittest.TestCase):
    """Test LLM configuration functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use a temporary config for tests
        self.original_config_file = llm_integration.LLM_CONFIG_FILE
        llm_integration.LLM_CONFIG_FILE = "/tmp/test_llm_config.json"
        # Clean up any existing test config
        if os.path.exists(llm_integration.LLM_CONFIG_FILE):
            os.remove(llm_integration.LLM_CONFIG_FILE)
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(llm_integration.LLM_CONFIG_FILE):
            os.remove(llm_integration.LLM_CONFIG_FILE)
        llm_integration.LLM_CONFIG_FILE = self.original_config_file
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        config = llm_integration.load_llm_config()
        self.assertEqual(config["provider"], "openai")
        self.assertFalse(config["enabled"])
        self.assertEqual(config["temperature"], 0.7)
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        config = llm_integration.load_llm_config()
        config["provider"] = "anthropic"
        config["enabled"] = True
        llm_integration.save_llm_config(config)
        
        loaded = llm_integration.load_llm_config()
        self.assertEqual(loaded["provider"], "anthropic")
        self.assertTrue(loaded["enabled"])
    
    def test_update_config(self):
        """Test updating configuration."""
        updated = llm_integration.update_llm_config(temperature=0.5)
        self.assertEqual(updated["temperature"], 0.5)
    
    def test_is_llm_enabled_false_by_default(self):
        """Test that LLM is disabled by default."""
        self.assertFalse(llm_integration.is_llm_enabled())
    
    def test_set_openai_config(self):
        """Test setting OpenAI configuration."""
        result = llm_integration.set_openai_config("test-key", "gpt-4")
        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["openai_model"], "gpt-4")
        self.assertTrue(result["enabled"])
    
    def test_set_anthropic_config(self):
        """Test setting Anthropic configuration."""
        result = llm_integration.set_anthropic_config("test-key", "claude-3-opus")
        self.assertEqual(result["provider"], "anthropic")
        self.assertEqual(result["anthropic_model"], "claude-3-opus")
    
    def test_get_frontend_config_no_keys(self):
        """Test frontend config doesn't expose API keys."""
        llm_integration.set_openai_config("secret-key")
        frontend = llm_integration.get_llm_config_for_frontend()
        
        self.assertNotIn("openai_api_key", frontend)
        self.assertNotIn("anthropic_api_key", frontend)
        self.assertTrue(frontend["has_openai"])


class TestLLMClients(unittest.TestCase):
    """Test LLM client classes."""
    
    def test_openai_client_init(self):
        """Test OpenAI client initialization."""
        config = {"openai_api_key": "test", "openai_model": "gpt-3.5-turbo"}
        client = llm_integration.OpenAIClient(config)
        self.assertEqual(client.config["openai_api_key"], "test")
    
    def test_anthropic_client_init(self):
        """Test Anthropic client initialization."""
        config = {"anthropic_api_key": "test", "anthropic_model": "claude-3-haiku"}
        client = llm_integration.AnthropicClient(config)
        self.assertEqual(client.config["anthropic_api_key"], "test")
    
    def test_local_client_init(self):
        """Test Local LLM client initialization."""
        config = {"local_endpoint": "http://localhost:11434/api/generate", "local_model": "llama2"}
        client = llm_integration.LocalLLMClient(config)
        self.assertEqual(client.config["local_model"], "llama2")
    
    @patch('requests.post')
    def test_openai_client_complete(self, mock_post):
        """Test OpenAI client completion."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}]
        }
        mock_post.return_value = mock_response
        
        config = {"openai_api_key": "test", "openai_model": "gpt-3.5-turbo", "temperature": 0.7, "max_tokens": 500}
        client = llm_integration.OpenAIClient(config)
        result = client.complete("Hi")
        
        self.assertEqual(result, "Hello!")
    
    def test_openai_client_no_key(self):
        """Test OpenAI client with no API key."""
        config = {"openai_api_key": "", "openai_model": "gpt-3.5-turbo"}
        client = llm_integration.OpenAIClient(config)
        result = client.complete("Hi")
        self.assertIsNone(result)


class TestIntentExtraction(unittest.TestCase):
    """Test intent extraction with LLM."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.original_config_file = llm_integration.LLM_CONFIG_FILE
        llm_integration.LLM_CONFIG_FILE = "/tmp/test_llm_config.json"
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(llm_integration.LLM_CONFIG_FILE):
            os.remove(llm_integration.LLM_CONFIG_FILE)
        llm_integration.LLM_CONFIG_FILE = self.original_config_file
    
    def test_extract_intent_no_client(self):
        """Test intent extraction when no LLM client is available."""
        result = llm_integration.extract_intent_with_llm("show my calls")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
