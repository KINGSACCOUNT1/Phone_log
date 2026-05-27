"""Voice Configuration - Make AI speech sound natural and human-like.

This module provides tools to make synthesized speech sound more natural,
including voice cloning support, speech patterns, and humanization features.
"""

import json
import os
import random
import re

# ─── Configuration File ────────────────────────────────────────────────────────

_DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
VOICE_CONFIG_FILE = os.path.join(_DATA_DIR, "voice_config.json")

DEFAULT_VOICE_CONFIG = {
    "tts_provider": "browser",  # Options: "browser", "elevenlabs", "custom"
    "elevenlabs_api_key": "",
    "elevenlabs_voice_id": "",
    "custom_voice_url": "",
    "cloned_voices": {},  # Store cloned voice IDs
    "humanization": {
        "enabled": True,
        "add_fillers": True,
        "add_pauses": True,
        "add_breathing": True,
        "use_contractions": True,
        "variation_level": 0.7,  # 0-1, higher = more variation
    },
    "speech_settings": {
        "rate": 0.95,       # Slightly slower than normal
        "pitch": 1.0,
        "volume": 1.0,
        "pause_duration_ms": 300,  # Pause duration in milliseconds
    },
}


def load_voice_config():
    """Load voice configuration from file."""
    if os.path.exists(VOICE_CONFIG_FILE):
        with open(VOICE_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Merge with defaults for any missing keys
            merged = DEFAULT_VOICE_CONFIG.copy()
            merged.update(config)
            return merged
    return DEFAULT_VOICE_CONFIG.copy()


def save_voice_config(config):
    """Save voice configuration to file."""
    with open(VOICE_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def update_voice_config(**kwargs):
    """Update voice configuration with provided values."""
    config = load_voice_config()
    for key, value in kwargs.items():
        if key in config:
            config[key] = value
    save_voice_config(config)
    return config


# ─── Natural Speech Patterns ───────────────────────────────────────────────────

# Common contractions to make speech sound natural
CONTRACTIONS = {
    "i am": "I'm",
    "i have": "I've",
    "i will": "I'll",
    "i would": "I'd",
    "you are": "you're",
    "you have": "you've",
    "you will": "you'll",
    "you would": "you'd",
    "he is": "he's",
    "she is": "she's",
    "it is": "it's",
    "we are": "we're",
    "they are": "they're",
    "that is": "that's",
    "what is": "what's",
    "who is": "who's",
    "there is": "there's",
    "here is": "here's",
    "do not": "don't",
    "does not": "doesn't",
    "did not": "didn't",
    "is not": "isn't",
    "are not": "aren't",
    "was not": "wasn't",
    "were not": "weren't",
    "have not": "haven't",
    "has not": "hasn't",
    "had not": "hadn't",
    "will not": "won't",
    "would not": "wouldn't",
    "could not": "couldn't",
    "should not": "shouldn't",
    "can not": "can't",
    "cannot": "can't",
    "let us": "let's",
    "going to": "gonna",
    "want to": "wanna",
    "got to": "gotta",
}

# Natural fillers that real people use
NATURAL_FILLERS = {
    "thinking": ["um", "uh", "hmm", "well", "so", "you know", "I mean", "let me think"],
    "transition": ["anyway", "so", "well", "okay so", "alright", "right"],
    "emphasis": ["actually", "basically", "honestly", "really", "literally"],
    "agreement": ["yeah", "yes", "uh-huh", "right", "exactly", "absolutely"],
    "uncertainty": ["I think", "maybe", "probably", "I guess", "kind of", "sort of"],
}

# Breathing and pause markers (for SSML or custom processing)
PAUSE_MARKERS = {
    "short": "...",
    "medium": "... ",
    "long": "...... ",
    "breath": "*breath* ",
}

# Personality-specific speech adjustments
PERSONALITY_SPEECH = {
    "casual": {
        "use_contractions": True,
        "filler_frequency": 0.3,
        "formal_words_to_casual": {
            "hello": "hey",
            "goodbye": "bye",
            "yes": "yeah",
            "no": "nah",
            "thank you": "thanks",
            "please": "please",
            "perhaps": "maybe",
            "certainly": "sure",
            "I understand": "I get it",
            "I apologize": "sorry",
        },
    },
    "warm": {
        "add_endearments": True,
        "endearments": ["dear", "sweetie", "hun", "love"],
        "warm_expressions": ["oh", "aww", "hmm", "ahh"],
    },
    "confident": {
        "remove_hedging": True,
        "hedging_words": ["maybe", "perhaps", "I think", "I guess", "kind of", "sort of"],
        "strong_words": ["definitely", "absolutely", "certainly", "clearly"],
    },
}


# ─── Speech Humanization Functions ─────────────────────────────────────────────

def apply_contractions(text):
    """Replace formal phrases with natural contractions."""
    result = text
    for formal, contraction in CONTRACTIONS.items():
        # Case insensitive replacement
        pattern = re.compile(re.escape(formal), re.IGNORECASE)
        result = pattern.sub(contraction, result)
    return result


def add_natural_fillers(text, persona_type="default", frequency=0.2):
    """Add natural speech fillers to make text sound more human."""
    if random.random() > frequency:
        return text
    
    sentences = text.split('. ')
    result = []
    
    for i, sentence in enumerate(sentences):
        if i == 0 and random.random() < 0.3:
            # Sometimes add a filler at the start
            filler = random.choice(NATURAL_FILLERS["thinking"])
            sentence = f"{filler.capitalize()}, {sentence[0].lower()}{sentence[1:]}" if sentence else sentence
        elif random.random() < frequency:
            # Add filler between sentences
            filler = random.choice(NATURAL_FILLERS["transition"])
            sentence = f"{filler.capitalize()}, {sentence[0].lower()}{sentence[1:]}" if sentence else sentence
        
        result.append(sentence)
    
    return '. '.join(result)


def add_pauses(text, style="natural"):
    """Add natural pauses to text for more realistic speech timing."""
    # Add pauses after certain punctuation
    text = re.sub(r'([,;:])\s', r'\1 ... ', text)
    
    # Add longer pauses after periods
    text = re.sub(r'(\.) ', r'\1 ...... ', text)
    
    # Add thinking pauses before certain phrases
    thinking_triggers = ["I think", "maybe", "probably", "well", "so"]
    for trigger in thinking_triggers:
        text = text.replace(trigger, f"... {trigger}")
    
    return text


def add_breathing_sounds(text):
    """Add subtle breathing markers for more natural speech rhythm."""
    sentences = text.split('. ')
    result = []
    
    for i, sentence in enumerate(sentences):
        # Add breath marker occasionally between long sentences
        if i > 0 and len(sentence) > 50 and random.random() < 0.4:
            sentence = f"*breath* {sentence}"
        result.append(sentence)
    
    return '. '.join(result)


def add_personality_touches(text, personality="casual"):
    """Add personality-specific speech touches."""
    if personality not in PERSONALITY_SPEECH:
        return text
    
    style = PERSONALITY_SPEECH[personality]
    
    if style.get("use_contractions"):
        text = apply_contractions(text)
    
    if style.get("add_endearments") and random.random() < 0.3:
        endearment = random.choice(style.get("endearments", []))
        text = f"{text}, {endearment}"
    
    if "formal_words_to_casual" in style:
        for formal, casual in style["formal_words_to_casual"].items():
            text = text.replace(formal, casual)
            text = text.replace(formal.capitalize(), casual.capitalize())
    
    return text


def humanize_text(text, persona_id=None, config=None):
    """
    Main function to humanize text for more natural speech.
    
    Args:
        text: The text to humanize
        persona_id: Optional persona ID for personality-specific touches
        config: Optional voice config override
    
    Returns:
        Humanized text that sounds more natural when spoken
    """
    if config is None:
        config = load_voice_config()
    
    humanization = config.get("humanization", {})
    
    if not humanization.get("enabled", True):
        return text
    
    # Apply contractions for natural speech
    if humanization.get("use_contractions", True):
        text = apply_contractions(text)
    
    # Add natural fillers
    if humanization.get("add_fillers", True):
        variation = humanization.get("variation_level", 0.7)
        text = add_natural_fillers(text, frequency=variation * 0.3)
    
    # Add personality touches based on persona
    if persona_id == "lamai":
        text = add_personality_touches(text, "warm")
    elif persona_id == "coach_jv":
        text = add_personality_touches(text, "confident")
    else:
        text = add_personality_touches(text, "casual")
    
    return text


# ─── Voice Cloning Support ─────────────────────────────────────────────────────

def add_cloned_voice(name, voice_id, provider="elevenlabs"):
    """Add a cloned voice to the configuration."""
    config = load_voice_config()
    config["cloned_voices"][name] = {
        "voice_id": voice_id,
        "provider": provider,
    }
    save_voice_config(config)
    return config


def get_cloned_voice(name):
    """Get a cloned voice by name."""
    config = load_voice_config()
    return config.get("cloned_voices", {}).get(name)


def list_cloned_voices():
    """List all saved cloned voices."""
    config = load_voice_config()
    return config.get("cloned_voices", {})


def remove_cloned_voice(name):
    """Remove a cloned voice from configuration."""
    config = load_voice_config()
    if name in config.get("cloned_voices", {}):
        del config["cloned_voices"][name]
        save_voice_config(config)
        return True
    return False


# ─── SSML Generation for Advanced TTS ──────────────────────────────────────────

def text_to_ssml(text, voice_settings=None):
    """
    Convert text to SSML for more natural speech synthesis.
    
    SSML (Speech Synthesis Markup Language) allows for:
    - Precise pause control
    - Emphasis on words
    - Pronunciation control
    - Breathing sounds
    """
    if voice_settings is None:
        voice_settings = {}
    
    rate = voice_settings.get("rate", 0.95)
    
    # Start SSML document
    ssml = f'<speak><prosody rate="{rate}">'
    
    # Convert pause markers to SSML breaks
    text = text.replace("...... ", '<break time="600ms"/>')
    text = text.replace("... ", '<break time="300ms"/>')
    text = text.replace("*breath* ", '<break time="200ms"/>')
    
    # Add emphasis to certain words
    emphasis_words = ["really", "very", "so", "absolutely", "definitely"]
    for word in emphasis_words:
        text = text.replace(f" {word} ", f' <emphasis level="moderate">{word}</emphasis> ')
    
    ssml += text
    ssml += '</prosody></speak>'
    
    return ssml


# ─── Voice Provider Configuration ──────────────────────────────────────────────

def get_elevenlabs_config():
    """Get ElevenLabs API configuration for voice cloning."""
    config = load_voice_config()
    return {
        "api_key": config.get("elevenlabs_api_key", ""),
        "voice_id": config.get("elevenlabs_voice_id", ""),
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,        # Lower = more expressive
            "similarity_boost": 0.8,  # Higher = more similar to original
            "style": 0.5,             # Speaking style
            "use_speaker_boost": True,
        },
    }


def set_elevenlabs_config(api_key=None, voice_id=None):
    """Set ElevenLabs API configuration."""
    config = load_voice_config()
    if api_key is not None:
        config["elevenlabs_api_key"] = api_key
    if voice_id is not None:
        config["elevenlabs_voice_id"] = voice_id
    save_voice_config(config)
    return config


# ─── Export Voice Configuration for Frontend ───────────────────────────────────

def get_voice_config_for_frontend():
    """Get voice configuration safe for frontend (no API keys)."""
    config = load_voice_config()
    return {
        "tts_provider": config.get("tts_provider", "browser"),
        "has_elevenlabs": bool(config.get("elevenlabs_api_key")),
        "cloned_voices": list(config.get("cloned_voices", {}).keys()),
        "humanization": config.get("humanization", {}),
        "speech_settings": config.get("speech_settings", {}),
    }
