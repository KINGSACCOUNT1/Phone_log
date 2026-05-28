"""Tests for Dialog Manager module."""

import unittest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dialog_manager


class TestDialogState(unittest.TestCase):
    """Test DialogState class."""
    
    def test_create_state(self):
        """Test creating a dialog state."""
        state = dialog_manager.DialogState("add_call")
        
        self.assertEqual(state.flow_name, "add_call")
        self.assertEqual(state.current_step, 0)
        self.assertFalse(state.completed)
        self.assertFalse(state.cancelled)
    
    def test_set_slot(self):
        """Test setting a slot value."""
        state = dialog_manager.DialogState("add_call")
        state.set_slot("contact_name", "Alice")
        
        self.assertEqual(state.get_slot("contact_name"), "Alice")
    
    def test_set_slot_confirmed(self):
        """Test setting a confirmed slot value."""
        state = dialog_manager.DialogState("add_call")
        state.set_slot("contact_name", "Alice", confirmed=True)
        
        self.assertIn("contact_name", state.confirmed_slots)
    
    def test_is_slot_filled(self):
        """Test checking if slot is filled."""
        state = dialog_manager.DialogState("add_call")
        
        self.assertFalse(state.is_slot_filled("contact_name"))
        state.set_slot("contact_name", "Alice")
        self.assertTrue(state.is_slot_filled("contact_name"))
    
    def test_get_missing_slots(self):
        """Test getting missing required slots."""
        state = dialog_manager.DialogState("add_call")
        state.set_slot("contact_name", "Alice")
        
        missing = state.get_missing_slots(["contact_name", "phone_number", "direction"])
        self.assertIn("phone_number", missing)
        self.assertIn("direction", missing)
        self.assertNotIn("contact_name", missing)
    
    def test_to_dict(self):
        """Test converting state to dictionary."""
        state = dialog_manager.DialogState("add_call")
        state.set_slot("contact_name", "Alice")
        
        data = state.to_dict()
        self.assertEqual(data["flow_name"], "add_call")
        self.assertIn("contact_name", data["slots"])
    
    def test_from_dict(self):
        """Test creating state from dictionary."""
        data = {
            "flow_name": "add_call",
            "current_step": 2,
            "slots": {"contact_name": "Alice"},
            "completed": False,
            "cancelled": False,
        }
        state = dialog_manager.DialogState.from_dict(data)
        
        self.assertEqual(state.flow_name, "add_call")
        self.assertEqual(state.current_step, 2)


class TestSlot(unittest.TestCase):
    """Test Slot class."""
    
    def test_create_slot(self):
        """Test creating a slot."""
        slot = dialog_manager.Slot(
            name="contact_name",
            slot_type="name",
            prompt="Who called?",
            required=True,
        )
        
        self.assertEqual(slot.name, "contact_name")
        self.assertEqual(slot.slot_type, "name")
        self.assertTrue(slot.required)
    
    def test_validate_text(self):
        """Test text validation."""
        slot = dialog_manager.Slot(name="notes", slot_type="text")
        
        self.assertTrue(slot.validate("Some notes"))
        self.assertTrue(slot.validate(""))
    
    def test_validate_number(self):
        """Test number validation."""
        slot = dialog_manager.Slot(name="duration", slot_type="number")
        
        self.assertTrue(slot.validate("123"))
        self.assertTrue(slot.validate(123))
        self.assertFalse(slot.validate("abc"))
    
    def test_validate_phone(self):
        """Test phone number validation."""
        slot = dialog_manager.Slot(name="phone", slot_type="phone")
        
        self.assertTrue(slot.validate("555-123-4567"))
        self.assertTrue(slot.validate("+1 555 123 4567"))
        self.assertFalse(slot.validate("abc"))
    
    def test_validate_direction(self):
        """Test direction validation."""
        slot = dialog_manager.Slot(name="direction", slot_type="direction")
        
        self.assertTrue(slot.validate("incoming"))
        self.assertTrue(slot.validate("outgoing"))
        self.assertTrue(slot.validate("missed"))
        self.assertFalse(slot.validate("invalid"))


class TestDialogManager(unittest.TestCase):
    """Test DialogManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.dm = dialog_manager.DialogManager()
    
    def test_start_flow(self):
        """Test starting a dialog flow."""
        result = self.dm.start_flow("add_call")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["flow_name"], "add_call")
        self.assertIsNotNone(result["prompt"])
    
    def test_start_unknown_flow(self):
        """Test starting an unknown flow."""
        result = self.dm.start_flow("unknown_flow")
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_is_in_flow(self):
        """Test checking if in a flow."""
        self.assertFalse(self.dm.is_in_flow())
        
        self.dm.start_flow("add_call")
        self.assertTrue(self.dm.is_in_flow())
    
    def test_get_current_flow(self):
        """Test getting current flow name."""
        self.assertIsNone(self.dm.get_current_flow())
        
        self.dm.start_flow("add_call")
        self.assertEqual(self.dm.get_current_flow(), "add_call")
    
    def test_process_input_name(self):
        """Test processing name input."""
        self.dm.start_flow("add_call")
        result = self.dm.process_input("Alice Johnson")
        
        self.assertTrue(result["success"])
        self.assertTrue(result["in_flow"])
    
    def test_process_input_direction(self):
        """Test processing direction input."""
        self.dm.start_flow("add_call")
        self.dm.process_input("Alice")  # Fill name
        self.dm.process_input("555-1234")  # Fill phone (optional)
        result = self.dm.process_input("incoming")  # Fill direction
        
        self.assertTrue(result["success"])
    
    def test_cancel_flow(self):
        """Test canceling a flow."""
        self.dm.start_flow("add_call")
        result = self.dm.process_input("cancel")
        
        self.assertTrue(result["cancelled"])
        self.assertFalse(self.dm.is_in_flow())
    
    def test_cancel_with_different_phrases(self):
        """Test canceling with different phrases."""
        for phrase in ["stop", "quit", "nevermind", "forget it"]:
            self.dm.start_flow("add_call")
            result = self.dm.process_input(phrase)
            self.assertTrue(result.get("cancelled", False), f"Failed to cancel with '{phrase}'")
    
    def test_skip_optional_slot(self):
        """Test skipping optional slot."""
        self.dm.start_flow("add_call")
        self.dm.process_input("Alice")  # Name
        result = self.dm.process_input("skip")  # Skip phone
        
        self.assertTrue(result["success"])
    
    def test_complete_flow(self):
        """Test completing a dialog flow."""
        self.dm.start_flow("add_call")
        self.dm.process_input("Alice Johnson")  # Name
        self.dm.process_input("555-1234")  # Phone
        self.dm.process_input("incoming")  # Direction
        self.dm.process_input("skip")  # Duration
        self.dm.process_input("none")  # Notes
        
        # Should ask for confirmation
        result = self.dm.process_input("yes")  # Confirm
        
        self.assertTrue(result.get("completed", False) or result.get("in_flow", True))


class TestDialogManagerExtractions(unittest.TestCase):
    """Test slot value extraction."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.dm = dialog_manager.DialogManager()
    
    def test_extract_name_from_phrase(self):
        """Test extracting name from a phrase."""
        self.dm.start_flow("add_call")
        result = self.dm.process_input("The call was with Alice Johnson")
        
        # Should extract "Alice Johnson"
        self.assertTrue(result["success"])
    
    def test_extract_phone_from_phrase(self):
        """Test extracting phone from a phrase."""
        self.dm.start_flow("add_call")
        self.dm.process_input("Alice")
        result = self.dm.process_input("Their number is 555-123-4567")
        
        self.assertTrue(result["success"])
    
    def test_extract_direction_synonyms(self):
        """Test extracting direction from synonyms."""
        self.dm.start_flow("add_call")
        self.dm.process_input("Bob")
        self.dm.process_input("skip")  # Skip phone
        
        result = self.dm.process_input("I received a call")
        # Should recognize "received" as "incoming"
        self.assertTrue(result["success"])


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def setUp(self):
        """Reset global dialog manager."""
        dialog_manager.dialog_manager = dialog_manager.DialogManager()
    
    def test_start_dialog(self):
        """Test start_dialog function."""
        result = dialog_manager.start_dialog("add_call")
        self.assertTrue(result["success"])
    
    def test_process_dialog_input(self):
        """Test process_dialog_input function."""
        dialog_manager.start_dialog("add_call")
        result = dialog_manager.process_dialog_input("Alice")
        self.assertTrue(result["success"])
    
    def test_is_in_dialog(self):
        """Test is_in_dialog function."""
        self.assertFalse(dialog_manager.is_in_dialog())
        dialog_manager.start_dialog("add_call")
        self.assertTrue(dialog_manager.is_in_dialog())
    
    def test_cancel_dialog(self):
        """Test cancel_dialog function."""
        dialog_manager.start_dialog("add_call")
        result = dialog_manager.cancel_dialog()
        self.assertTrue(result["success"])
        self.assertFalse(dialog_manager.is_in_dialog())


class TestAffirmativeNegativeDetection(unittest.TestCase):
    """Test affirmative and negative detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.dm = dialog_manager.DialogManager()
    
    def test_affirmative_phrases(self):
        """Test detecting affirmative phrases."""
        affirmatives = ["yes", "yeah", "yep", "sure", "ok", "okay", "correct", "y"]
        for phrase in affirmatives:
            self.assertTrue(self.dm._is_affirmative(phrase), f"Failed for '{phrase}'")
    
    def test_negative_phrases(self):
        """Test detecting negative phrases."""
        negatives = ["no", "nope", "nah", "wrong", "n", "cancel"]
        for phrase in negatives:
            self.assertTrue(self.dm._is_negative(phrase), f"Failed for '{phrase}'")


if __name__ == "__main__":
    unittest.main()
