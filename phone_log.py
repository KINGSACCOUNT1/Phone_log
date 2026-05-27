"""Phone Log - core module for managing phone call records."""

import json
import os
from datetime import datetime, timezone

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "call_log.json")

DIRECTIONS = ("incoming", "outgoing", "missed")


def _load(path=None):
    """Load call log entries from the JSON data file."""
    file_path = path or DATA_FILE
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save(logs, path=None):
    """Persist call log entries to the JSON data file."""
    file_path = path or DATA_FILE
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)


def _next_id(logs):
    """Return the next available integer ID."""
    if not logs:
        return 1
    return max(entry["id"] for entry in logs) + 1


def add_call(contact_name, phone_number, direction, duration_seconds=None, notes="", data_file=None):
    """Add a new call log entry.

    Args:
        contact_name (str): Name of the contact.
        phone_number (str): Phone number of the contact.
        direction (str): One of 'incoming', 'outgoing', or 'missed'.
        duration_seconds (int | None): Duration of the call in seconds (None for missed calls).
        notes (str): Optional free-text notes about the call.
        data_file (str | None): Override path for the data file (used in tests).

    Returns:
        dict: The newly created call log entry.

    Raises:
        ValueError: If any required field is invalid.
    """
    contact_name = contact_name.strip()
    phone_number = phone_number.strip()
    direction = direction.strip().lower()

    if not contact_name:
        raise ValueError("contact_name must not be empty.")
    if not phone_number:
        raise ValueError("phone_number must not be empty.")
    if direction not in DIRECTIONS:
        raise ValueError(f"direction must be one of {DIRECTIONS}.")
    if duration_seconds is not None:
        duration_seconds = int(duration_seconds)
        if duration_seconds < 0:
            raise ValueError("duration_seconds must be a non-negative integer.")

    logs = _load(data_file)
    entry = {
        "id": _next_id(logs),
        "contact_name": contact_name,
        "phone_number": phone_number,
        "direction": direction,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": duration_seconds,
        "notes": notes.strip(),
    }
    logs.append(entry)
    _save(logs, data_file)
    return entry


def get_all(data_file=None):
    """Return all call log entries, most recent first.

    Args:
        data_file (str | None): Override path for the data file.

    Returns:
        list[dict]: All call log entries sorted by timestamp descending.
    """
    logs = _load(data_file)
    return sorted(logs, key=lambda e: e["timestamp"], reverse=True)


def search(query, data_file=None):
    """Search call log entries by contact name or phone number (case-insensitive).

    Args:
        query (str): Search term to match against contact_name or phone_number.
        data_file (str | None): Override path for the data file.

    Returns:
        list[dict]: Matching entries sorted by timestamp descending.
    """
    query = query.strip().lower()
    if not query:
        return []
    logs = _load(data_file)
    matches = [
        e for e in logs
        if query in e["contact_name"].lower() or query in e["phone_number"]
    ]
    return sorted(matches, key=lambda e: e["timestamp"], reverse=True)


def delete_call(call_id, data_file=None):
    """Delete a call log entry by ID.

    Args:
        call_id (int): The ID of the entry to delete.
        data_file (str | None): Override path for the data file.

    Returns:
        bool: True if an entry was deleted, False if no entry matched the ID.
    """
    logs = _load(data_file)
    new_logs = [e for e in logs if e["id"] != call_id]
    if len(new_logs) == len(logs):
        return False
    _save(new_logs, data_file)
    return True


def update_notes(call_id, notes, data_file=None):
    """Update the notes field of a call log entry.

    Args:
        call_id (int): The ID of the entry to update.
        notes (str): New notes text.
        data_file (str | None): Override path for the data file.

    Returns:
        dict | None: The updated entry, or None if not found.
    """
    logs = _load(data_file)
    for entry in logs:
        if entry["id"] == call_id:
            entry["notes"] = notes.strip()
            _save(logs, data_file)
            return entry
    return None


def format_duration(seconds):
    """Convert a duration in seconds to a human-readable string (e.g. '2m 30s').

    Args:
        seconds (int | None): Duration in seconds, or None.

    Returns:
        str: Formatted duration string, or '-' if None.
    """
    if seconds is None:
        return "-"
    minutes, secs = divmod(int(seconds), 60)
    hours, mins = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}h {mins}m {secs}s"
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"
