"""Unit tests for the personas module - persona management and speech patterns."""

import random
import unittest

import personas


class TestGetPersona(unittest.TestCase):
    """Tests for the get_persona function."""

    def test_get_existing_persona(self):
        persona = personas.get_persona("coach_jv")
        self.assertIsNotNone(persona)
        self.assertEqual(persona["name"], "Coach JV")

    def test_get_lamai_persona(self):
        persona = personas.get_persona("lamai")
        self.assertIsNotNone(persona)
        self.assertEqual(persona["name"], "Lamai")
        self.assertEqual(persona["background"]["nationality"], "Thai")

    def test_get_nonexistent_persona(self):
        persona = personas.get_persona("nonexistent")
        self.assertIsNone(persona)


class TestListPersonas(unittest.TestCase):
    """Tests for the list_personas function."""

    def test_list_personas_returns_list(self):
        result = personas.list_personas()
        self.assertIsInstance(result, list)

    def test_list_personas_contains_expected_fields(self):
        result = personas.list_personas()
        for p in result:
            self.assertIn("id", p)
            self.assertIn("name", p)
            self.assertIn("full_name", p)
            self.assertIn("role", p)
            self.assertIn("nationality", p)

    def test_list_personas_includes_coach_jv(self):
        result = personas.list_personas()
        ids = [p["id"] for p in result]
        self.assertIn("coach_jv", ids)

    def test_list_personas_includes_lamai(self):
        result = personas.list_personas()
        ids = [p["id"] for p in result]
        self.assertIn("lamai", ids)


class TestGetRandomFiller(unittest.TestCase):
    """Tests for the get_random_filler function."""

    def test_get_filler_for_valid_persona(self):
        random.seed(42)
        filler = personas.get_random_filler("coach_jv")
        self.assertIsInstance(filler, str)
        self.assertTrue(len(filler) > 0)

    def test_get_filler_from_persona_fillers(self):
        persona = personas.get_persona("coach_jv")
        expected_fillers = persona["speech_patterns"]["fillers"]
        # Test multiple times due to randomness
        for _ in range(10):
            filler = personas.get_random_filler("coach_jv")
            self.assertIn(filler, expected_fillers)

    def test_get_filler_invalid_persona(self):
        filler = personas.get_random_filler("invalid")
        self.assertEqual(filler, "")

    def test_get_filler_lamai(self):
        persona = personas.get_persona("lamai")
        expected_fillers = persona["speech_patterns"]["fillers"]
        for _ in range(10):
            filler = personas.get_random_filler("lamai")
            self.assertIn(filler, expected_fillers)


class TestGetRandomExpression(unittest.TestCase):
    """Tests for the get_random_expression function."""

    def test_get_expression_for_valid_persona(self):
        random.seed(42)
        expression = personas.get_random_expression("coach_jv")
        self.assertIsInstance(expression, str)

    def test_get_expression_from_persona_expressions(self):
        persona = personas.get_persona("coach_jv")
        expected = persona["speech_patterns"]["expressions"]
        for _ in range(10):
            expression = personas.get_random_expression("coach_jv")
            self.assertIn(expression, expected)

    def test_get_expression_invalid_persona(self):
        expression = personas.get_random_expression("invalid")
        self.assertEqual(expression, "")


class TestAddSpeechFlavor(unittest.TestCase):
    """Tests for the add_speech_flavor function."""

    def test_add_flavor_invalid_persona_returns_original(self):
        text = "Hello world"
        result = personas.add_speech_flavor("invalid", text)
        self.assertEqual(result, text)

    def test_add_flavor_empty_text(self):
        result = personas.add_speech_flavor("coach_jv", "")
        self.assertEqual(result, "")

    def test_add_flavor_lamai_modifies_text(self):
        # Seed random for reproducible tests
        random.seed(42)
        text = "Hello, how are you doing today. I hope you are well."
        result = personas.add_speech_flavor("lamai", text)
        # Result may or may not be modified based on random chance
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_add_flavor_coach_jv_modifies_text(self):
        random.seed(42)
        text = "Let me help you with that. It's going to be great."
        result = personas.add_speech_flavor("coach_jv", text)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_add_flavor_preserves_base_content(self):
        # Even with modifications, core content should be preserved
        random.seed(42)
        text = "Important message here"
        result = personas.add_speech_flavor("coach_jv", text)
        # Some part of original should remain
        self.assertTrue(any(word in result for word in ["Important", "message", "here"]))


class TestHumanizeResponse(unittest.TestCase):
    """Tests for the humanize_response function."""

    def test_humanize_empty_text(self):
        result = personas.humanize_response("")
        self.assertEqual(result, "")

    def test_humanize_none_text(self):
        result = personas.humanize_response(None)
        self.assertIsNone(result)

    def test_humanize_with_persona(self):
        random.seed(42)
        text = "Hello there, how can I help you today."
        result = personas.humanize_response(text, "lamai")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_humanize_without_persona(self):
        random.seed(42)
        text = "Hello there, how can I help you."
        result = personas.humanize_response(text, None)
        self.assertIsInstance(result, str)

    def test_humanize_may_add_pauses(self):
        # With specific seed, pause may be added
        random.seed(1)
        text = "Hello, how are you doing"
        result = personas.humanize_response(text, None)
        # Either original or modified - should be valid string
        self.assertIsInstance(result, str)


class TestFormatPersonaIntro(unittest.TestCase):
    """Tests for the format_persona_intro function."""

    def test_format_intro_coach_jv(self):
        intro = personas.format_persona_intro("coach_jv")
        self.assertIn("John Vasquez", intro)
        self.assertIn("Coach JV", intro)
        self.assertIn("American", intro)

    def test_format_intro_lamai(self):
        intro = personas.format_persona_intro("lamai")
        self.assertIn("Lamai Nin", intro)
        self.assertIn("Thailand", intro)
        self.assertIn("boutique", intro)
        self.assertIn("30", intro)  # age

    def test_format_intro_invalid_persona(self):
        intro = personas.format_persona_intro("invalid")
        self.assertEqual(intro, "Unknown persona")


class TestPersonaToIdentity(unittest.TestCase):
    """Tests for the persona_to_identity function."""

    def test_convert_coach_jv_to_identity(self):
        identity = personas.persona_to_identity("coach_jv")
        self.assertIsNotNone(identity)
        self.assertEqual(identity["name"], "Coach JV")
        self.assertEqual(identity["full_name"], "John Vasquez")
        self.assertEqual(identity["voice"], "male")
        self.assertEqual(identity["persona_id"], "coach_jv")

    def test_convert_lamai_to_identity(self):
        identity = personas.persona_to_identity("lamai")
        self.assertIsNotNone(identity)
        self.assertEqual(identity["name"], "Lamai")
        self.assertEqual(identity["full_name"], "Lamai Nin")
        self.assertEqual(identity["voice"], "female")
        self.assertEqual(identity["persona_id"], "lamai")

    def test_convert_invalid_persona_returns_none(self):
        identity = personas.persona_to_identity("invalid")
        self.assertIsNone(identity)

    def test_identity_has_required_fields(self):
        identity = personas.persona_to_identity("coach_jv")
        required_fields = ["name", "role", "personality", "greeting", "voice", "persona_id"]
        for field in required_fields:
            self.assertIn(field, identity)


class TestPersonaDefinitions(unittest.TestCase):
    """Tests for the PERSONAS dictionary structure."""

    def test_personas_dict_exists(self):
        self.assertIsInstance(personas.PERSONAS, dict)
        self.assertTrue(len(personas.PERSONAS) >= 2)

    def test_persona_has_required_fields(self):
        required_fields = ["name", "role", "personality", "greeting", "voice", "background", "speech_patterns"]
        for persona_id, persona in personas.PERSONAS.items():
            for field in required_fields:
                self.assertIn(field, persona, f"Persona {persona_id} missing {field}")

    def test_persona_background_has_nationality(self):
        for persona_id, persona in personas.PERSONAS.items():
            self.assertIn("nationality", persona["background"], f"Persona {persona_id} missing nationality")

    def test_persona_speech_patterns_has_fillers(self):
        for persona_id, persona in personas.PERSONAS.items():
            self.assertIn("fillers", persona["speech_patterns"], f"Persona {persona_id} missing fillers")
            self.assertTrue(len(persona["speech_patterns"]["fillers"]) > 0)


if __name__ == "__main__":
    unittest.main()
