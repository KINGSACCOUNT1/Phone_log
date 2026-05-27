"""Tests for Emotion Detection module."""

import unittest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import emotion_detection


class TestDetectEmotion(unittest.TestCase):
    """Test emotion detection function."""
    
    def test_detect_happy(self):
        """Test detecting happy emotion."""
        emotion, confidence, _ = emotion_detection.detect_emotion("I'm so happy today!")
        self.assertEqual(emotion, "happy")
        self.assertGreater(confidence, 0.3)
    
    def test_detect_sad(self):
        """Test detecting sad emotion."""
        emotion, confidence, _ = emotion_detection.detect_emotion("I feel so sad and disappointed")
        self.assertEqual(emotion, "sad")
        self.assertGreater(confidence, 0.3)
    
    def test_detect_angry(self):
        """Test detecting angry emotion."""
        emotion, confidence, _ = emotion_detection.detect_emotion("I'm really angry about this!! It's ridiculous!")
        self.assertEqual(emotion, "angry")
        self.assertGreater(confidence, 0.3)
    
    def test_detect_frustrated(self):
        """Test detecting frustrated emotion."""
        emotion, confidence, _ = emotion_detection.detect_emotion("This doesn't work! I keep getting the same problem.")
        self.assertEqual(emotion, "frustrated")
        self.assertGreaterEqual(confidence, 0.3)
    
    def test_detect_grateful(self):
        """Test detecting grateful emotion."""
        emotion, confidence, _ = emotion_detection.detect_emotion("Thank you so much! I really appreciate your help!")
        self.assertEqual(emotion, "grateful")
        self.assertGreater(confidence, 0.3)
    
    def test_detect_neutral(self):
        """Test detecting neutral emotion."""
        emotion, confidence, _ = emotion_detection.detect_emotion("ok")
        self.assertEqual(emotion, "neutral")
    
    def test_returns_details(self):
        """Test that details are returned."""
        _, _, details = emotion_detection.detect_emotion("I'm excited!")
        self.assertIn("raw_scores", details)


class TestGetSentiment(unittest.TestCase):
    """Test sentiment analysis function."""
    
    def test_positive_sentiment(self):
        """Test detecting positive sentiment."""
        sentiment, confidence = emotion_detection.get_sentiment("This is great! I love it!")
        self.assertEqual(sentiment, "positive")
        self.assertGreater(confidence, 0.5)
    
    def test_negative_sentiment(self):
        """Test detecting negative sentiment."""
        sentiment, confidence = emotion_detection.get_sentiment("This is terrible and broken")
        self.assertEqual(sentiment, "negative")
        self.assertGreater(confidence, 0.5)
    
    def test_neutral_sentiment(self):
        """Test detecting neutral sentiment."""
        sentiment, confidence = emotion_detection.get_sentiment("The sky is blue")
        self.assertEqual(sentiment, "neutral")


class TestEmpatheticResponses(unittest.TestCase):
    """Test empathetic response generation."""
    
    def test_get_prefix_happy(self):
        """Test getting prefix for happy emotion."""
        prefix = emotion_detection.get_empathetic_prefix("happy")
        self.assertIn(prefix, emotion_detection.EMPATHETIC_RESPONSES["happy"])
    
    def test_get_prefix_sad(self):
        """Test getting prefix for sad emotion."""
        prefix = emotion_detection.get_empathetic_prefix("sad")
        self.assertIn(prefix, emotion_detection.EMPATHETIC_RESPONSES["sad"])
    
    def test_get_prefix_unknown(self):
        """Test getting prefix for unknown emotion."""
        prefix = emotion_detection.get_empathetic_prefix("unknown_emotion")
        self.assertIn(prefix, emotion_detection.EMPATHETIC_RESPONSES["neutral"])
    
    def test_adjust_response_tone_negative(self):
        """Test adjusting response for negative emotion."""
        original = "Here's the information."
        adjusted = emotion_detection.adjust_response_tone(original, "sad", "negative")
        # Should add empathetic prefix
        self.assertGreater(len(adjusted), len(original))
    
    def test_adjust_response_tone_positive(self):
        """Test adjusting response for positive emotion."""
        original = "Done"
        adjusted = emotion_detection.adjust_response_tone(original, "happy", "positive")
        # Should end with exclamation
        self.assertTrue(adjusted.endswith("!"))


class TestEmotionalContext(unittest.TestCase):
    """Test EmotionalContext class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ctx = emotion_detection.EmotionalContext()
    
    def test_add_emotion(self):
        """Test adding emotion to context."""
        entry = self.ctx.add_emotion("I'm feeling happy today!")
        
        self.assertEqual(entry["emotion"], "happy")
        self.assertEqual(len(self.ctx.history), 1)
    
    def test_emotional_trend(self):
        """Test getting emotional trend."""
        self.ctx.add_emotion("I'm happy!")
        self.ctx.add_emotion("This is great!")
        self.ctx.add_emotion("I'm sad now")
        
        trend = self.ctx.get_emotional_trend()
        self.assertIn(trend, ["happy", "sad", "neutral", "grateful"])
    
    def test_sentiment_trend(self):
        """Test getting sentiment trend."""
        self.ctx.add_emotion("Good news!")
        self.ctx.add_emotion("Great job!")
        
        trend = self.ctx.get_sentiment_trend()
        self.assertEqual(trend, "positive")
    
    def test_is_escalating_negative(self):
        """Test detecting escalating negative emotions."""
        self.ctx.add_emotion("I'm frustrated")
        self.ctx.add_emotion("This is making me angry!!")
        
        self.assertTrue(self.ctx.is_escalating_negative())
    
    def test_not_escalating(self):
        """Test when not escalating."""
        self.ctx.add_emotion("Hello")
        
        self.assertFalse(self.ctx.is_escalating_negative())
    
    def test_clear_history(self):
        """Test clearing emotional history."""
        self.ctx.add_emotion("Test")
        self.ctx.clear()
        
        self.assertEqual(len(self.ctx.history), 0)
    
    def test_history_limit(self):
        """Test that history is limited."""
        ctx = emotion_detection.EmotionalContext(history_size=3)
        
        for i in range(5):
            ctx.add_emotion(f"Message {i}")
        
        self.assertEqual(len(ctx.history), 3)


class TestAnalyzeEmotion(unittest.TestCase):
    """Test analyze_emotion convenience function."""
    
    def setUp(self):
        """Reset global emotional context."""
        emotion_detection.emotional_context = emotion_detection.EmotionalContext()
    
    def test_analyze_returns_dict(self):
        """Test that analyze_emotion returns a dictionary."""
        result = emotion_detection.analyze_emotion("Hello!")
        
        self.assertIsInstance(result, dict)
        self.assertIn("emotion", result)
        self.assertIn("sentiment", result)
        self.assertIn("emotional_trend", result)
        self.assertIn("empathetic_response", result)
    
    def test_analyze_updates_context(self):
        """Test that analyze_emotion updates global context."""
        emotion_detection.analyze_emotion("Test message")
        ctx = emotion_detection.get_emotional_context()
        
        self.assertEqual(len(ctx.history), 1)


if __name__ == "__main__":
    unittest.main()
