"""
Guardian Suggestions Management
Handles health suggestions from guardians to elderly
"""

from flask import Blueprint, request, jsonify
import json
import os
from datetime import datetime

suggestions_bp = Blueprint('suggestions', __name__)

# Data files
SUGGESTIONS_FILE = 'suggestions.json'
ELDERLY_FILE = 'elderly.json'

def load_suggestions():
    """Load suggestions data"""
    if os.path.exists(SUGGESTIONS_FILE):
        with open(SUGGESTIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_suggestions(suggestions):
    """Save suggestions data"""
    with open(SUGGESTIONS_FILE, 'w') as f:
        json.dump(suggestions, f, indent=2)

def load_elderly():
    """Load elderly data"""
    if os.path.exists(ELDERLY_FILE):
        with open(ELDERLY_FILE, 'r') as f:
            return json.load(f)
    return {}

@suggestions_bp.route("/suggestions", methods=["POST"])
def add_suggestion():
    """Add health suggestion for elderly person"""
    try:
        data = request.get_json()
        elderly_id = data.get('elderly_id')
        title = data.get('title')
        details = data.get('details')
        priority = data.get('priority', 'normal')
        
        if not all([elderly_id, title, details]):
            return jsonify({
                "status": "error",
                "message": "Missing required fields"
            }), 400
        
        suggestions = load_suggestions()
        suggestion_id = f"{elderly_id}_{title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        suggestions[suggestion_id] = {
            "id": suggestion_id,
            "elderly_id": elderly_id,
            "title": title,
            "details": details,
            "priority": priority,
            "created_at": datetime.now().isoformat()
        }
        
        save_suggestions(suggestions)
        
        print(f"[SUGGESTION] Added suggestion '{title}' for {elderly_id}")
        
        return jsonify({
            "status": "success",
            "message": "Suggestion added successfully",
            "suggestion_id": suggestion_id
        }), 201
        
    except Exception as e:
        print(f"Error adding suggestion: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@suggestions_bp.route("/suggestions/<elderly_id>", methods=["GET"])
def get_suggestions(elderly_id):
    """Get all suggestions for an elderly person"""
    try:
        suggestions = load_suggestions()
        elderly_suggestions = [
            suggestion for suggestion in suggestions.values()
            if suggestion.get('elderly_id') == elderly_id
        ]
        
        # Sort by priority and creation time
        priority_order = {'urgent': 0, 'important': 1, 'normal': 2}
        elderly_suggestions.sort(key=lambda x: (priority_order.get(x.get('priority', 'normal'), 2), x.get('created_at', '')))
        
        return jsonify({
            "status": "success",
            "suggestions": elderly_suggestions
        }), 200
        
    except Exception as e:
        print(f"Error getting suggestions: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@suggestions_bp.route("/suggestions/<suggestion_id>", methods=["DELETE"])
def remove_suggestion(suggestion_id):
    """Remove a suggestion"""
    try:
        suggestions = load_suggestions()
        
        if suggestion_id not in suggestions:
            return jsonify({
                "status": "error",
                "message": "Suggestion not found"
            }), 404
        
        del suggestions[suggestion_id]
        save_suggestions(suggestions)
        
        print(f"[SUGGESTION] Removed suggestion {suggestion_id}")
        
        return jsonify({
            "status": "success",
            "message": "Suggestion removed successfully"
        }), 200
        
    except Exception as e:
        print(f"Error removing suggestion: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
