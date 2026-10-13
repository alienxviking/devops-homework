import os

from flask import Flask, jsonify, request

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "dev")

notes = []


@app.route("/")
def index():
    return jsonify({
        "message": "Notes API is running",
        "version": APP_VERSION,
        "count": len(notes),
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/notes", methods=["GET"])
def get_notes():
    return jsonify({"notes": notes})


@app.route("/notes", methods=["POST"])
def add_note():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"error": "text is required"}), 400
    note = {"id": len(notes) + 1, "text": text}
    notes.append(note)
    return jsonify(note), 201


@app.route("/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    for note in notes:
        if note["id"] == note_id:
            notes.remove(note)
            return jsonify({"deleted": note_id})
    return jsonify({"error": "note not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
