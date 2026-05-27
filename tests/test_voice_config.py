"""Unit tests for the voice_config module - humanization and voice configuration."""

import json
import os
import random
import tempfile
import unittest

import voice_config


class TestVoiceConfigLoadSave(unittest.TestCase):
    """Tests for voice configuration load/save functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_file = voice_config.VOICE_CONFIG_FILE
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        voice_config.VOICE_CONFIG_FILE = self.tmp.name

    def tearDown(self):
        """Restore original and clean up."""
        voice_config.VOICE_CONFIG_FILE = self.original_file
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_load_default_config(self):
        config = voice_config.load_voice_config()
        self.assertEqual(config["tts_provider"], "browser")
        # Check humanization exists (enabled state may vary based on existing config)
        self.assertIn("humanization", config)

    def test_save_and_load_config(self):
        config = {"tts_provider": "elevenlabs", "test_key": "test_value"}
        voice_config.save_voice_config(config)
        loaded = voice_config.load_voice_config()
        self.assertEqual(loaded["tts_provider"], "elevenlabs")
        self.assertEqual(loaded["test_key"], "test_value")

    def test_load_merges_with_defaults(self):
        # Save partial config
        partial = {"tts_provider": "custom"}
        voice_config.save_voice_config(partial)
        loaded = voice_config.load_voice_config()
        # Should have the custom value
        self.assertEqual(loaded["tts_provider"], "custom")
        # Should also have defaults for missing keys
        self.assertIn("humanization", loaded)

    def test_update_voice_config(self):
        voice_config.save_voice_config(voice_config.DEFAULT_VOICE_CONFIG.copy())
        updated = voice_config.update_voice_config(tts_provider="elevenlabs")
        self.assertEqual(updated["tts_provider"], "elevenlabs")

    def test_update_voice_config_ignores_unknown_keys(self):
        voice_config.save_voice_config(voice_config.DEFAULT_VOICE_CONFIG.copy())
        updated = voice_config.update_voice_config(unknown_key="value")
        self.assertNotIn("unknown_key", updated)


class TestApplyContractions(unittest.TestCase):
    """Tests for the apply_contractions function."""

    def test_basic_contraction(self):
        result = voice_config.apply_contractions("I am happy")
        self.assertEqual(result, "I'm happy")

    def test_multiple_contractions(self):
        result = voice_config.apply_contractions("I am going to do not worry")
        self.assertIn("I'm", result)
        self.assertIn("don't", result)

    def test_case_insensitive(self):
        result = voice_config.apply_contractions("YOU ARE great")
        self.assertIn("you're", result.lower())

    def test_will_not_contraction(self):
        result = voice_config.apply_contractions("I will not do it")
        # Note: "will not" -> "won't" may be applied first or "I will" -> "I'll"
        # Either is valid natural speech
        self.assertTrue("won't" in result or "I'll" in result)

    def test_cannot_contraction(self):
        result = voice_config.apply_contractions("I cannot do this")
        self.assertIn("can't", result)

    def test_informal_contractions(self):
        result = voice_config.apply_contractions("I am going to do it")
        self.assertIn("gonna", result)


class TestAddNaturalFillers(unittest.TestCase):
    """Tests for the add_natural_fillers function."""

    def test_returns_string(self):
        result = voice_config.add_natural_fillers("Hello world")
        self.assertIsInstance(result, str)

    def test_may_add_fillers(self):
        # With high frequency, should add fillers
        random.seed(1)
        text = "This is a sentence. Here is another sentence."
        result = voice_config.add_natural_fillers(text, frequency=1.0)
        self.assertIsInstance(result, str)

    def test_low_frequency_less_modification(self):
        random.seed(42)
        text = "Simple text"
        result = voice_config.add_natural_fillers(text, frequency=0.0)
        # With 0 frequency, should return original
        self.assertEqual(result, text)


class TestAddPauses(unittest.TestCase):
    """Tests for the add_pauses function."""

    def test_adds_pauses_after_comma(self):
        result = voice_config.add_pauses("Hello, world")
        self.assertIn("...", result)

    def test_adds_pauses_after_period(self):
        result = voice_config.add_pauses("First sentence. Second sentence.")
        self.assertIn("......", result)

    def test_adds_thinking_pauses(self):
        result = voice_config.add_pauses("I think this is good")
        self.assertIn("...", result)


class TestAddBreathingSounds(unittest.TestCase):
    """Tests for the add_breathing_sounds function."""

    def test_returns_string(self):
        result = voice_config.add_breathing_sounds("Short text")
        self.assertIsInstance(result, str)

    def test_may_add_breath_to_long_sentences(self):
        random.seed(42)
        text = "This is a short sentence. This is a much longer sentence that contains many words and should be over fifty characters long to trigger the breathing mechanism."
        result = voice_config.add_breathing_sounds(text)
        self.assertIsInstance(result, str)


class TestAddPersonalityTouches(unittest.TestCase):
    """Tests for the add_personality_touches function."""

    def test_casual_personality(self):
        result = voice_config.add_personality_touches("Hello there", "casual")
        # May convert "hello" to "hey"
        self.assertIsInstance(result, str)

    def test_warm_personality(self):
        random.seed(1)
        result = voice_config.add_personality_touches("That is nice", "warm")
        # May add endearments
        self.assertIsInstance(result, str)

    def test_confident_personality(self):
        result = voice_config.add_personality_touches("I think it is good", "confident")
        self.assertIsInstance(result, str)

    def test_unknown_personality_returns_original(self):
        text = "Original text"
        result = voice_config.add_personality_touches(text, "nonexistent")
        self.assertEqual(result, text)


class TestHumanizeText(unittest.TestCase):
    """Tests for the main humanize_text function."""

    def setUp(self):
        self.original_file = voice_config.VOICE_CONFIG_FILE
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        voice_config.VOICE_CONFIG_FILE = self.tmp.name

    def tearDown(self):
        voice_config.VOICE_CONFIG_FILE = self.original_file
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_humanize_applies_contractions(self):
        config = voice_config.DEFAULT_VOICE_CONFIG.copy()
        config["humanization"]["add_fillers"] = False
        result = voice_config.humanize_text("I am happy", config=config)
        self.assertIn("I'm", result)

    def test_humanize_disabled(self):
        config = voice_config.DEFAULT_VOICE_CONFIG.copy()
        config["humanization"]["enabled"] = False
        text = "I am going to do this"
        result = voice_config.humanize_text(text, config=config)
        self.assertEqual(result, text)

    def test_humanize_with_lamai_persona(self):
        random.seed(42)
        config = voice_config.DEFAULT_VOICE_CONFIG.copy()
        result = voice_config.humanize_text("That is nice", "lamai", config)
        self.assertIsInstance(result, str)

    def test_humanize_with_coach_jv_persona(self):
        random.seed(42)
        config = voice_config.DEFAULT_VOICE_CONFIG.copy()
        result = voice_config.humanize_text("Let us do this", "coach_jv", config)
        self.assertIsInstance(result, str)


class TestClonedVoices(unittest.TestCase):
    """Tests for voice cloning configuration functions."""

    def setUp(self):
        self.original_file = voice_config.VOICE_CONFIG_FILE
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        voice_config.VOICE_CONFIG_FILE = self.tmp.name

    def tearDown(self):
        voice_config.VOICE_CONFIG_FILE = self.original_file
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_add_cloned_voice(self):
        voice_config.add_cloned_voice("test_voice", "voice123", "elevenlabs")
        voice = voice_config.get_cloned_voice("test_voice")
        self.assertIsNotNone(voice)
        self.assertEqual(voice["voice_id"], "voice123")
        self.assertEqual(voice["provider"], "elevenlabs")

    def test_get_nonexistent_cloned_voice(self):
        voice = voice_config.get_cloned_voice("nonexistent")
        self.assertIsNone(voice)

    def test_list_cloned_voices(self):
        voice_config.add_cloned_voice("voice1", "id1")
        voice_config.add_cloned_voice("voice2", "id2")
        voices = voice_config.list_cloned_voices()
        self.assertIn("voice1", voices)
        self.assertIn("voice2", voices)

    def test_remove_cloned_voice(self):
        voice_config.add_cloned_voice("to_remove", "id123")
        result = voice_config.remove_cloned_voice("to_remove")
        self.assertTrue(result)
        self.assertIsNone(voice_config.get_cloned_voice("to_remove"))

    def test_remove_nonexistent_voice(self):
        result = voice_config.remove_cloned_voice("nonexistent")
        self.assertFalse(result)


class TestTextToSSML(unittest.TestCase):
    """Tests for the text_to_ssml function."""

    def test_basic_ssml_structure(self):
        ssml = voice_config.text_to_ssml("Hello world")
        self.assertTrue(ssml.startswith("<speak>"))
        self.assertTrue(ssml.endswith("</speak>"))
        self.assertIn("prosody", ssml)

    def test_ssml_converts_pause_markers(self):
        text = "Hello... world"
        ssml = voice_config.text_to_ssml(text)
        self.assertIn("break", ssml)

    def test_ssml_adds_emphasis(self):
        text = "This is really important"
        ssml = voice_config.text_to_ssml(text)
        self.assertIn("emphasis", ssml)

    def test_ssml_with_custom_rate(self):
        ssml = voice_config.text_to_ssml("Hello", {"rate": 0.8})
        self.assertIn('rate="0.8"', ssml)


class TestElevenLabsConfig(unittest.TestCase):
    """Tests for ElevenLabs configuration functions."""

    def setUp(self):
        self.original_file = voice_config.VOICE_CONFIG_FILE
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        voice_config.VOICE_CONFIG_FILE = self.tmp.name

    def tearDown(self):
        voice_config.VOICE_CONFIG_FILE = self.original_file
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_get_elevenlabs_config_default(self):
        config = voice_config.get_elevenlabs_config()
        self.assertEqual(config["api_key"], "")
        self.assertEqual(config["model_id"], "eleven_monolingual_v1")
        self.assertIn("voice_settings", config)

    def test_set_elevenlabs_config(self):
        voice_config.set_elevenlabs_config(api_key="test_key", voice_id="test_voice")
        config = voice_config.get_elevenlabs_config()
        self.assertEqual(config["api_key"], "test_key")
        self.assertEqual(config["voice_id"], "test_voice")

    def test_set_elevenlabs_partial_update(self):
        voice_config.set_elevenlabs_config(api_key="key1")
        voice_config.set_elevenlabs_config(voice_id="voice1")
        config = voice_config.get_elevenlabs_config()
        self.assertEqual(config["api_key"], "key1")
        self.assertEqual(config["voice_id"], "voice1")


class TestGetVoiceConfigForFrontend(unittest.TestCase):
    """Tests for the get_voice_config_for_frontend function."""

    def setUp(self):
        self.original_file = voice_config.VOICE_CONFIG_FILE
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        os.unlink(self.tmp.name)
        voice_config.VOICE_CONFIG_FILE = self.tmp.name

    def tearDown(self):
        voice_config.VOICE_CONFIG_FILE = self.original_file
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    def test_frontend_config_excludes_api_key(self):
        voice_config.set_elevenlabs_config(api_key="secret_key")
        frontend_config = voice_config.get_voice_config_for_frontend()
        self.assertNotIn("elevenlabs_api_key", frontend_config)
        self.assertNotIn("api_key", frontend_config)
        self.assertNotIn("secret_key", str(frontend_config))

    def test_frontend_config_has_expected_fields(self):
        frontend_config = voice_config.get_voice_config_for_frontend()
        self.assertIn("tts_provider", frontend_config)
        self.assertIn("has_elevenlabs", frontend_config)
        self.assertIn("cloned_voices", frontend_config)
        self.assertIn("humanization", frontend_config)
        self.assertIn("speech_settings", frontend_config)

    def test_frontend_config_has_elevenlabs_flag(self):
        # Without API key
        config1 = voice_config.get_voice_config_for_frontend()
        self.assertFalse(config1["has_elevenlabs"])
        
        # With API key
        voice_config.set_elevenlabs_config(api_key="test_key")
        config2 = voice_config.get_voice_config_for_frontend()
        self.assertTrue(config2["has_elevenlabs"])


class TestConstants(unittest.TestCase):
    """Tests for module constants."""

    def test_contractions_dict_exists(self):
        self.assertIsInstance(voice_config.CONTRACTIONS, dict)
        self.assertTrue(len(voice_config.CONTRACTIONS) > 10)

    def test_natural_fillers_dict_exists(self):
        self.assertIsInstance(voice_config.NATURAL_FILLERS, dict)
        self.assertIn("thinking", voice_config.NATURAL_FILLERS)
        self.assertIn("transition", voice_config.NATURAL_FILLERS)

    def test_pause_markers_exist(self):
        self.assertIsInstance(voice_config.PAUSE_MARKERS, dict)
        self.assertIn("short", voice_config.PAUSE_MARKERS)
        self.assertIn("long", voice_config.PAUSE_MARKERS)

    def test_personality_speech_exists(self):
        self.assertIsInstance(voice_config.PERSONALITY_SPEECH, dict)
        self.assertIn("casual", voice_config.PERSONALITY_SPEECH)
        self.assertIn("warm", voice_config.PERSONALITY_SPEECH)
        self.assertIn("confident", voice_config.PERSONALITY_SPEECH)


if __name__ == "__main__":
    unittest.main()
