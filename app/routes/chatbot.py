from flask import Blueprint, request, jsonify
from app.services.emotion_service import emotion_service
from app.services.translation_service import translation_service
from app.utils.language import detect_language

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "El servicio está activo"})

@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "El campo 'text' es obligatorio"}), 400
            
        user_text = data['text'].strip()
        if not user_text:
            return jsonify({"error": "El texto no puede estar vacío"}), 400

        user_lang = detect_language(user_text)
        emotions = emotion_service.analyze(user_text)
        
        response_data = {
            "emotions": emotions,
            "language": user_lang,
            "response": "Respuesta del chatbot"  # Implementar lógica de respuesta
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
