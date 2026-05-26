const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
const multer = require("multer");
const { toFile } = require("openai/uploads");

const { getVoicePreset, buildSystemPrompt } = require("./character");
const { createOpenAIClient } = require("./openaiClient");

dotenv.config();

const app = express();
const upload = multer();
const port = Number(process.env.PORT || 4000);

app.use(
  cors({
    origin: process.env.ALLOWED_ORIGIN || "*",
  })
);
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.post("/api/session/turn", upload.single("audio"), async (req, res) => {
  try {
    const audioFile = req.file;
    const character = safeParse(req.body.character, {
      characterName: "Nova",
      persona: "Friendly daily assistant",
      gender: "woman",
    });
    const userTextFallback = req.body.userText || "";

    if (!audioFile && !userTextFallback) {
      return res.status(400).json({
        error: "Provide either an audio file or userText.",
      });
    }

    const openai = createOpenAIClient();

    let transcript = userTextFallback;
    if (!transcript && audioFile && openai) {
      const transcription = await openai.audio.transcriptions.create({
        file: await toFile(
          audioFile.buffer,
          audioFile.originalname || "speech.m4a",
          {
            type: audioFile.mimetype || "audio/m4a",
          }
        ),
        model: "gpt-4o-mini-transcribe",
      });
      transcript = transcription.text;
    }

    if (!transcript) {
      transcript = "Hello, this is a demo input because STT is not configured.";
    }

    let replyText;
    if (openai) {
      const systemPrompt = buildSystemPrompt(character);
      const completion = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        temperature: 0.8,
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: transcript },
        ],
      });
      replyText = completion.choices?.[0]?.message?.content?.trim();
    }

    if (!replyText) {
      replyText = `I heard you say: ${transcript}. OpenAI key is missing, so this is a local fallback response.`;
    }

    const voicePreset = getVoicePreset(character.gender);
    let audioBase64 = null;

    if (openai) {
      const speech = await openai.audio.speech.create({
        model: "gpt-4o-mini-tts",
        voice: voicePreset.voice,
        input: replyText,
      });

      const audioBuffer = Buffer.from(await speech.arrayBuffer());
      audioBase64 = audioBuffer.toString("base64");
    }

    return res.json({
      transcript,
      replyText,
      audioBase64,
      mimeType: "audio/mpeg",
      usedVoice: voicePreset.voice,
      note: "Character voices are synthetic. Do not impersonate real people.",
    });
  } catch (error) {
    console.error(error);
    return res.status(500).json({
      error: "Failed to process voice turn.",
      detail: error?.message,
    });
  }
});

app.listen(port, () => {
  console.log(`Phone log server listening on port ${port}`);
});

function safeParse(value, fallback) {
  if (!value) {
    return fallback;
  }

  try {
    return JSON.parse(value);
  } catch (_error) {
    return fallback;
  }
}
