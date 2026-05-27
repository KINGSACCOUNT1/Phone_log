# Phone Log

A lightweight command-line application for logging and managing phone call records.  
All data is stored locally in a `call_log.json` file – no external dependencies required.

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

---

## Requirements

- Python 3.8 or later (standard library only – no `pip install` needed)

---

## Usage

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

## Project Structure

```
Phone_log/
├── phone_log.py          # Core module – data model and CRUD operations
├── cli.py                # Command-line interface (argparse)
├── call_log.json         # Auto-created data file (git-ignored)
├── tests/
│   └── test_phone_log.py # Unit tests
└── README.md
```
