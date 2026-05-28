"""Dialog Manager - Multi-turn conversation handling with slot filling.

This module provides:
- Multi-turn dialog state management
- Slot filling for structured data collection
- Context-aware conversation flow
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

# ─── Dialog State ──────────────────────────────────────────────────────────────

class DialogState:
    """Represents the current state of a dialog flow."""
    
    def __init__(self, flow_name: str = None):
        self.flow_name = flow_name
        self.current_step = 0
        self.slots: Dict[str, Any] = {}
        self.confirmed_slots: Dict[str, Any] = {}
        self.pending_confirmation = False
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.last_updated = self.started_at
        self.turns = 0
        self.completed = False
        self.cancelled = False
    
    def set_slot(self, name: str, value: Any, confirmed: bool = False):
        """Set a slot value."""
        self.slots[name] = value
        if confirmed:
            self.confirmed_slots[name] = value
        self.last_updated = datetime.now(timezone.utc).isoformat()
    
    def get_slot(self, name: str, default: Any = None) -> Any:
        """Get a slot value."""
        return self.slots.get(name, default)
    
    def is_slot_filled(self, name: str) -> bool:
        """Check if a slot has a value."""
        return name in self.slots and self.slots[name] is not None
    
    def get_missing_slots(self, required_slots: List[str]) -> List[str]:
        """Get list of required slots that are not yet filled."""
        return [s for s in required_slots if not self.is_slot_filled(s)]
    
    def to_dict(self) -> dict:
        """Convert state to dictionary."""
        return {
            "flow_name": self.flow_name,
            "current_step": self.current_step,
            "slots": self.slots,
            "confirmed_slots": self.confirmed_slots,
            "pending_confirmation": self.pending_confirmation,
            "started_at": self.started_at,
            "last_updated": self.last_updated,
            "turns": self.turns,
            "completed": self.completed,
            "cancelled": self.cancelled,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DialogState":
        """Create state from dictionary."""
        state = cls(data.get("flow_name"))
        state.current_step = data.get("current_step", 0)
        state.slots = data.get("slots", {})
        state.confirmed_slots = data.get("confirmed_slots", {})
        state.pending_confirmation = data.get("pending_confirmation", False)
        state.started_at = data.get("started_at")
        state.last_updated = data.get("last_updated")
        state.turns = data.get("turns", 0)
        state.completed = data.get("completed", False)
        state.cancelled = data.get("cancelled", False)
        return state


# ─── Slot Definitions ──────────────────────────────────────────────────────────

class Slot:
    """Definition for a dialog slot."""
    
    def __init__(
        self,
        name: str,
        slot_type: str = "text",
        prompt: str = None,
        required: bool = True,
        validation: Callable[[Any], bool] = None,
        extraction_patterns: List[str] = None,
        default: Any = None,
        confirmation_prompt: str = None,
    ):
        self.name = name
        self.slot_type = slot_type  # text, number, choice, phone, name, direction
        self.prompt = prompt or f"Please provide {name}:"
        self.required = required
        self.validation = validation
        self.extraction_patterns = extraction_patterns or []
        self.default = default
        self.confirmation_prompt = confirmation_prompt
    
    def validate(self, value: Any) -> bool:
        """Validate slot value."""
        if value is None:
            return not self.required
        
        if self.validation:
            return self.validation(value)
        
        # Type-specific validation
        if self.slot_type == "number":
            try:
                int(value)
                return True
            except (ValueError, TypeError):
                return False
        elif self.slot_type == "phone":
            import re
            # Basic phone number validation
            return bool(re.match(r'^[\d\s\-\+\(\)]{7,}$', str(value)))
        elif self.slot_type == "direction":
            return str(value).lower() in ["incoming", "outgoing", "missed"]
        
        return True


# ─── Dialog Flows ──────────────────────────────────────────────────────────────

# Predefined dialog flows
DIALOG_FLOWS = {
    "add_call": {
        "name": "Add Call",
        "description": "Add a new call record",
        "slots": [
            Slot(
                name="contact_name",
                slot_type="name",
                prompt="Who was the call with? Please provide the contact name.",
                required=True,
                extraction_patterns=[
                    r"(?:with|from|to|called)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
                    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:called|phoned)",
                ],
            ),
            Slot(
                name="phone_number",
                slot_type="phone",
                prompt="What's their phone number? (You can skip if unknown)",
                required=False,
                extraction_patterns=[
                    r"(?:number|#|phone)[:\s]*(\+?[\d\s\-\(\)]{7,})",
                    r"(\+?[\d]{3}[\-\s]?[\d]{3}[\-\s]?[\d]{4})",
                ],
            ),
            Slot(
                name="direction",
                slot_type="direction",
                prompt="Was this an incoming, outgoing, or missed call?",
                required=True,
                extraction_patterns=[
                    r"(incoming|outgoing|missed)",
                    r"(?:I\s+)?(received|made|missed)",
                ],
            ),
            Slot(
                name="duration",
                slot_type="number",
                prompt="How long was the call in minutes? (Enter 0 for missed calls)",
                required=False,
                default=0,
                extraction_patterns=[
                    r"(\d+)\s*(?:minute|min|m)",
                    r"(\d+)\s*(?:second|sec|s)",
                    r"(?:for|lasted|duration)[:\s]*(\d+)",
                ],
            ),
            Slot(
                name="notes",
                slot_type="text",
                prompt="Any notes about this call? (Optional, say 'skip' or 'none')",
                required=False,
                default="",
            ),
        ],
        "confirmation_prompt": "I'll add a {direction} call with {contact_name}. Is that correct?",
        "success_message": "Great! I've logged the call with {contact_name}.",
        "cancel_message": "No problem, I've cancelled adding the call.",
    },
    
    "search_calls": {
        "name": "Search Calls",
        "description": "Search call records",
        "slots": [
            Slot(
                name="search_query",
                slot_type="text",
                prompt="What would you like to search for? (name, number, or keyword)",
                required=True,
                extraction_patterns=[
                    r"(?:search|find|look)\s+(?:for\s+)?(.+)",
                    r"(?:calls?\s+)?(?:from|with|to)\s+(.+)",
                ],
            ),
        ],
        "confirmation_prompt": None,  # No confirmation needed
        "success_message": "Here are the calls I found matching '{search_query}':",
        "cancel_message": "Search cancelled.",
    },
    
    "delete_call": {
        "name": "Delete Call",
        "description": "Delete a call record",
        "slots": [
            Slot(
                name="call_id",
                slot_type="number",
                prompt="Which call would you like to delete? Please provide the call ID number.",
                required=True,
                extraction_patterns=[
                    r"(?:call|record|id|#)\s*(\d+)",
                    r"(?:delete|remove)\s*(\d+)",
                ],
            ),
        ],
        "confirmation_prompt": "Are you sure you want to delete call #{call_id}?",
        "success_message": "Done! I've deleted call #{call_id}.",
        "cancel_message": "Okay, I won't delete that call.",
    },
}


# ─── Dialog Manager ────────────────────────────────────────────────────────────

class DialogManager:
    """Manages multi-turn dialog flows."""
    
    def __init__(self):
        self.state: Optional[DialogState] = None
        self.flows = DIALOG_FLOWS
    
    def start_flow(self, flow_name: str) -> dict:
        """Start a new dialog flow."""
        if flow_name not in self.flows:
            return {
                "success": False,
                "error": f"Unknown flow: {flow_name}",
            }
        
        self.state = DialogState(flow_name)
        flow = self.flows[flow_name]
        
        # Get first unfilled required slot
        slots = flow["slots"]
        first_slot = slots[0] if slots else None
        
        return {
            "success": True,
            "flow_name": flow_name,
            "prompt": first_slot.prompt if first_slot else "Ready to proceed.",
            "current_slot": first_slot.name if first_slot else None,
            "state": self.state.to_dict(),
        }
    
    def process_input(self, user_input: str) -> dict:
        """Process user input within the current dialog flow."""
        if not self.state or not self.state.flow_name:
            return {
                "success": False,
                "in_flow": False,
                "error": "No active dialog flow",
            }
        
        self.state.turns += 1
        flow = self.flows[self.state.flow_name]
        slots = flow["slots"]
        
        # Check for cancellation
        if self._is_cancel_intent(user_input):
            self.state.cancelled = True
            result = {
                "success": True,
                "in_flow": False,
                "completed": False,
                "cancelled": True,
                "response": flow.get("cancel_message", "Dialog cancelled."),
                "state": self.state.to_dict(),
            }
            self.state = None
            return result
        
        # Handle confirmation if pending
        if self.state.pending_confirmation:
            return self._handle_confirmation(user_input)
        
        # Find current slot to fill
        current_slot = None
        for slot in slots:
            if not self.state.is_slot_filled(slot.name) and slot.required:
                current_slot = slot
                break
        
        # If no required slots left, try optional ones
        if not current_slot:
            for slot in slots:
                if not self.state.is_slot_filled(slot.name):
                    current_slot = slot
                    break
        
        if current_slot:
            # Try to extract slot value from input
            extracted_value = self._extract_slot_value(user_input, current_slot)
            
            if extracted_value is not None:
                # Validate and set slot
                if current_slot.validate(extracted_value):
                    self.state.set_slot(current_slot.name, extracted_value)
                else:
                    return {
                        "success": True,
                        "in_flow": True,
                        "prompt": f"That doesn't seem right. {current_slot.prompt}",
                        "current_slot": current_slot.name,
                        "state": self.state.to_dict(),
                    }
            else:
                # Check for skip intent on optional slots
                if not current_slot.required and self._is_skip_intent(user_input):
                    self.state.set_slot(current_slot.name, current_slot.default)
                else:
                    # Couldn't extract value, re-prompt
                    return {
                        "success": True,
                        "in_flow": True,
                        "prompt": current_slot.prompt,
                        "current_slot": current_slot.name,
                        "state": self.state.to_dict(),
                    }
        
        # Check if all required slots are filled
        missing = self.state.get_missing_slots([s.name for s in slots if s.required])
        
        if missing:
            # Find next slot to fill
            next_slot = next((s for s in slots if s.name in missing), None)
            return {
                "success": True,
                "in_flow": True,
                "prompt": next_slot.prompt if next_slot else "Please provide more information.",
                "current_slot": next_slot.name if next_slot else None,
                "state": self.state.to_dict(),
            }
        
        # All required slots filled - check for confirmation
        if flow.get("confirmation_prompt"):
            self.state.pending_confirmation = True
            confirmation_text = self._format_template(
                flow["confirmation_prompt"],
                self.state.slots
            )
            return {
                "success": True,
                "in_flow": True,
                "awaiting_confirmation": True,
                "prompt": confirmation_text,
                "state": self.state.to_dict(),
            }
        
        # Complete the flow
        return self._complete_flow()
    
    def _handle_confirmation(self, user_input: str) -> dict:
        """Handle confirmation response."""
        flow = self.flows[self.state.flow_name]
        
        if self._is_affirmative(user_input):
            # Confirm all slots
            self.state.confirmed_slots = self.state.slots.copy()
            return self._complete_flow()
        elif self._is_negative(user_input):
            self.state.cancelled = True
            result = {
                "success": True,
                "in_flow": False,
                "completed": False,
                "cancelled": True,
                "response": flow.get("cancel_message", "Dialog cancelled."),
                "state": self.state.to_dict(),
            }
            self.state = None
            return result
        else:
            # Re-prompt for confirmation
            confirmation_text = self._format_template(
                flow["confirmation_prompt"],
                self.state.slots
            )
            return {
                "success": True,
                "in_flow": True,
                "awaiting_confirmation": True,
                "prompt": f"Please confirm: {confirmation_text} (yes/no)",
                "state": self.state.to_dict(),
            }
    
    def _complete_flow(self) -> dict:
        """Complete the current dialog flow."""
        flow = self.flows[self.state.flow_name]
        self.state.completed = True
        
        success_message = self._format_template(
            flow.get("success_message", "Done!"),
            self.state.slots
        )
        
        result = {
            "success": True,
            "in_flow": False,
            "completed": True,
            "response": success_message,
            "collected_data": self.state.slots.copy(),
            "state": self.state.to_dict(),
        }
        
        # Reset state
        completed_state = self.state
        self.state = None
        
        return result
    
    def _extract_slot_value(self, text: str, slot: Slot) -> Any:
        """Extract slot value from text."""
        import re
        
        text_lower = text.lower().strip()
        
        # Try extraction patterns
        for pattern in slot.extraction_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                
                # Convert direction synonyms
                if slot.slot_type == "direction":
                    value = value.lower()
                    if value == "received":
                        value = "incoming"
                    elif value == "made":
                        value = "outgoing"
                
                # Convert duration to seconds
                if slot.slot_type == "number" and slot.name == "duration":
                    try:
                        value = int(value)
                        # Check if it was in minutes
                        if "min" in text_lower:
                            value = value * 60
                    except ValueError:
                        continue
                
                return value
        
        # For simple text slots, use the whole input
        if slot.slot_type == "text" and len(text.strip()) > 0:
            return text.strip()
        
        # For name slots, try to extract capitalized words
        if slot.slot_type == "name":
            name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
            if name_match:
                return name_match.group(1)
            # Fallback: use input if it looks like a name
            if text.strip() and not any(c.isdigit() for c in text):
                return text.strip().title()
        
        # For phone slots
        if slot.slot_type == "phone":
            phone_match = re.search(r'(\+?[\d\s\-\(\)]{7,})', text)
            if phone_match:
                return phone_match.group(1).strip()
        
        # For direction slots
        if slot.slot_type == "direction":
            if "incoming" in text_lower or "received" in text_lower:
                return "incoming"
            elif "outgoing" in text_lower or "made" in text_lower:
                return "outgoing"
            elif "missed" in text_lower:
                return "missed"
        
        # For number slots
        if slot.slot_type == "number":
            num_match = re.search(r'(\d+)', text)
            if num_match:
                return int(num_match.group(1))
        
        return None
    
    def _format_template(self, template: str, data: dict) -> str:
        """Format a template string with slot data."""
        try:
            return template.format(**data)
        except KeyError:
            # Handle missing keys gracefully
            import re
            def replace(match):
                key = match.group(1)
                return str(data.get(key, f"[{key}]"))
            return re.sub(r'\{(\w+)\}', replace, template)
    
    def _is_cancel_intent(self, text: str) -> bool:
        """Check if input indicates cancellation."""
        cancel_phrases = ["cancel", "stop", "quit", "abort", "nevermind", "never mind", "forget it"]
        text_lower = text.lower().strip()
        return any(phrase in text_lower for phrase in cancel_phrases)
    
    def _is_skip_intent(self, text: str) -> bool:
        """Check if input indicates skipping."""
        skip_phrases = ["skip", "none", "no", "pass", "next", "n/a", "na", "nothing"]
        text_lower = text.lower().strip()
        return text_lower in skip_phrases or any(phrase == text_lower for phrase in skip_phrases)
    
    def _is_affirmative(self, text: str) -> bool:
        """Check if input is affirmative."""
        affirmative = ["yes", "yeah", "yep", "yup", "sure", "correct", "right", "ok", "okay", "confirm", "y", "absolutely", "definitely"]
        text_lower = text.lower().strip()
        return text_lower in affirmative
    
    def _is_negative(self, text: str) -> bool:
        """Check if input is negative."""
        negative = ["no", "nope", "nah", "wrong", "incorrect", "cancel", "n"]
        text_lower = text.lower().strip()
        return text_lower in negative
    
    def is_in_flow(self) -> bool:
        """Check if currently in a dialog flow."""
        return self.state is not None and not self.state.completed and not self.state.cancelled
    
    def get_current_flow(self) -> Optional[str]:
        """Get the name of the current flow."""
        return self.state.flow_name if self.state else None
    
    def cancel_flow(self) -> dict:
        """Cancel the current flow."""
        if not self.state:
            return {"success": False, "error": "No active flow"}
        
        flow = self.flows.get(self.state.flow_name, {})
        self.state.cancelled = True
        result = {
            "success": True,
            "response": flow.get("cancel_message", "Dialog cancelled."),
        }
        self.state = None
        return result
    
    def get_state(self) -> Optional[dict]:
        """Get current dialog state."""
        return self.state.to_dict() if self.state else None


# ─── Global Instance ───────────────────────────────────────────────────────────

dialog_manager = DialogManager()


def get_dialog_manager() -> DialogManager:
    """Get the global dialog manager instance."""
    return dialog_manager


def start_dialog(flow_name: str) -> dict:
    """Start a new dialog flow."""
    return dialog_manager.start_flow(flow_name)


def process_dialog_input(user_input: str) -> dict:
    """Process input in the current dialog."""
    return dialog_manager.process_input(user_input)


def is_in_dialog() -> bool:
    """Check if currently in a dialog."""
    return dialog_manager.is_in_flow()


def cancel_dialog() -> dict:
    """Cancel the current dialog."""
    return dialog_manager.cancel_flow()
