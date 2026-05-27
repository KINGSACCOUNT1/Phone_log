# Phone Log

A lightweight command-line and web application for logging and managing phone call records.  
All data is stored locally in a `call_log.json` file – no external database required.

---

## Features

| Feature | Status |
|---------|--------|
| Add incoming / outgoing / missed calls | ✅ |
| View all call records (newest first) | ✅ |
| Filter records by direction | ✅ |
| Search by contact name or phone number | ✅ |
| Delete a record by ID | ✅ |
| Update notes on an existing record | ✅ |
| Human-readable duration formatting | ✅ |
| **Web GUI with voice assistant** | ✅ |
| **Customizable assistant identity** | ✅ |
| **Multiple personas (6 characters)** | ✅ |
| **Speech recognition input** | ✅ |
| **Synthesis preview (reasoning/response)** | ✅ |
| **Call analytics & statistics** | ✅ |
| **Export (CSV, JSON, HTML)** | ✅ |
| **Import from CSV** | ✅ |
| **Backup & restore** | ✅ |
| **Dark/Light theme support** | ✅ |
| **Mobile-responsive design** | ✅ |
| **CI/CD with GitHub Actions** | ✅ |
| **API documentation (OpenAPI)** | ✅ |

---

## Requirements

- Python 3.8 or later
- Flask (for web interface): `pip install flask`

---

## Web Interface (GUI)

### Starting the Web App

```bash
pip install flask
python web_app.py
```

Then open **http://localhost:5000** in your browser.

### Features

1. **Voice Assistant**: Click the 🎤 microphone button and speak naturally
2. **Customizable Identity**: Click ⚙️ to change the assistant's name, role, personality, and greeting
3. **Multiple Personas**: Choose from 6 unique characters with different nationalities and personalities
4. **Synthesis Preview**: See the assistant's reasoning process in real-time
5. **Call Management**: Add, view, search, and delete calls through the GUI
6. **Analytics**: View call statistics, trends, and top contacts
7. **Export/Import**: Export to CSV, JSON, or HTML; import from CSV
8. **Theme Toggle**: Switch between dark and light modes

### Example Voice Commands

- "Show my calls"
- "Search for Alice"
- "How many calls do I have?"
- "Delete call 5"
- "Who are you?"
- "Help"

---

## CLI Usage

Run commands through `cli.py`:

```bash
python cli.py <command> [options]
```

### Add a call

```bash
# Incoming call with duration and notes
python cli.py add "Alice Johnson" "555-1234" incoming --duration 90 --notes "Discussed project"

# Outgoing call (5 minutes)
python cli.py add "Bob Smith" "555-5678" outgoing --duration 300

# Missed call (no duration)
python cli.py add "Unknown" "555-0000" missed
```

### List all calls

```bash
python cli.py list

# Filter by direction
python cli.py list --direction incoming
python cli.py list --direction outgoing
python cli.py list --direction missed
```

### Search calls

```bash
python cli.py search alice
python cli.py search "555-1234"
```

### Update notes on a record

```bash
python cli.py notes 2 "Callback scheduled for tomorrow"
```

### Delete a record

```bash
python cli.py delete 3
```

---

## Data Format

Records are stored in `call_log.json` as a JSON array.  
Each entry has the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique auto-incrementing identifier |
| `contact_name` | string | Name of the contact |
| `phone_number` | string | Phone number |
| `direction` | string | `"incoming"`, `"outgoing"`, or `"missed"` |
| `timestamp` | string | ISO 8601 datetime of when the record was logged |
| `duration_seconds` | int \| null | Duration in seconds (`null` for missed calls) |
| `notes` | string | Optional free-text notes |

---

## Running Tests

```bash
python -m unittest tests/test_phone_log.py -v
```

---

## Deploy to Render

This app is ready for deployment to [Render](https://render.com) using the included Blueprint.

### One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/KINGSACCOUNT1/Phone_log)

### Manual Deploy

1. Fork or push this repo to your GitHub account
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New** → **Blueprint**
4. Connect your GitHub repository
5. Render will automatically detect the `render.yaml` and deploy your app

Your app will be live at `https://phone-log.onrender.com` (or similar URL).

---

## Project Structure

```
Phone_log/
├── phone_log.py          # Core module – data model and CRUD operations
├── cli.py                # Command-line interface (argparse)
├── assistant.py          # Voice assistant – intent recognition & response generation
├── personas.py           # Predefined character personas (6 nationalities)
├── voice_config.py       # Voice humanization and TTS configuration
├── analytics.py          # Call statistics and analytics
├── export.py             # Export/import functionality (CSV, JSON, HTML)
├── web_app.py            # Flask web server with API endpoints
├── templates/
│   └── index.html        # Web interface HTML
├── static/
│   ├── style.css         # Web interface styles (dark/light themes)
│   └── app.js            # Client-side JavaScript (speech recognition, API)
├── docs/
│   ├── openapi.yaml      # API documentation (OpenAPI 3.0)
│   └── VOICE_COMMANDS.md # Voice commands user guide
├── tests/
│   ├── test_phone_log.py # Unit tests for core module
│   ├── test_assistant.py # Tests for assistant module
│   ├── test_personas.py  # Tests for personas module
│   ├── test_voice_config.py # Tests for voice configuration
│   ├── test_analytics.py # Tests for analytics module
│   ├── test_export.py    # Tests for export/import
│   └── test_web_app.py   # Integration tests for web API
├── .github/
│   └── workflows/
│       └── ci.yml        # GitHub Actions CI/CD pipeline
├── call_log.json         # Auto-created data file (git-ignored)
├── assistant_identity.json  # Assistant customization (git-ignored)
├── render.yaml           # Render deployment configuration
└── README.md
```

---

## Available Personas

| Persona | Name | Nationality | Role |
|---------|------|-------------|------|
| `coach_jv` | Coach JV | American | Trading Coach & Mentor |
| `lamai` | Lamai | Thai | Bank Account Manager |
| `maria` | Maria | Mexican | Customer Service Representative |
| `james` | James | British | Technical Support Specialist |
| `yuki` | Yuki | Japanese | Personal Assistant |
| `alex` | Alex | American | Friendly AI Assistant |

---

## API Documentation

The API is documented using OpenAPI 3.0 specification. See `docs/openapi.yaml` for full details.

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/calls` | GET | List all call records |
| `/api/calls` | POST | Add a new call |
| `/api/calls/<id>` | DELETE | Delete a call |
| `/api/chat` | POST | Send message to voice assistant |
| `/api/analytics/stats` | GET | Get call statistics |
| `/api/export/csv` | GET | Export as CSV |
| `/api/export/json` | GET | Export as JSON |
| `/api/backup` | GET | Create full backup |
| `/api/restore` | POST | Restore from backup |

---

## Running Tests

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests/test_phone_log.py -v
```

---

## Development

### Linting

```bash
pip install flake8 black isort

# Check formatting
black --check .
isort --check-only .
flake8 .

# Fix formatting
black .
isort .
```

### CI/CD

This project uses GitHub Actions for continuous integration:
- Linting with flake8, black, and isort
- Testing on Python 3.9, 3.10, 3.11, and 3.12
- Security scanning with Bandit and Safety
