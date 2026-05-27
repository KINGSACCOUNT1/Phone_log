"""Emotion Detection - Analyze user sentiment and emotional state.

This module provides:
- Basic sentiment analysis (positive/negative/neutral)
- Emotion classification (happy, sad, angry, frustrated, etc.)
- Empathetic response suggestions
"""

import re
from typing import Tuple, List

# ─── Emotion Categories ────────────────────────────────────────────────────────

EMOTIONS = {
    "happy": {
        "keywords": ["happy", "glad", "great", "awesome", "wonderful", "excited", "love", "amazing", "fantastic", "excellent", "yay", "hurray", "perfect", "thrilled"],
        "patterns": [r"!\s*$", r"(?:so|very|really)\s+(?:happy|glad|excited)", r"can't\s+wait"],
        "emoji_patterns": [r"[😊😄😃🙂😁🎉🎊❤️💕]"],
        "intensity_multipliers": {"very": 1.3, "so": 1.2, "really": 1.2, "extremely": 1.5},
    },
    "sad": {
        "keywords": ["sad", "unhappy", "disappointed", "upset", "down", "depressed", "miss", "lonely", "sorry", "unfortunate", "terrible", "awful"],
        "patterns": [r"(?:feel|feeling)\s+(?:sad|down|low)", r"miss(?:ing)?\s+(?:you|them|her|him)"],
        "emoji_patterns": [r"[😢😭😞😔😿💔]"],
        "intensity_multipliers": {"very": 1.3, "so": 1.2, "really": 1.2, "extremely": 1.5},
    },
    "angry": {
        "keywords": ["angry", "mad", "furious", "annoyed", "irritated", "frustrated", "hate", "stupid", "ridiculous", "unacceptable", "outrageous"],
        "patterns": [r"!{2,}", r"(?:so|very)\s+(?:angry|mad|annoyed)", r"can't\s+believe", r"what\s+the\s+hell"],
        "emoji_patterns": [r"[😠😡🤬😤💢]"],
        "intensity_multipliers": {"very": 1.3, "so": 1.2, "really": 1.2, "extremely": 1.5},
    },
    "frustrated": {
        "keywords": ["frustrated", "stuck", "confused", "lost", "struggling", "difficult", "hard", "problem", "issue", "trouble", "doesn't work", "not working", "broken"],
        "patterns": [r"(?:keep|keeps)\s+(?:happening|failing)", r"(?:can't|cannot)\s+(?:figure|understand)", r"(?:why|how)\s+(?:is|does)\s+this"],
        "emoji_patterns": [r"[😩😫🤦‍♂️🤦‍♀️😖]"],
        "intensity_multipliers": {"very": 1.3, "so": 1.2, "really": 1.2, "extremely": 1.5},
    },
    "anxious": {
        "keywords": ["worried", "anxious", "nervous", "scared", "afraid", "concerned", "uneasy", "stressed", "overwhelmed", "panic"],
        "patterns": [r"(?:what\s+if)", r"(?:worried|scared)\s+(?:about|that)", r"hope\s+(?:it|this|that)\s+(?:works|helps)"],
        "emoji_patterns": [r"[😰😨😱🥺😬]"],
        "intensity_multipliers": {"very": 1.3, "so": 1.2, "really": 1.2, "extremely": 1.5},
    },
    "grateful": {
        "keywords": ["thank", "thanks", "grateful", "appreciate", "thankful", "blessed", "wonderful", "helpful"],
        "patterns": [r"thank\s+you", r"thanks\s+(?:so\s+much|a\s+lot)", r"(?:really|so)\s+appreciate"],
        "emoji_patterns": [r"[🙏💖😇🥰]"],
        "intensity_multipliers": {"very": 1.3, "so": 1.2, "really": 1.2},
    },
    "neutral": {
        "keywords": ["okay", "ok", "fine", "alright", "sure", "yes", "no", "maybe"],
        "patterns": [r"^(?:ok|okay|sure|fine)$"],
        "emoji_patterns": [],
        "intensity_multipliers": {},
    },
}

# Sentiment keywords for quick classification
POSITIVE_WORDS = {"good", "great", "nice", "awesome", "wonderful", "excellent", "love", "happy", "glad", "thanks", "thank", "please", "helpful", "perfect", "amazing"}
NEGATIVE_WORDS = {"bad", "terrible", "awful", "hate", "angry", "sad", "frustrated", "annoyed", "disappointed", "problem", "issue", "wrong", "broken", "stuck", "difficult"}


# ─── Emotion Detection ─────────────────────────────────────────────────────────

def detect_emotion(text: str) -> Tuple[str, float, dict]:
    """
    Detect the primary emotion in the given text.
    
    Returns:
        Tuple of (emotion_name, confidence, details)
        - emotion_name: The detected emotion (e.g., "happy", "sad", "angry")
        - confidence: Confidence score (0.0 to 1.0)
        - details: Dictionary with additional analysis details
    """
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))
    
    emotion_scores = {}
    
    for emotion, config in EMOTIONS.items():
        score = 0.0
        matches = []
        
        # Check keywords
        keyword_matches = words & set(config["keywords"])
        if keyword_matches:
            score += len(keyword_matches) * 0.3
            matches.extend(list(keyword_matches))
        
        # Check patterns
        for pattern in config["patterns"]:
            if re.search(pattern, text_lower):
                score += 0.25
                matches.append(f"pattern:{pattern}")
        
        # Check emoji patterns
        for emoji_pattern in config.get("emoji_patterns", []):
            if re.search(emoji_pattern, text):
                score += 0.2
                matches.append("emoji_match")
        
        # Apply intensity multipliers
        for word, multiplier in config.get("intensity_multipliers", {}).items():
            if word in words:
                score *= multiplier
        
        emotion_scores[emotion] = {"score": min(score, 1.0), "matches": matches}
    
    # Find the highest scoring emotion
    if not emotion_scores:
        return ("neutral", 0.5, {"raw_scores": {}})
    
    best_emotion = max(emotion_scores.keys(), key=lambda e: emotion_scores[e]["score"])
    best_score = emotion_scores[best_emotion]["score"]
    
    # If no clear emotion detected, return neutral
    if best_score < 0.2:
        return ("neutral", 0.5, {"raw_scores": emotion_scores})
    
    return (
        best_emotion,
        min(best_score, 1.0),
        {
            "raw_scores": emotion_scores,
            "matches": emotion_scores[best_emotion]["matches"],
        }
    )


def get_sentiment(text: str) -> Tuple[str, float]:
    """
    Get basic sentiment classification (positive/negative/neutral).
    
    Returns:
        Tuple of (sentiment, confidence)
        - sentiment: "positive", "negative", or "neutral"
        - confidence: Confidence score (0.0 to 1.0)
    """
    text_lower = text.lower()
    words = set(re.findall(r'\b\w+\b', text_lower))
    
    positive_count = len(words & POSITIVE_WORDS)
    negative_count = len(words & NEGATIVE_WORDS)
    
    # Check for exclamation marks (can indicate strong sentiment)
    exclamation_count = text.count("!")
    
    # Check for question marks (often neutral)
    question_count = text.count("?")
    
    # Calculate base sentiment
    if positive_count > negative_count:
        sentiment = "positive"
        confidence = min(0.5 + (positive_count - negative_count) * 0.15, 1.0)
    elif negative_count > positive_count:
        sentiment = "negative"
        confidence = min(0.5 + (negative_count - positive_count) * 0.15, 1.0)
    else:
        sentiment = "neutral"
        confidence = 0.6
    
    # Adjust for punctuation
    if exclamation_count > 0 and sentiment != "neutral":
        confidence = min(confidence + 0.1, 1.0)
    
    if question_count > 0:
        confidence = max(confidence - 0.1, 0.3)
    
    return (sentiment, confidence)


# ─── Empathetic Response Suggestions ───────────────────────────────────────────

EMPATHETIC_RESPONSES = {
    "happy": [
        "That's wonderful to hear!",
        "I'm so glad!",
        "That's great news!",
        "How exciting!",
    ],
    "sad": [
        "I'm sorry to hear that.",
        "That sounds difficult.",
        "I understand how you feel.",
        "I'm here if you need anything.",
    ],
    "angry": [
        "I understand your frustration.",
        "That does sound frustrating.",
        "I can see why that would be upsetting.",
        "Let me see how I can help with that.",
    ],
    "frustrated": [
        "I understand that can be frustrating.",
        "Let me help you with that.",
        "I'm here to help sort this out.",
        "Let's work through this together.",
    ],
    "anxious": [
        "I understand your concern.",
        "Don't worry, we'll figure this out.",
        "It's going to be okay.",
        "Let me help put your mind at ease.",
    ],
    "grateful": [
        "You're welcome!",
        "Happy to help!",
        "My pleasure!",
        "Anytime!",
    ],
    "neutral": [
        "I understand.",
        "Got it.",
        "Okay, let me help with that.",
        "Sure thing.",
    ],
}


def get_empathetic_prefix(emotion: str) -> str:
    """Get an empathetic response prefix based on detected emotion."""
    import random
    responses = EMPATHETIC_RESPONSES.get(emotion, EMPATHETIC_RESPONSES["neutral"])
    return random.choice(responses)


def adjust_response_tone(response: str, emotion: str, sentiment: str) -> str:
    """
    Adjust response tone based on user's emotional state.
    
    Args:
        response: The original response text
        emotion: Detected emotion
        sentiment: Detected sentiment (positive/negative/neutral)
    
    Returns:
        Adjusted response with appropriate tone
    """
    # For negative emotions, add empathetic prefix
    if emotion in ["sad", "angry", "frustrated", "anxious"]:
        prefix = get_empathetic_prefix(emotion)
        # Don't add prefix if response already starts with empathetic phrase
        empathetic_starts = ["i'm sorry", "i understand", "that sounds", "don't worry", "let me help"]
        if not any(response.lower().startswith(start) for start in empathetic_starts):
            response = f"{prefix} {response}"
    
    # For positive emotions, maintain enthusiasm
    elif emotion in ["happy", "grateful"]:
        # Add enthusiasm markers if not already present
        if not response.endswith("!") and not response.endswith("?"):
            response = response.rstrip(".") + "!"
    
    return response


# ─── Emotion-Aware Context ─────────────────────────────────────────────────────

class EmotionalContext:
    """Track emotional context across a conversation."""
    
    def __init__(self, history_size: int = 5):
        self.history: List[dict] = []
        self.history_size = history_size
    
    def add_emotion(self, text: str):
        """Analyze and add emotion to history."""
        emotion, confidence, details = detect_emotion(text)
        sentiment, sent_confidence = get_sentiment(text)
        
        entry = {
            "text": text[:100],  # Store truncated text
            "emotion": emotion,
            "emotion_confidence": confidence,
            "sentiment": sentiment,
            "sentiment_confidence": sent_confidence,
        }
        
        self.history.append(entry)
        
        # Keep only recent history
        if len(self.history) > self.history_size:
            self.history = self.history[-self.history_size:]
        
        return entry
    
    def get_emotional_trend(self) -> str:
        """Get the overall emotional trend in the conversation."""
        if not self.history:
            return "neutral"
        
        # Count emotions
        emotion_counts = {}
        for entry in self.history:
            emotion = entry["emotion"]
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Return most common emotion
        return max(emotion_counts.keys(), key=lambda e: emotion_counts[e])
    
    def get_sentiment_trend(self) -> str:
        """Get the overall sentiment trend."""
        if not self.history:
            return "neutral"
        
        positive_count = sum(1 for e in self.history if e["sentiment"] == "positive")
        negative_count = sum(1 for e in self.history if e["sentiment"] == "negative")
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        return "neutral"
    
    def is_escalating_negative(self) -> bool:
        """Check if negative emotions are escalating."""
        if len(self.history) < 2:
            return False
        
        recent = self.history[-2:]
        negative_emotions = {"sad", "angry", "frustrated", "anxious"}
        
        return all(e["emotion"] in negative_emotions for e in recent)
    
    def clear(self):
        """Clear emotional history."""
        self.history = []


# ─── Global Instance ───────────────────────────────────────────────────────────

emotional_context = EmotionalContext()


def analyze_emotion(text: str) -> dict:
    """
    Analyze emotion in text and update context.
    
    Returns:
        Dictionary with emotion analysis results
    """
    emotion, confidence, details = detect_emotion(text)
    sentiment, sent_confidence = get_sentiment(text)
    
    # Update context
    emotional_context.add_emotion(text)
    
    return {
        "emotion": emotion,
        "emotion_confidence": confidence,
        "sentiment": sentiment,
        "sentiment_confidence": sent_confidence,
        "emotional_trend": emotional_context.get_emotional_trend(),
        "is_escalating": emotional_context.is_escalating_negative(),
        "empathetic_response": get_empathetic_prefix(emotion),
    }


def get_emotional_context() -> EmotionalContext:
    """Get the global emotional context instance."""
    return emotional_context
