"""Phone Log Web Application - Flask-based web interface with voice assistant."""

import json
from flask import Flask, render_template, request, jsonify, Response

import phone_log
import assistant
import voice_config
import analytics
import export

app = Flask(__name__)


# ─── Web Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main web interface."""
    identity = assistant.load_identity()
    return render_template("index.html", identity=identity)


# ─── API Endpoints ─────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Process chat messages and return assistant response with reasoning."""
    data = request.get_json()
    user_input = data.get("message", "").strip()
    
    if not user_input:
        return jsonify({"error": "Message cannot be empty"}), 400
    
    result = assistant.chat(user_input)
    return jsonify(result)


@app.route("/api/identity", methods=["GET"])
def api_get_identity():
    """Get current assistant identity."""
    return jsonify(assistant.load_identity())


@app.route("/api/identity", methods=["PUT"])
def api_update_identity():
    """Update assistant identity."""
    data = request.get_json()
    updated = assistant.update_identity(
        name=data.get("name"),
        role=data.get("role"),
        personality=data.get("personality"),
        greeting=data.get("greeting"),
        voice=data.get("voice"),
    )
    return jsonify(updated)


@app.route("/api/calls", methods=["GET"])
def api_list_calls():
    """List all call records."""
    direction = request.args.get("direction")
    calls = phone_log.get_all()
    if direction:
        calls = [c for c in calls if c["direction"] == direction]
    return jsonify(calls)


@app.route("/api/calls", methods=["POST"])
def api_add_call():
    """Add a new call record."""
    data = request.get_json()
    try:
        entry = phone_log.add_call(
            contact_name=data.get("contact_name", ""),
            phone_number=data.get("phone_number", ""),
            direction=data.get("direction", ""),
            duration_seconds=data.get("duration_seconds"),
            notes=data.get("notes", ""),
        )
        return jsonify(entry), 201
    except ValueError:
        return jsonify({"error": "Invalid call data. Please check all fields."}), 400


@app.route("/api/calls/<int:call_id>", methods=["DELETE"])
def api_delete_call(call_id):
    """Delete a call record by ID."""
    if phone_log.delete_call(call_id):
        return jsonify({"success": True, "message": f"Deleted call {call_id}"})
    return jsonify({"error": f"Call {call_id} not found"}), 404


@app.route("/api/calls/<int:call_id>/notes", methods=["PUT"])
def api_update_notes(call_id):
    """Update notes on a call record."""
    data = request.get_json()
    notes = data.get("notes", "")
    entry = phone_log.update_notes(call_id, notes)
    if entry:
        return jsonify(entry)
    return jsonify({"error": f"Call {call_id} not found"}), 404


@app.route("/api/calls/search", methods=["GET"])
def api_search_calls():
    """Search call records."""
    query = request.args.get("q", "")
    calls = phone_log.search(query)
    return jsonify(calls)


@app.route("/api/history", methods=["GET"])
def api_get_history():
    """Get conversation history."""
    return jsonify(assistant.conversation.get_history())


@app.route("/api/history", methods=["DELETE"])
def api_clear_history():
    """Clear conversation history."""
    assistant.conversation.clear()
    return jsonify({"success": True, "message": "History cleared"})


# ─── Persona Endpoints ─────────────────────────────────────────────────────────

@app.route("/api/personas", methods=["GET"])
def api_list_personas():
    """List all available personas."""
    return jsonify(assistant.get_available_personas())


@app.route("/api/personas/<persona_id>", methods=["POST"])
def api_set_persona(persona_id):
    """Set the assistant to use a specific persona."""
    result = assistant.set_persona(persona_id)
    if result:
        return jsonify(result)
    return jsonify({"error": f"Persona '{persona_id}' not found"}), 404


# ─── Voice Configuration Endpoints ─────────────────────────────────────────────

@app.route("/api/voice/config", methods=["GET"])
def api_get_voice_config():
    """Get voice configuration (safe for frontend - no API keys)."""
    return jsonify(voice_config.get_voice_config_for_frontend())


@app.route("/api/voice/config", methods=["PUT"])
def api_update_voice_config():
    """Update voice configuration."""
    data = request.get_json()
    updated = voice_config.update_voice_config(**data)
    return jsonify(voice_config.get_voice_config_for_frontend())


@app.route("/api/voice/humanize", methods=["POST"])
def api_humanize_text():
    """Humanize text to sound more natural."""
    data = request.get_json()
    text = data.get("text", "")
    persona_id = data.get("persona_id")
    
    humanized = voice_config.humanize_text(text, persona_id)
    return jsonify({"original": text, "humanized": humanized})


@app.route("/api/voice/clones", methods=["GET"])
def api_list_voice_clones():
    """List all saved voice clones."""
    return jsonify(voice_config.list_cloned_voices())


@app.route("/api/voice/clones", methods=["POST"])
def api_add_voice_clone():
    """Add a new voice clone configuration."""
    data = request.get_json()
    name = data.get("name", "")
    voice_id = data.get("voice_id", "")
    provider = data.get("provider", "elevenlabs")
    
    if not name or not voice_id:
        return jsonify({"error": "Name and voice_id are required"}), 400
    
    voice_config.add_cloned_voice(name, voice_id, provider)
    return jsonify({"success": True, "message": f"Voice clone '{name}' added"})


@app.route("/api/voice/clones/<name>", methods=["DELETE"])
def api_remove_voice_clone(name):
    """Remove a voice clone configuration."""
    if voice_config.remove_cloned_voice(name):
        return jsonify({"success": True, "message": f"Voice clone '{name}' removed"})
    return jsonify({"error": f"Voice clone '{name}' not found"}), 404


@app.route("/api/voice/elevenlabs", methods=["PUT"])
def api_set_elevenlabs():
    """Set ElevenLabs API configuration for voice cloning."""
    data = request.get_json()
    voice_config.set_elevenlabs_config(
        api_key=data.get("api_key"),
        voice_id=data.get("voice_id"),
    )
    return jsonify({"success": True, "message": "ElevenLabs configuration updated"})


# ─── Analytics Endpoints ───────────────────────────────────────────────────────

@app.route("/api/analytics/stats", methods=["GET"])
def api_get_statistics():
    """Get comprehensive call statistics."""
    stats = analytics.get_call_statistics()
    return jsonify(stats)


@app.route("/api/analytics/daily", methods=["GET"])
def api_get_daily_stats():
    """Get daily call statistics."""
    days = request.args.get("days", 30, type=int)
    data = analytics.get_calls_per_day(days)
    return jsonify(data)


@app.route("/api/analytics/contacts", methods=["GET"])
def api_get_contact_summary():
    """Get contact summary statistics."""
    data = analytics.get_contact_summary()
    return jsonify(data)


@app.route("/api/analytics/hourly", methods=["GET"])
def api_get_hourly_distribution():
    """Get hourly call distribution."""
    data = analytics.get_hourly_distribution()
    return jsonify(data)


@app.route("/api/analytics/weekly", methods=["GET"])
def api_get_weekly_trends():
    """Get weekly call trends."""
    weeks = request.args.get("weeks", 4, type=int)
    data = analytics.get_weekly_trends(weeks)
    return jsonify(data)


@app.route("/api/analytics/duration-distribution", methods=["GET"])
def api_get_duration_distribution():
    """Get call duration distribution."""
    data = analytics.get_call_duration_distribution()
    return jsonify(data)


# ─── Export Endpoints ──────────────────────────────────────────────────────────

@app.route("/api/export/csv", methods=["GET"])
def api_export_csv():
    """Export call records as CSV."""
    csv_content = export.export_to_csv()
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=phone_log.csv"}
    )


@app.route("/api/export/json", methods=["GET"])
def api_export_json():
    """Export call records as JSON."""
    json_content = export.export_to_json()
    return Response(
        json_content,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=phone_log.json"}
    )


@app.route("/api/export/html", methods=["GET"])
def api_export_html():
    """Export call records as HTML report."""
    html_content = export.export_to_html()
    return Response(
        html_content,
        mimetype="text/html",
        headers={"Content-Disposition": "attachment; filename=phone_log.html"}
    )


@app.route("/api/export/report", methods=["GET"])
def api_generate_report():
    """Generate a text summary report."""
    report = export.generate_summary_report()
    return Response(
        report,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=phone_log_report.txt"}
    )


@app.route("/api/import/csv", methods=["POST"])
def api_import_csv():
    """Import call records from CSV."""
    if "file" not in request.files:
        data = request.get_json()
        if data and "content" in data:
            csv_content = data["content"]
        else:
            return jsonify({"error": "No file or content provided"}), 400
    else:
        file = request.files["file"]
        csv_content = file.read().decode("utf-8")
    
    result = export.import_from_csv(csv_content)
    return jsonify(result)


# ─── Backup and Restore Endpoints ──────────────────────────────────────────────

@app.route("/api/backup", methods=["GET"])
def api_backup():
    """Create a full backup of all data."""
    calls = phone_log.get_all()
    identity = assistant.load_identity()
    voice_cfg = voice_config.load_voice_config()
    
    backup_data = {
        "version": "1.0",
        "timestamp": get_current_utc_datetime().isoformat(),
        "calls": calls,
        "identity": identity,
        "voice_config": voice_cfg,
    }
    
    return Response(
        json.dumps(backup_data, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=phone_log_backup.json"}
    )


@app.route("/api/restore", methods=["POST"])
def api_restore():
    """Restore data from a backup."""
    if "file" not in request.files:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No backup data provided"}), 400
        backup_data = data
    else:
        file = request.files["file"]
        backup_data = json.loads(file.read().decode("utf-8"))
    
    try:
        # Restore calls
        if "calls" in backup_data:
            # Clear existing and restore
            phone_log._save(backup_data["calls"])
        
        # Restore identity
        if "identity" in backup_data:
            assistant.save_identity(backup_data["identity"])
        
        # Restore voice config
        if "voice_config" in backup_data:
            voice_config.save_voice_config(backup_data["voice_config"])
        
        return jsonify({"success": True, "message": "Backup restored successfully"})
    except (json.JSONDecodeError, KeyError, TypeError):
        return jsonify({"error": "Invalid backup format"}), 400
    except Exception:
        return jsonify({"error": "Restore failed. Please check the backup file."}), 400


def get_current_utc_datetime():
    """Return the current UTC datetime."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


# ─── Main Entry Point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    debug_mode = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    print("\n" + "=" * 60)
    print("  Phone Log Web Assistant")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60 + "\n")
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
