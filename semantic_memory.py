"""Semantic Memory - Long-term context and knowledge storage for the assistant.

This module provides:
- Persistent memory of important facts about users and conversations
- Topic-based memory retrieval for context-aware responses
- Memory consolidation and relevance scoring
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import List, Optional

# ─── Configuration ─────────────────────────────────────────────────────────────

_DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
MEMORY_FILE = os.path.join(_DATA_DIR, "semantic_memory.json")

DEFAULT_MEMORY_CONFIG = {
    "enabled": True,
    "max_memories": 1000,
    "relevance_threshold": 0.3,
    "auto_extract": True,  # Automatically extract facts from conversations
}


# ─── Memory Entry Structure ────────────────────────────────────────────────────

class MemoryEntry:
    """Represents a single memory entry."""
    
    def __init__(
        self,
        content: str,
        memory_type: str = "fact",
        tags: List[str] = None,
        importance: float = 0.5,
        source: str = "conversation",
        created_at: str = None,
        last_accessed: str = None,
        access_count: int = 0,
        memory_id: str = None,
    ):
        self.content = content  # Set content first for _generate_id
        self.memory_id = memory_id or self._generate_id()
        self.memory_type = memory_type  # fact, preference, event, contact, topic
        self.tags = tags or []
        self.importance = importance  # 0.0 to 1.0
        self.source = source
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.last_accessed = last_accessed or self.created_at
        self.access_count = access_count
    
    def _generate_id(self) -> str:
        """Generate a unique ID for the memory."""
        import hashlib
        timestamp = datetime.now(timezone.utc).isoformat()
        content_hash = hashlib.md5(f"{self.content}{timestamp}".encode()).hexdigest()[:8]
        return f"mem_{content_hash}"
    
    def to_dict(self) -> dict:
        """Convert memory entry to dictionary."""
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "tags": self.tags,
            "importance": self.importance,
            "source": self.source,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """Create memory entry from dictionary."""
        return cls(
            memory_id=data.get("memory_id"),
            content=data["content"],
            memory_type=data.get("memory_type", "fact"),
            tags=data.get("tags", []),
            importance=data.get("importance", 0.5),
            source=data.get("source", "conversation"),
            created_at=data.get("created_at"),
            last_accessed=data.get("last_accessed"),
            access_count=data.get("access_count", 0),
        )
    
    def update_access(self):
        """Update access timestamp and count."""
        self.last_accessed = datetime.now(timezone.utc).isoformat()
        self.access_count += 1


# ─── Memory Store ──────────────────────────────────────────────────────────────

class SemanticMemory:
    """Manages semantic memory storage and retrieval."""
    
    def __init__(self):
        self.memories: List[MemoryEntry] = []
        self.config = DEFAULT_MEMORY_CONFIG.copy()
        self._load()
    
    def _load(self):
        """Load memories from file."""
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config.update(data.get("config", {}))
                    self.memories = [
                        MemoryEntry.from_dict(m) 
                        for m in data.get("memories", [])
                    ]
            except (json.JSONDecodeError, KeyError):
                self.memories = []
    
    def _save(self):
        """Save memories to file."""
        data = {
            "config": self.config,
            "memories": [m.to_dict() for m in self.memories],
        }
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def add(
        self,
        content: str,
        memory_type: str = "fact",
        tags: List[str] = None,
        importance: float = 0.5,
        source: str = "conversation",
    ) -> MemoryEntry:
        """Add a new memory entry."""
        # Check for duplicates
        for existing in self.memories:
            if self._similarity(existing.content, content) > 0.9:
                # Update existing memory instead of adding duplicate
                existing.importance = max(existing.importance, importance)
                existing.update_access()
                self._save()
                return existing
        
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            importance=importance,
            source=source,
        )
        
        self.memories.append(entry)
        
        # Enforce memory limit
        if len(self.memories) > self.config.get("max_memories", 1000):
            self._consolidate()
        
        self._save()
        return entry
    
    def search(
        self,
        query: str,
        memory_type: str = None,
        tags: List[str] = None,
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """Search memories by relevance to query."""
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for memory in self.memories:
            # Filter by type if specified
            if memory_type and memory.memory_type != memory_type:
                continue
            
            # Filter by tags if specified
            if tags and not any(t in memory.tags for t in tags):
                continue
            
            # Calculate relevance score
            score = self._calculate_relevance(memory, query_lower, query_words)
            
            if score >= self.config.get("relevance_threshold", 0.3):
                results.append((score, memory))
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Update access for returned memories
        top_results = []
        for score, memory in results[:limit]:
            memory.update_access()
            top_results.append(memory)
        
        if top_results:
            self._save()
        
        return top_results
    
    def get_context_summary(self, topics: List[str] = None, limit: int = 5) -> str:
        """Get a summary of relevant memories for context."""
        if not topics:
            # Return recent important memories
            sorted_memories = sorted(
                self.memories,
                key=lambda m: (m.importance, m.access_count),
                reverse=True,
            )
            relevant = sorted_memories[:limit]
        else:
            # Search for topic-related memories
            relevant = []
            for topic in topics:
                relevant.extend(self.search(topic, limit=limit // len(topics) or 1))
        
        if not relevant:
            return ""
        
        summary_parts = []
        for memory in relevant:
            summary_parts.append(f"- {memory.content}")
        
        return "Relevant memories:\n" + "\n".join(summary_parts)
    
    def get_by_type(self, memory_type: str, limit: int = 20) -> List[MemoryEntry]:
        """Get memories of a specific type."""
        filtered = [m for m in self.memories if m.memory_type == memory_type]
        return sorted(filtered, key=lambda m: m.importance, reverse=True)[:limit]
    
    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        for i, memory in enumerate(self.memories):
            if memory.memory_id == memory_id:
                self.memories.pop(i)
                self._save()
                return True
        return False
    
    def clear(self):
        """Clear all memories."""
        self.memories = []
        self._save()
    
    def _calculate_relevance(
        self,
        memory: MemoryEntry,
        query_lower: str,
        query_words: set,
    ) -> float:
        """Calculate relevance score between memory and query."""
        content_lower = memory.content.lower()
        content_words = set(content_lower.split())
        
        # Exact substring match
        if query_lower in content_lower:
            exact_score = 0.8
        else:
            exact_score = 0.0
        
        # Word overlap score
        common_words = query_words & content_words
        if query_words:
            word_score = len(common_words) / len(query_words)
        else:
            word_score = 0.0
        
        # Tag match bonus
        tag_score = 0.0
        for word in query_words:
            if word in memory.tags:
                tag_score += 0.2
        tag_score = min(tag_score, 0.4)
        
        # Importance factor
        importance_factor = memory.importance * 0.2
        
        # Combine scores
        total_score = max(exact_score, word_score) + tag_score + importance_factor
        
        return min(total_score, 1.0)
    
    def _similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _consolidate(self):
        """Consolidate memories to stay within limit."""
        # Remove low-importance, rarely accessed memories
        self.memories.sort(
            key=lambda m: (m.importance, m.access_count, m.created_at),
            reverse=True,
        )
        max_memories = self.config.get("max_memories", 1000)
        self.memories = self.memories[:max_memories]


# ─── Fact Extraction ───────────────────────────────────────────────────────────

# Patterns for extracting facts from conversations
FACT_PATTERNS = [
    # Contact preferences
    (r"(?:my |the )?(?:friend|colleague|boss|partner|wife|husband|mother|father|sister|brother)\s+(?:is\s+)?(?:named\s+)?([A-Z][a-z]+)", "contact", ["personal", "contact"]),
    (r"([A-Z][a-z]+)\s+is\s+my\s+(friend|colleague|boss|partner|wife|husband|mother|father|sister|brother)", "contact", ["personal", "contact"]),
    
    # Preferences
    (r"(?:I\s+)?prefer\s+(?:to\s+)?(.+)", "preference", ["user_preference"]),
    (r"(?:I\s+)?(?:like|love|enjoy)\s+(.+)", "preference", ["user_preference"]),
    (r"(?:I\s+)?(?:don't like|hate|dislike)\s+(.+)", "preference", ["user_preference", "negative"]),
    
    # Schedules/routines
    (r"(?:I\s+)?usually\s+(.+)", "routine", ["schedule", "routine"]),
    (r"(?:I\s+)?always\s+(.+)", "routine", ["schedule", "routine"]),
    (r"(?:I\s+)?(?:call|talk to)\s+(.+?)\s+(?:every|on)\s+(.+)", "routine", ["schedule", "call_pattern"]),
    
    # Important facts
    (r"(?:remember\s+that\s+)?(.+?)\s+is\s+important", "fact", ["important"]),
    (r"(?:don't\s+forget\s+that\s+)?(.+)", "fact", ["reminder"]),
]


def extract_facts_from_text(text: str) -> List[dict]:
    """Extract potential facts from conversation text."""
    facts = []
    
    for pattern, memory_type, tags in FACT_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            content = match.group(0).strip()
            if len(content) > 10:  # Ignore very short matches
                facts.append({
                    "content": content,
                    "memory_type": memory_type,
                    "tags": tags,
                    "importance": 0.6 if "important" in tags else 0.4,
                })
    
    return facts


def auto_memorize(memory: SemanticMemory, user_input: str, assistant_response: str):
    """Automatically extract and store relevant facts from a conversation exchange."""
    # Extract facts from user input
    user_facts = extract_facts_from_text(user_input)
    for fact in user_facts:
        memory.add(
            content=fact["content"],
            memory_type=fact["memory_type"],
            tags=fact["tags"],
            importance=fact["importance"],
            source="user_input",
        )
    
    return len(user_facts)


# ─── Global Instance ───────────────────────────────────────────────────────────

# Global semantic memory instance
semantic_memory = SemanticMemory()


def get_memory() -> SemanticMemory:
    """Get the global semantic memory instance."""
    return semantic_memory


def remember(content: str, memory_type: str = "fact", tags: List[str] = None, importance: float = 0.5) -> MemoryEntry:
    """Convenience function to add a memory."""
    return semantic_memory.add(content, memory_type, tags, importance)


def recall(query: str, limit: int = 5) -> List[MemoryEntry]:
    """Convenience function to search memories."""
    return semantic_memory.search(query, limit=limit)


def forget(memory_id: str) -> bool:
    """Convenience function to delete a memory."""
    return semantic_memory.delete(memory_id)


def get_relevant_context(topics: List[str] = None) -> str:
    """Get relevant context for the current conversation."""
    return semantic_memory.get_context_summary(topics)
