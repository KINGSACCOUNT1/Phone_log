const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
const multer = require("multer");
const { toFile } = require("openai/uploads");
const rateLimit = require("express-rate-limit");
const helmet = require("helmet");
const { body, validationResult } = require("express-validator");

const { getVoicePreset, buildSystemPrompt } = require("./character");
const { createOpenAIClient } = require("./openaiClient");

dotenv.config();

const app = express();
const upload = multer();
const port = Number(process.env.PORT || 4000);

const sessionStore = new Map(); // In-memory session store

app.use(
  cors({
    origin: process.env.ALLOWED_ORIGIN || "*",
  })
);
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

// Apply security headers
app.use(helmet());

// Rate limiting middleware
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
});
app.use(limiter);

app.post(
  "/api/session/turn",
  upload.single("audio"),
  body("character").isString().withMessage("Character data must be a string."),
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

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
        });
        transcript = transcription.text;
      }

      if (!transcript) {
        transcript = "Hello, this is a demo input because STT is not configured.";
      }

      const sessionId = req.body.sessionId || "default";
      if (!sessionStore.has(sessionId)) {
        sessionStore.set(sessionId, []);
      }

      const sessionHistory = sessionStore.get(sessionId);

      // Limit session history to the last 5 messages
      if (sessionHistory.length > 5) {
        sessionHistory.shift();
      }

      // Add user input to session history
      sessionHistory.push({ role: "user", content: transcript });

      let replyText;
      if (openai) {
        const systemPrompt = buildSystemPrompt(character);
        const completion = await openai.chat.completions.create({
          model: "gpt-4o-mini",
          temperature: 0.8,
          messages: [
            { role: "system", content: systemPrompt },
            ...sessionHistory,
          ],
        });
        replyText = completion.choices?.[0]?.message?.content?.trim();
      }

      if (replyText) {
        sessionHistory.push({ role: "assistant", content: replyText });
      }

      res.json({ transcript, replyText });
    } catch (error) {
      res.status(500).json({ error: "Internal server error." });
    }
  }
);

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
