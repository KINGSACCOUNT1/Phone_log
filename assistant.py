"""Phone Log Assistant - conversational AI assistant for managing phone calls."""

import json
import os
import re
from datetime import datetime, timezone

import phone_log
import personas

# ─── Assistant Identity ────────────────────────────────────────────────────────

_DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))  # resolved data directory
IDENTITY_FILE = os.path.join(_DATA_DIR, "assistant_identity.json")

DEFAULT_IDENTITY = {
    "name": "Luna",
    "role": "Phone Log Assistant",
    "personality": "friendly, helpful, and concise",
    "greeting": "Hello dear, how are you doing today?",
    "voice": "female",
    "persona_id": None,
}


def load_identity():
    """Load assistant identity from file, or return defaults."""
    if os.path.exists(IDENTITY_FILE):
        with open(IDENTITY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_IDENTITY.copy()


def save_identity(identity):
    """Save assistant identity to file."""
    with open(IDENTITY_FILE, "w", encoding="utf-8") as f:
        json.dump(identity, f, indent=2)


def update_identity(name=None, role=None, personality=None, greeting=None, voice=None):
    """Update specific identity fields."""
    identity = load_identity()
    if name is not None:
        identity["name"] = name.strip()
    if role is not None:
        identity["role"] = role.strip()
    if personality is not None:
        identity["personality"] = personality.strip()
    if greeting is not None:
        identity["greeting"] = greeting.strip()
    if voice is not None:
        identity["voice"] = voice.strip()
    save_identity(identity)
    return identity


def set_persona(persona_id):
    """Set the assistant to use a predefined persona."""
    persona_identity = personas.persona_to_identity(persona_id)
    if persona_identity:
        save_identity(persona_identity)
        return persona_identity
    return None


def get_available_personas():
    """Get list of available personas."""
    return personas.list_personas()


# ─── Intent Recognition ────────────────────────────────────────────────────────

# Confidence scores for intent matching
CONFIDENCE_HIGH = 0.8    # Pattern matched successfully
CONFIDENCE_LOW = 0.2     # No pattern matched, fallback to unknown

INTENT_PATTERNS = {
    "add_call": [
        r"(?:add|log|record|create)\s+(?:a\s+)?(?:new\s+)?(?:call|phone call)",
        r"(?:i\s+)?(?:had|got|received|made|missed)\s+(?:a\s+)?(?:call|phone call)",
        r"(?:log|add)\s+(?:that\s+)?(.+?)\s+called",
    ],
    "list_calls": [
        r"(?:show|list|display|get|view)\s+(?:all\s+)?(?:my\s+)?(?:calls|call log|phone calls|records)",
        r"what\s+(?:calls|phone calls)\s+(?:do i have|are there)",
        r"(?:show|list)\s+(?:me\s+)?(?:my\s+)?(?:recent\s+)?calls",
    ],
    "search_calls": [
        r"(?:search|find|look for|look up)\s+(?:calls?\s+)?(?:from|by|for|with)?\s*(.+)",
        r"(?:any|show)\s+calls?\s+(?:from|with|to)\s+(.+)",
        r"(?:did|has)\s+(.+?)\s+call(?:ed)?",
    ],
    "delete_call": [
        r"(?:delete|remove|erase)\s+(?:call\s+)?(?:record\s+)?(?:id\s+)?(\d+)",
        r"(?:remove|delete)\s+(?:the\s+)?(?:last\s+)?call",
    ],
    "greeting": [
        r"^(?:hi|hello|hey|good\s+(?:morning|afternoon|evening)|howdy)(?:\s|$|!|\?|,)",
        r"^(?:what's up|sup|yo)(?:\s|$|!|\?)",
    ],
    "help": [
        r"(?:what\s+can\s+you\s+do|help|commands|how\s+do\s+i)",
        r"(?:show|tell)\s+(?:me\s+)?(?:what\s+you\s+can\s+do|your\s+capabilities)",
    ],
    "identity": [
        r"(?:who\s+are\s+you|what(?:'s|\s+is)\s+your\s+name|introduce\s+yourself)",
        r"(?:tell\s+me\s+about\s+yourself)",
    ],
    "full_name": [
        r"(?:what(?:'s|\s+is)\s+your\s+full\s+name)",
        r"(?:your\s+full\s+name)",
        r"(?:tell\s+me\s+your\s+full\s+name)",
    ],
    "stats": [
        r"(?:how\s+many|count|total)\s+(?:calls|records)",
        r"(?:give\s+me\s+)?(?:call\s+)?(?:statistics|stats|summary)",
    ],
}


def recognize_intent(text):
    """
    Recognize user intent from natural language text.
    
    Returns:
        tuple: (intent_name, extracted_entities, confidence)
    """
    text = text.strip().lower()
    
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities = match.groups() if match.groups() else ()
                return (intent, entities, CONFIDENCE_HIGH)
    
    # Default fallback
    return ("unknown", (), CONFIDENCE_LOW)


# ─── Response Generation ───────────────────────────────────────────────────────

def generate_response(user_input):
    """
    Process user input and generate assistant response with reasoning.
    
    Returns:
        dict: {
            "reasoning": str,       # Assistant's thought process
            "response": str,        # Final response to user
            "action_taken": str,    # What action was performed (if any)
            "data": any             # Any relevant data (e.g., call records)
        }
    """
    identity = load_identity()
    assistant_name = identity["name"]
    
    intent, entities, confidence = recognize_intent(user_input)
    
    result = {
        "reasoning": "",
        "response": "",
        "action_taken": None,
        "data": None,
    }
    
    # ─── Handle each intent ────────────────────────────────────────────────────
    
    # Get persona ID if using a persona
    persona_id = identity.get("persona_id")
    
    if intent == "greeting":
        result["reasoning"] = (
            f"User greeted me. I should respond warmly and wait for their response "
            f"before providing any additional information."
        )
        # Use persona-specific greeting if available
        if persona_id:
            response = identity.get("greeting", "Hello dear, how are you doing today?")
            response = personas.add_speech_flavor(persona_id, response)
            result["response"] = response
        else:
            result["response"] = "Hello dear, how are you doing today?"
        result["action_taken"] = "greeted_user"
    
    elif intent == "full_name":
        result["reasoning"] = (
            f"User is asking for my full name. I'll provide it if I have one."
        )
        full_name = identity.get("full_name", assistant_name)
        if persona_id:
            if persona_id == "lamai":
                result["response"] = f"Ohh, hmmm... my full name is {full_name}. But please, just call me {assistant_name}!"
            elif persona_id == "coach_jv":
                result["response"] = f"My full name is {full_name}. But everyone calls me {assistant_name}!"
            else:
                result["response"] = f"My full name is {full_name}."
        else:
            result["response"] = f"My name is {assistant_name}."
        result["action_taken"] = "told_full_name"
        
    elif intent == "identity":
        result["reasoning"] = (
            f"User wants to know about me. I'll introduce myself as {assistant_name}, "
            f"the {identity['role']}."
        )
        # Use persona-specific intro if available
        if persona_id:
            result["response"] = personas.format_persona_intro(persona_id)
        else:
            result["response"] = (
                f"I'm {assistant_name}, your {identity['role']}! "
                f"I'm {identity['personality']}. I can help you log calls, search your "
                f"call history, and manage your phone records. Just ask!"
            )
        result["action_taken"] = "introduced_self"
        
    elif intent == "help":
        result["reasoning"] = (
            "User needs help understanding my capabilities. I'll list what I can do "
            "in a clear and friendly way."
        )
        help_text = (
            f"Here's what I can help you with:\n\n"
            f"📞 **Add a call**: Say 'Log a call from [name]' or 'I had a call with [name]'\n"
            f"📋 **View calls**: Say 'Show my calls' or 'List all calls'\n"
            f"🔍 **Search**: Say 'Find calls from [name]' or 'Search for [number]'\n"
            f"🗑️ **Delete**: Say 'Delete call 5' to remove a record\n"
            f"📊 **Stats**: Say 'How many calls do I have?'\n\n"
            f"Just speak naturally – I'll do my best to understand!"
        )
        if persona_id:
            help_text = personas.add_speech_flavor(persona_id, help_text)
        result["response"] = help_text
        result["action_taken"] = "showed_help"
        
    elif intent == "list_calls":
        result["reasoning"] = (
            "User wants to see their call history. I'll fetch all calls and "
            "present them in a readable format."
        )
        calls = phone_log.get_all()
        if calls:
            result["response"] = f"Here are your {len(calls)} most recent call(s):"
            result["data"] = calls
        else:
            result["response"] = "You don't have any calls logged yet. Would you like to add one?"
        result["action_taken"] = "listed_calls"
        
    elif intent == "search_calls":
        query = entities[0].strip() if entities else ""
        if query:
            result["reasoning"] = (
                f"User is searching for calls related to '{query}'. "
                f"I'll search both contact names and phone numbers."
            )
            calls = phone_log.search(query)
            if calls:
                result["response"] = f"Found {len(calls)} call(s) matching '{query}':"
                result["data"] = calls
            else:
                result["response"] = f"No calls found matching '{query}'. Try a different search term?"
        else:
            result["reasoning"] = "User wants to search but didn't specify what. I'll ask for clarification."
            result["response"] = "What would you like me to search for? You can search by name or phone number."
        result["action_taken"] = "searched_calls"
        
    elif intent == "stats":
        result["reasoning"] = (
            "User wants call statistics. I'll calculate counts for each call type "
            "and present a summary."
        )
        calls = phone_log.get_all()
        incoming = len([c for c in calls if c["direction"] == "incoming"])
        outgoing = len([c for c in calls if c["direction"] == "outgoing"])
        missed = len([c for c in calls if c["direction"] == "missed"])
        
        result["response"] = (
            f"📊 **Call Statistics**\n\n"
            f"Total calls: {len(calls)}\n"
            f"↙️ Incoming: {incoming}\n"
            f"↗️ Outgoing: {outgoing}\n"
            f"✗ Missed: {missed}"
        )
        result["action_taken"] = "showed_stats"
        result["data"] = {
            "total": len(calls),
            "incoming": incoming,
            "outgoing": outgoing,
            "missed": missed,
        }
        
    elif intent == "add_call":
        result["reasoning"] = (
            "User wants to add a call. Since I need more details (name, number, direction), "
            "I'll guide them through the process or ask for the missing information."
        )
        result["response"] = (
            "I'd be happy to log a call for you! Please provide:\n\n"
            "• **Contact name**: Who called?\n"
            "• **Phone number**: What's their number?\n"
            "• **Direction**: Was it incoming, outgoing, or missed?\n\n"
            "Or use the form below to add the details."
        )
        result["action_taken"] = "prompted_add_call"
        
    elif intent == "delete_call":
        if entities and entities[0]:
            call_id = int(entities[0])
            result["reasoning"] = f"User wants to delete call ID {call_id}. I'll attempt to remove it."
            if phone_log.delete_call(call_id):
                result["response"] = f"✓ Deleted call record #{call_id}."
                result["action_taken"] = "deleted_call"
            else:
                result["response"] = f"I couldn't find a call with ID #{call_id}. Check the ID and try again?"
                result["action_taken"] = "delete_failed"
        else:
            result["reasoning"] = "User wants to delete a call but didn't specify which one."
            result["response"] = "Which call would you like me to delete? Please provide the call ID number."
            result["action_taken"] = "prompted_delete"
            
    else:  # unknown intent
        result["reasoning"] = (
            f"I'm not sure what the user means by '{user_input}'. "
            f"I'll politely ask for clarification and offer suggestions."
        )
        result["response"] = (
            f"I'm not quite sure what you mean. Could you try rephrasing?\n\n"
            f"You can ask me to:\n"
            f"• Show your calls\n"
            f"• Search for a contact\n"
            f"• Add a new call\n"
            f"• Get call statistics"
        )
        result["action_taken"] = "asked_clarification"
    
    return result


# ─── Conversation History ──────────────────────────────────────────────────────

class ConversationManager:
    """Manages conversation history for context-aware responses."""
    
    def __init__(self, max_history=20):
        self.history = []
        self.max_history = max_history
    
    def add_exchange(self, user_input, assistant_response):
        """Add a conversation exchange to history."""
        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user_input,
            "assistant": assistant_response,
        })
        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_history(self):
        """Return conversation history."""
        return self.history.copy()
    
    def clear(self):
        """Clear conversation history."""
        self.history = []


# Global conversation manager instance
conversation = ConversationManager()


def chat(user_input):
    """
    Main chat function - process input and maintain conversation history.
    
    Returns:
        dict: Full response including reasoning, response text, and any data
    """
    result = generate_response(user_input)
    conversation.add_exchange(user_input, result["response"])
    return result
