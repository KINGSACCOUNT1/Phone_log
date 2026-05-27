"""LLM Integration - Connect to OpenAI/Claude for advanced conversational AI.

This module provides integration with Large Language Models for:
- Complex intent understanding beyond pattern matching
- Natural language generation with context awareness
- Fallback handling for unknown queries
"""

import json
import os
from typing import Optional

# ─── Configuration ─────────────────────────────────────────────────────────────

_DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
LLM_CONFIG_FILE = os.path.join(_DATA_DIR, "llm_config.json")

DEFAULT_LLM_CONFIG = {
    "provider": "openai",  # Options: "openai", "anthropic", "local", "none"
    "openai_api_key": "",
    "openai_model": "gpt-3.5-turbo",
    "anthropic_api_key": "",
    "anthropic_model": "claude-3-haiku-20240307",
    "local_endpoint": "http://localhost:11434/api/generate",  # Ollama default
    "local_model": "llama2",
    "enabled": False,  # Disabled by default until API key is configured
    "temperature": 0.7,
    "max_tokens": 500,
    "fallback_to_patterns": True,  # Use pattern matching if LLM fails
}

# System prompt for the assistant
SYSTEM_PROMPT = """You are a helpful phone log assistant named {name}. Your personality is {personality}.

Your capabilities include:
1. Adding phone call records (contact name, phone number, direction: incoming/outgoing/missed)
2. Listing and searching call history
3. Deleting call records by ID
4. Providing call statistics and analytics

When users want to add a call, extract:
- contact_name: The name of the person
- phone_number: Their phone number (if provided)
- direction: incoming, outgoing, or missed
- duration: Duration in seconds (if mentioned)
- notes: Any additional information

Respond in a {personality} manner. Keep responses concise but helpful.

Current conversation context:
{context}
"""


def load_llm_config():
    """Load LLM configuration from file."""
    if os.path.exists(LLM_CONFIG_FILE):
        with open(LLM_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            merged = DEFAULT_LLM_CONFIG.copy()
            merged.update(config)
            return merged
    return DEFAULT_LLM_CONFIG.copy()


def save_llm_config(config):
    """Save LLM configuration to file."""
    with open(LLM_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def update_llm_config(**kwargs):
    """Update LLM configuration with provided values."""
    config = load_llm_config()
    for key, value in kwargs.items():
        if key in config:
            config[key] = value
    save_llm_config(config)
    return config


def is_llm_enabled():
    """Check if LLM integration is enabled and configured."""
    config = load_llm_config()
    if not config.get("enabled", False):
        return False
    
    provider = config.get("provider", "none")
    if provider == "openai":
        return bool(config.get("openai_api_key"))
    elif provider == "anthropic":
        return bool(config.get("anthropic_api_key"))
    elif provider == "local":
        return bool(config.get("local_endpoint"))
    return False


# ─── LLM Client Classes ────────────────────────────────────────────────────────

class LLMClient:
    """Base class for LLM clients."""
    
    def __init__(self, config: dict):
        self.config = config
    
    def complete(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Generate a completion for the given prompt."""
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """OpenAI API client."""
    
    def complete(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Generate completion using OpenAI API."""
        try:
            import requests
            
            api_key = self.config.get("openai_api_key", "")
            if not api_key:
                return None
            
            auth_header = "Bearer " + api_key
            headers = {
                "Authorization": auth_header,
                "Content-Type": "application/json",
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.config.get("openai_model", "gpt-3.5-turbo"),
                "messages": messages,
                "temperature": self.config.get("temperature", 0.7),
                "max_tokens": self.config.get("max_tokens", 500),
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30,
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return None
                
        except Exception:
            return None


class AnthropicClient(LLMClient):
    """Anthropic (Claude) API client."""
    
    def complete(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Generate completion using Anthropic API."""
        try:
            import requests
            
            api_key = self.config.get("anthropic_api_key", "")
            if not api_key:
                return None
            
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            }
            
            data = {
                "model": self.config.get("anthropic_model", "claude-3-haiku-20240307"),
                "max_tokens": self.config.get("max_tokens", 500),
                "messages": [{"role": "user", "content": prompt}],
            }
            
            if system_prompt:
                data["system"] = system_prompt
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=30,
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            else:
                return None
                
        except Exception:
            return None


class LocalLLMClient(LLMClient):
    """Local LLM client (e.g., Ollama)."""
    
    def complete(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Generate completion using local LLM endpoint."""
        try:
            import requests
            
            endpoint = self.config.get("local_endpoint", "http://localhost:11434/api/generate")
            
            full_prompt = f"{system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
            
            data = {
                "model": self.config.get("local_model", "llama2"),
                "prompt": full_prompt,
                "stream": False,
            }
            
            response = requests.post(endpoint, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                return None
                
        except Exception:
            return None


def get_llm_client() -> Optional[LLMClient]:
    """Get the appropriate LLM client based on configuration."""
    config = load_llm_config()
    
    if not config.get("enabled", False):
        return None
    
    provider = config.get("provider", "none")
    
    if provider == "openai":
        return OpenAIClient(config)
    elif provider == "anthropic":
        return AnthropicClient(config)
    elif provider == "local":
        return LocalLLMClient(config)
    
    return None


# ─── Intent Extraction with LLM ────────────────────────────────────────────────

INTENT_EXTRACTION_PROMPT = """Analyze the following user message and extract the intent and entities.

User message: "{message}"

Respond ONLY with a valid JSON object in this exact format:
{{
    "intent": "one of: add_call, list_calls, search_calls, delete_call, greeting, help, identity, stats, unknown",
    "confidence": 0.0 to 1.0,
    "entities": {{
        "contact_name": "extracted name or null",
        "phone_number": "extracted number or null",
        "direction": "incoming/outgoing/missed or null",
        "duration": "duration in seconds or null",
        "call_id": "ID number or null",
        "search_query": "search term or null"
    }},
    "requires_clarification": true/false,
    "clarification_question": "question to ask if clarification needed"
}}
"""


def extract_intent_with_llm(message: str, context: str = "") -> Optional[dict]:
    """Use LLM to extract intent and entities from user message."""
    client = get_llm_client()
    if not client:
        return None
    
    prompt = INTENT_EXTRACTION_PROMPT.format(message=message)
    
    try:
        response = client.complete(prompt)
        if response:
            # Parse JSON from response
            # Try to find JSON in the response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
    except (json.JSONDecodeError, Exception):
        pass
    
    return None


# ─── Natural Response Generation ───────────────────────────────────────────────

def generate_natural_response(
    intent: str,
    entities: dict,
    action_result: dict,
    identity: dict,
    context: str = ""
) -> Optional[str]:
    """Generate a natural language response using LLM."""
    client = get_llm_client()
    if not client:
        return None
    
    system_prompt = SYSTEM_PROMPT.format(
        name=identity.get("name", "Luna"),
        personality=identity.get("personality", "friendly and helpful"),
        context=context or "No previous context"
    )
    
    prompt = f"""Generate a natural response for the following situation:

Intent: {intent}
Entities: {json.dumps(entities)}
Action Result: {json.dumps(action_result)}

Keep the response concise and natural. Use the assistant's personality."""

    return client.complete(prompt, system_prompt)


# ─── Fallback Handling ─────────────────────────────────────────────────────────

def handle_unknown_with_llm(message: str, identity: dict, context: str = "") -> Optional[str]:
    """Handle unknown intents using LLM for a more natural conversation."""
    client = get_llm_client()
    if not client:
        return None
    
    system_prompt = SYSTEM_PROMPT.format(
        name=identity.get("name", "Luna"),
        personality=identity.get("personality", "friendly and helpful"),
        context=context or "No previous context"
    )
    
    prompt = f"""The user said: "{message}"

This doesn't match any of my predefined actions. Please provide a helpful response that:
1. Acknowledges what the user said
2. Gently guides them toward what I can help with (phone call logging, searching, statistics)
3. Offers to help in a friendly way

Keep the response short and natural."""

    return client.complete(prompt, system_prompt)


# ─── API Configuration Helpers ─────────────────────────────────────────────────

def get_llm_config_for_frontend():
    """Get LLM configuration safe for frontend (no API keys)."""
    config = load_llm_config()
    return {
        "provider": config.get("provider", "none"),
        "enabled": config.get("enabled", False),
        "has_openai": bool(config.get("openai_api_key")),
        "has_anthropic": bool(config.get("anthropic_api_key")),
        "openai_model": config.get("openai_model", "gpt-3.5-turbo"),
        "anthropic_model": config.get("anthropic_model", "claude-3-haiku-20240307"),
        "local_model": config.get("local_model", "llama2"),
        "temperature": config.get("temperature", 0.7),
        "fallback_to_patterns": config.get("fallback_to_patterns", True),
    }


def set_openai_config(api_key: str, model: str = "gpt-3.5-turbo"):
    """Configure OpenAI API settings."""
    config = load_llm_config()
    config["openai_api_key"] = api_key
    config["openai_model"] = model
    config["provider"] = "openai"
    config["enabled"] = bool(api_key)
    save_llm_config(config)
    return config


def set_anthropic_config(api_key: str, model: str = "claude-3-haiku-20240307"):
    """Configure Anthropic API settings."""
    config = load_llm_config()
    config["anthropic_api_key"] = api_key
    config["anthropic_model"] = model
    config["provider"] = "anthropic"
    config["enabled"] = bool(api_key)
    save_llm_config(config)
    return config


def set_local_llm_config(endpoint: str, model: str = "llama2"):
    """Configure local LLM settings."""
    config = load_llm_config()
    config["local_endpoint"] = endpoint
    config["local_model"] = model
    config["provider"] = "local"
    config["enabled"] = bool(endpoint)
    save_llm_config(config)
    return config
