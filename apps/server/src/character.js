const VOICE_PRESETS = {
  woman: {
    voice: "alloy",
    stylePrompt:
      "You are a warm, natural, emotionally intelligent female voice assistant. Keep responses concise and spoken-word friendly.",
  },
  man: {
    voice: "verse",
    stylePrompt:
      "You are a grounded, natural, confident male voice assistant. Keep responses concise and spoken-word friendly.",
  },
};

function getVoicePreset(gender) {
  return VOICE_PRESETS[gender] || VOICE_PRESETS.woman;
}

function buildSystemPrompt({ characterName, persona, gender }) {
  const preset = getVoicePreset(gender);
  return [
    "You are a character in a live voice conversation app.",
    "Never claim to be a real person or copied identity.",
    "Be natural, emotionally aware, and conversational.",
    "Keep responses under 60 words unless user asks for detail.",
    `Character name: ${characterName || "Nova"}`,
    `Persona: ${persona || "Friendly daily assistant"}`,
    preset.stylePrompt,
  ].join(" ");
}

module.exports = {
  getVoicePreset,
  buildSystemPrompt,
};
