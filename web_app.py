"""Phone Log Web Application - Flask-based web interface with voice assistant."""

import json
from flask import Flask, render_template, request, jsonify

import phone_log
import assistant

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


# ─── Main Entry Point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    debug_mode = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    print("\n" + "=" * 60)
    print("  Phone Log Web Assistant")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60 + "\n")
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
