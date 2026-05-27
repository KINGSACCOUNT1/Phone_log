# Phone Log Voice

Speech-to-speech character conversation app with:
- Expo React Native mobile client
- Node.js Express backend
- Optional OpenAI STT + LLM + TTS pipeline

This project is designed for realistic synthetic character voices (male/female style presets) while avoiding real-person impersonation.

## Project Structure

- apps/mobile: Expo phone app (record voice, send turn, play response)
- apps/server: API for STT, reply generation, and TTS

## Features

- Push-to-talk input from mobile
- Character selection (female/male presets)
- Speech-to-speech response loop
- Session memory per conversation id (short rolling history)
- Playback interruption when user starts speaking again
- URL-based audio playback for lower response latency on mobile
- Local fallback mode when no API key is configured
- Safety prompting to avoid identity impersonation

## Prerequisites

- Node.js 20+
- npm 10+
- Expo Go app on your phone (for fastest testing)

## Setup

1. Install dependencies from repo root:

	npm install

2. Configure backend environment:

	cp apps/server/.env.example apps/server/.env

3. Configure mobile environment:

	cp apps/mobile/.env.example apps/mobile/.env

4. Set your API base URL in apps/mobile/.env:

	EXPO_PUBLIC_API_BASE_URL=http://YOUR_COMPUTER_IP:4000

5. Optional: enable full STT + LLM + TTS by setting in apps/server/.env:

	OPENAI_API_KEY=your_key_here

## Run

Run backend:

npm run dev:server

Run mobile app (new terminal):

npm run dev:mobile

Then scan the Expo QR code with your phone.

## API Endpoint

POST /api/session/turn

Form fields:
- audio: audio file (m4a) from mobile recording
- character: JSON string with:
  - characterName
  - persona
  - gender (woman or man)

Response:
- sessionId
- transcript
- replyText
- audioBase64 (null in fallback mode)
- audioUrl (temporary streaming-friendly URL when TTS is enabled)
- mimeType
- usedVoice

Extra endpoints:
- GET /api/audio/:audioId (temporary audio file, 5 minute TTL)
- GET /api/session/:sessionId/history (debug conversation memory)

## Safety

- The app is for synthetic character voices.
- Do not use it to mimic or impersonate real people.
- Always disclose AI voice use when required by law/policy.
