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
- Local fallback mode when no API key is configured
- Safety prompting to avoid identity impersonation

## New Features

### Offline Mode
- The mobile app now detects network connectivity and provides a fallback error message when offline.

### Enhanced Security
- The backend server includes rate limiting and input validation to prevent abuse.
- Security headers are applied using Helmet.

### Improved UI
- The mobile app features an interactive character selection component.
- Enhanced status indicators for recording and processing states.

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
- transcript
- replyText
- audioBase64 (null in fallback mode)
- mimeType
- usedVoice

## Safety

- The app is for synthetic character voices.
- Do not use it to mimic or impersonate real people.
- Always disclose AI voice use when required by law/policy.

## Testing

### Mobile App
1. Ensure the Expo Go app is installed on your phone.
2. Run the mobile app using:

	npm run dev:mobile

3. Test the offline mode by disabling your internet connection.

### Backend Server
1. Start the server using:

	npm run dev:server

2. Test the `/api/session/turn` endpoint with valid and invalid inputs to verify validation and rate limiting.

## Contribution

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.
