"""Phone Log Web Application - Flask-based web interface with voice assistant.

Enhanced with:
- AI capabilities configuration endpoints
- Semantic memory management
- Emotion detection
- Dialog flow management
- WebSocket voice streaming
"""

import json
from flask import Flask, render_template, request, jsonify, Response

import phone_log
import assistant
import voice_config
import analytics
import export

# Import new AI enhancement modules
try:
    import llm_integration
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    import semantic_memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

try:
    import emotion_detection
    EMOTION_AVAILABLE = True
except ImportError:
    EMOTION_AVAILABLE = False

try:
    import dialog_manager
    DIALOG_AVAILABLE = True
except ImportError:
    DIALOG_AVAILABLE = False

try:
    import voice_streaming
    VOICE_STREAMING_AVAILABLE = True
except ImportError:
    VOICE_STREAMING_AVAILABLE = False

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


# ─── AI Capabilities Endpoints ─────────────────────────────────────────────────

@app.route("/api/ai/capabilities", methods=["GET"])
def api_get_ai_capabilities():
    """Get information about available AI capabilities."""
    return jsonify(assistant.get_ai_capabilities())


@app.route("/api/ai/llm/config", methods=["GET"])
def api_get_llm_config():
    """Get LLM configuration (safe for frontend)."""
    if not LLM_AVAILABLE:
        return jsonify({"available": False})
    return jsonify({
        "available": True,
        **llm_integration.get_llm_config_for_frontend()
    })


@app.route("/api/ai/llm/config", methods=["PUT"])
def api_set_llm_config():
    """Configure LLM integration."""
    data = request.get_json()
    provider = data.get("provider", "openai")
    api_key = data.get("api_key", "")
    model = data.get("model")
    
    result = assistant.configure_llm(provider, api_key, model)
    return jsonify(result)


# ─── Semantic Memory Endpoints ─────────────────────────────────────────────────

@app.route("/api/ai/memory", methods=["GET"])
def api_get_memories():
    """Search or list memories."""
    if not MEMORY_AVAILABLE:
        return jsonify({"available": False, "memories": []})
    
    query = request.args.get("q", "")
    memory_type = request.args.get("type")
    limit = request.args.get("limit", 20, type=int)
    
    if query:
        results = assistant.search_memories(query, limit)
    else:
        memory = semantic_memory.get_memory()
        if memory_type:
            results = [m.to_dict() for m in memory.get_by_type(memory_type, limit)]
        else:
            results = [m.to_dict() for m in memory.memories[:limit]]
    
    return jsonify({"available": True, "memories": results})


@app.route("/api/ai/memory", methods=["POST"])
def api_add_memory():
    """Add a new memory."""
    if not MEMORY_AVAILABLE:
        return jsonify({"success": False, "error": "Memory not available"})
    
    data = request.get_json()
    content = data.get("content", "")
    memory_type = data.get("type", "fact")
    tags = data.get("tags", [])
    importance = data.get("importance", 0.5)
    
    if not content:
        return jsonify({"error": "Content is required"}), 400
    
    result = assistant.remember_fact(content, memory_type, tags)
    return jsonify(result)


@app.route("/api/ai/memory/<memory_id>", methods=["DELETE"])
def api_delete_memory(memory_id):
    """Delete a memory by ID."""
    if not MEMORY_AVAILABLE:
        return jsonify({"success": False, "error": "Memory not available"})
    
    if semantic_memory.forget(memory_id):
        return jsonify({"success": True, "message": f"Memory {memory_id} deleted"})
    return jsonify({"error": f"Memory {memory_id} not found"}), 404


@app.route("/api/ai/memory/context", methods=["GET"])
def api_get_memory_context():
    """Get contextual memory summary."""
    if not MEMORY_AVAILABLE:
        return jsonify({"available": False, "context": ""})
    
    topics = request.args.getlist("topic")
    context = assistant.get_memory_summary(topics if topics else None)
    return jsonify({"available": True, "context": context})


# ─── Emotion Detection Endpoints ───────────────────────────────────────────────

@app.route("/api/ai/emotion", methods=["POST"])
def api_analyze_emotion():
    """Analyze emotion in text."""
    if not EMOTION_AVAILABLE:
        return jsonify({"available": False})
    
    data = request.get_json()
    text = data.get("text", "")
    
    if not text:
        return jsonify({"error": "Text is required"}), 400
    
    result = emotion_detection.analyze_emotion(text)
    return jsonify({"available": True, **result})


@app.route("/api/ai/emotion/context", methods=["GET"])
def api_get_emotional_context():
    """Get emotional context from conversation."""
    if not EMOTION_AVAILABLE:
        return jsonify({"available": False})
    
    ctx = emotion_detection.get_emotional_context()
    return jsonify({
        "available": True,
        "trend": ctx.get_emotional_trend(),
        "sentiment_trend": ctx.get_sentiment_trend(),
        "is_escalating": ctx.is_escalating_negative(),
        "history": ctx.history,
    })


# ─── Dialog Manager Endpoints ──────────────────────────────────────────────────

@app.route("/api/ai/dialog/status", methods=["GET"])
def api_get_dialog_status():
    """Get current dialog status."""
    if not DIALOG_AVAILABLE:
        return jsonify({"available": False, "in_dialog": False})
    
    dm = dialog_manager.get_dialog_manager()
    return jsonify({
        "available": True,
        "in_dialog": dm.is_in_flow(),
        "current_flow": dm.get_current_flow(),
        "state": dm.get_state(),
    })


@app.route("/api/ai/dialog/flows", methods=["GET"])
def api_list_dialog_flows():
    """List available dialog flows."""
    if not DIALOG_AVAILABLE:
        return jsonify({"available": False, "flows": []})
    
    dm = dialog_manager.get_dialog_manager()
    flows = []
    for flow_id, flow_data in dm.flows.items():
        flows.append({
            "id": flow_id,
            "name": flow_data.get("name", flow_id),
            "description": flow_data.get("description", ""),
        })
    
    return jsonify({"available": True, "flows": flows})


@app.route("/api/ai/dialog/start/<flow_name>", methods=["POST"])
def api_start_dialog(flow_name):
    """Start a dialog flow."""
    if not DIALOG_AVAILABLE:
        return jsonify({"success": False, "error": "Dialog manager not available"})
    
    result = dialog_manager.start_dialog(flow_name)
    return jsonify(result)


@app.route("/api/ai/dialog/input", methods=["POST"])
def api_dialog_input():
    """Process input in the current dialog."""
    if not DIALOG_AVAILABLE:
        return jsonify({"success": False, "error": "Dialog manager not available"})
    
    data = request.get_json()
    user_input = data.get("input", "")
    
    if not user_input:
        return jsonify({"error": "Input is required"}), 400
    
    result = dialog_manager.process_dialog_input(user_input)
    return jsonify(result)


@app.route("/api/ai/dialog/cancel", methods=["POST"])
def api_cancel_dialog():
    """Cancel the current dialog."""
    if not DIALOG_AVAILABLE:
        return jsonify({"success": False, "error": "Dialog manager not available"})
    
    result = dialog_manager.cancel_dialog()
    return jsonify(result)


# ─── Voice Streaming Endpoints ─────────────────────────────────────────────────

@app.route("/api/voice/stream/sessions", methods=["GET"])
def api_list_voice_sessions():
    """List active voice streaming sessions."""
    if not VOICE_STREAMING_AVAILABLE:
        return jsonify({"available": False, "sessions": []})
    
    manager = voice_streaming.get_voice_stream_manager()
    return jsonify({
        "available": True,
        "sessions": manager.list_sessions(),
    })


@app.route("/api/voice/stream/session", methods=["POST"])
def api_create_voice_session():
    """Create a new voice streaming session."""
    if not VOICE_STREAMING_AVAILABLE:
        return jsonify({"success": False, "error": "Voice streaming not available"})
    
    data = request.get_json() or {}
    config_data = data.get("config", {})
    
    config = voice_streaming.VoiceStreamConfig(
        sample_rate=config_data.get("sample_rate", 16000),
        channels=config_data.get("channels", 1),
        format=config_data.get("format", "pcm"),
        language=config_data.get("language", "en-US"),
    )
    
    manager = voice_streaming.get_voice_stream_manager()
    session = manager.create_session(config=config)
    
    return jsonify({
        "success": True,
        "session": session.to_dict(),
    })


@app.route("/api/voice/stream/session/<session_id>", methods=["DELETE"])
def api_close_voice_session(session_id):
    """Close a voice streaming session."""
    if not VOICE_STREAMING_AVAILABLE:
        return jsonify({"success": False, "error": "Voice streaming not available"})
    
    manager = voice_streaming.get_voice_stream_manager()
    if manager.close_session(session_id):
        return jsonify({"success": True, "message": f"Session {session_id} closed"})
    return jsonify({"error": f"Session {session_id} not found"}), 404


@app.route("/api/voice/stream/session/<session_id>/text", methods=["POST"])
def api_voice_session_text(session_id):
    """Send text input to a voice session."""
    if not VOICE_STREAMING_AVAILABLE:
        return jsonify({"success": False, "error": "Voice streaming not available"})
    
    data = request.get_json()
    text = data.get("text", "")
    
    if not text:
        return jsonify({"error": "Text is required"}), 400
    
    handler = voice_streaming.create_voice_handler(assistant.chat)
    result = handler.handle_message({
        "type": "text",
        "session_id": session_id,
        "text": text,
    })
    
    return jsonify(result)


# ─── Main Entry Point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    debug_mode = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    print("\n" + "=" * 60)
    print("  Phone Log Web Assistant")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60 + "\n")
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
