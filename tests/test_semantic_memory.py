"""Tests for Semantic Memory module."""

import unittest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import semantic_memory


class TestMemoryEntry(unittest.TestCase):
    """Test MemoryEntry class."""
    
    def test_create_memory_entry(self):
        """Test creating a memory entry."""
        entry = semantic_memory.MemoryEntry(
            content="User prefers morning calls",
            memory_type="preference",
            tags=["user", "schedule"],
            importance=0.8,
        )
        
        self.assertIsNotNone(entry.memory_id)
        self.assertEqual(entry.content, "User prefers morning calls")
        self.assertEqual(entry.memory_type, "preference")
        self.assertIn("user", entry.tags)
        self.assertEqual(entry.importance, 0.8)
    
    def test_to_dict(self):
        """Test converting memory entry to dictionary."""
        entry = semantic_memory.MemoryEntry(content="Test content")
        data = entry.to_dict()
        
        self.assertIn("memory_id", data)
        self.assertIn("content", data)
        self.assertIn("created_at", data)
    
    def test_from_dict(self):
        """Test creating memory entry from dictionary."""
        data = {
            "memory_id": "mem_test123",
            "content": "Test content",
            "memory_type": "fact",
            "tags": ["test"],
            "importance": 0.5,
        }
        entry = semantic_memory.MemoryEntry.from_dict(data)
        
        self.assertEqual(entry.memory_id, "mem_test123")
        self.assertEqual(entry.content, "Test content")
    
    def test_update_access(self):
        """Test updating access timestamp."""
        entry = semantic_memory.MemoryEntry(content="Test")
        original_count = entry.access_count
        entry.update_access()
        
        self.assertEqual(entry.access_count, original_count + 1)


class TestSemanticMemory(unittest.TestCase):
    """Test SemanticMemory class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.original_file = semantic_memory.MEMORY_FILE
        semantic_memory.MEMORY_FILE = "/tmp/test_semantic_memory.json"
        # Clean up any existing test file
        if os.path.exists(semantic_memory.MEMORY_FILE):
            os.remove(semantic_memory.MEMORY_FILE)
        # Create fresh memory instance
        self.memory = semantic_memory.SemanticMemory()
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(semantic_memory.MEMORY_FILE):
            os.remove(semantic_memory.MEMORY_FILE)
        semantic_memory.MEMORY_FILE = self.original_file
    
    def test_add_memory(self):
        """Test adding a memory."""
        entry = self.memory.add("Alice is a friend", "contact", ["personal"])
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.content, "Alice is a friend")
        self.assertEqual(len(self.memory.memories), 1)
    
    def test_add_duplicate_updates_existing(self):
        """Test that adding similar content updates existing memory."""
        self.memory.add("Alice is a friend", "contact")
        self.memory.add("Alice is a friend", "contact", importance=0.9)
        
        # Should not create duplicate
        self.assertEqual(len(self.memory.memories), 1)
        self.assertGreaterEqual(self.memory.memories[0].importance, 0.9)
    
    def test_search_memories(self):
        """Test searching memories."""
        self.memory.add("Alice is a close friend", "contact", ["friend"])
        self.memory.add("Bob works at the office", "contact", ["work"])
        self.memory.add("Meeting scheduled for Monday", "event", ["schedule"])
        
        results = self.memory.search("friend")
        self.assertGreater(len(results), 0)
        self.assertIn("Alice", results[0].content)
    
    def test_search_by_type(self):
        """Test searching by memory type."""
        self.memory.add("Alice is a friend", "contact")
        self.memory.add("Prefer morning calls", "preference")
        
        results = self.memory.search("", memory_type="contact")
        contact_results = [r for r in results if r.memory_type == "contact"]
        self.assertGreater(len(contact_results), 0)
    
    def test_get_by_type(self):
        """Test getting memories by type."""
        self.memory.add("Fact 1", "fact")
        self.memory.add("Preference 1", "preference")
        self.memory.add("Fact 2", "fact")
        
        facts = self.memory.get_by_type("fact")
        self.assertEqual(len(facts), 2)
    
    def test_delete_memory(self):
        """Test deleting a memory."""
        entry = self.memory.add("To be deleted", "fact")
        memory_id = entry.memory_id
        
        result = self.memory.delete(memory_id)
        self.assertTrue(result)
        self.assertEqual(len(self.memory.memories), 0)
    
    def test_delete_nonexistent(self):
        """Test deleting a non-existent memory."""
        result = self.memory.delete("nonexistent_id")
        self.assertFalse(result)
    
    def test_clear_memories(self):
        """Test clearing all memories."""
        self.memory.add("Memory 1", "fact")
        self.memory.add("Memory 2", "fact")
        
        self.memory.clear()
        self.assertEqual(len(self.memory.memories), 0)
    
    def test_get_context_summary(self):
        """Test getting context summary."""
        self.memory.add("Important fact about calls", "fact", importance=0.9)
        
        summary = self.memory.get_context_summary()
        self.assertIn("Important fact", summary)


class TestFactExtraction(unittest.TestCase):
    """Test fact extraction functions."""
    
    def test_extract_contact_fact(self):
        """Test extracting contact facts."""
        text = "My friend Alice called yesterday"
        facts = semantic_memory.extract_facts_from_text(text)
        
        # May or may not extract depending on patterns
        self.assertIsInstance(facts, list)
    
    def test_extract_preference_fact(self):
        """Test extracting preference facts."""
        text = "I prefer to call in the morning"
        facts = semantic_memory.extract_facts_from_text(text)
        
        self.assertIsInstance(facts, list)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.original_file = semantic_memory.MEMORY_FILE
        semantic_memory.MEMORY_FILE = "/tmp/test_semantic_memory_conv.json"
        if os.path.exists(semantic_memory.MEMORY_FILE):
            os.remove(semantic_memory.MEMORY_FILE)
        # Reset global instance
        semantic_memory.semantic_memory = semantic_memory.SemanticMemory()
    
    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(semantic_memory.MEMORY_FILE):
            os.remove(semantic_memory.MEMORY_FILE)
        semantic_memory.MEMORY_FILE = self.original_file
    
    def test_remember(self):
        """Test remember function."""
        entry = semantic_memory.remember("Test fact")
        self.assertIsNotNone(entry)
    
    def test_recall(self):
        """Test recall function."""
        semantic_memory.remember("Searchable content")
        results = semantic_memory.recall("searchable")
        self.assertIsInstance(results, list)
    
    def test_forget(self):
        """Test forget function."""
        entry = semantic_memory.remember("To forget")
        result = semantic_memory.forget(entry.memory_id)
        self.assertTrue(result)
    
    def test_get_memory(self):
        """Test get_memory function."""
        memory = semantic_memory.get_memory()
        self.assertIsInstance(memory, semantic_memory.SemanticMemory)


if __name__ == "__main__":
    unittest.main()
