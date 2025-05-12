from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import requests
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from functools import lru_cache
import torch

# Cargar variables de entorno
load_dotenv()

# Configuración de la aplicación
app = Flask(__name__)
CORS(app)  # Habilitar CORS para permitir solicitudes desde front-ends

# Configuración de logging
if not os.path.exists('logs'):
    os.makedirs('logs')
    
handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=3)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Cargar las claves API desde variables de entorno
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    app.logger.error("MISTRAL_API_KEY no encontrada en las variables de entorno")
    raise ValueError("MISTRAL_API_KEY es requerida para ejecutar la aplicación")

# Configurar el uso de CPU y limitar memoria
torch.cuda.is_available = lambda: False  # Forzar uso de CPU
torch.set_num_threads(4)  # Limitar número de hilos

# Clasificador de emociones (GoEmotions con DistilRoBERTa)
try:
    emotion_classifier = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=3,  # Obtener las 3 emociones más probables para un análisis más completo
        device=-1,  # -1 fuerza el uso de CPU
        model_kwargs={
            'low_cpu_mem_usage': True,
            'max_memory': {'cpu': "2GB"}
        }
    )
    app.logger.info("Clasificador de emociones cargado correctamente en CPU")
except Exception as e:
    app.logger.error(f"Error al cargar el clasificador de emociones: {e}")
    raise

# Mapeo de emociones del inglés al español
EMOTION_MAPPING = {
    "admiration": "admiración",
    "amusement": "diversión",
    "anger": "enojo",
    "annoyance": "irritación",
    "approval": "aprobación",
    "caring": "cuidado",
    "confusion": "confusión",
    "curiosity": "curiosidad",
    "desire": "deseo",
    "disappointment": "decepción",
    "disapproval": "desaprobación",
    "disgust": "asco",
    "embarrassment": "vergüenza",
    "excitement": "emoción",
    "fear": "miedo",
    "gratitude": "gratitud",
    "grief": "dolor",
    "joy": "alegría",
    "love": "amor",
    "nervousness": "nerviosismo",
    "optimism": "optimismo",
    "pride": "orgullo",
    "realization": "comprensión",
    "relief": "alivio",
    "remorse": "remordimiento",
    "sadness": "tristeza",
    "surprise": "sorpresa",
    "neutral": "neutral"
}

# Detectar idioma del texto
def detect_language(text):
    """Detecta si el texto está en español o inglés de forma simple."""
    spanish_words = {'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'pero', 'porque', 'como', 'qué', 'quién', 'cuándo', 'dónde', 'cómo'}
    
    words = set(text.lower().split())
    spanish_count = len(words.intersection(spanish_words))
    
    return 'es' if spanish_count > 0 else 'en'

# Traducir texto usando API de Mistral (para permitir mensajes en inglés o español)
@lru_cache(maxsize=100)
def translate_text(text, source_lang, target_lang):
    """Traduce texto usando la API de Mistral si es necesario."""
    if source_lang == target_lang:
        return text
        
    prompt = f"Traduce el siguiente texto de {source_lang} a {target_lang}. Solo devuelve la traducción sin explicaciones:\n\n{text}"
    
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "mistral-small",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 150
    }
    
    try:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        app.logger.error(f"Error al traducir texto: {e}")
        return text  # Devolvemos el texto original si hay un error

def generate_mistral_response(user_input, emotions, user_lang='es'):
    """
    Genera una respuesta empática basada en las emociones detectadas.
    
    Args:
        user_input: Texto del usuario
        emotions: Lista de diccionarios con las emociones detectadas
        user_lang: Idioma del usuario (es o en)
    """
    # Formatear las emociones detectadas
    emotion_str = ", ".join([
        f"{EMOTION_MAPPING.get(e['label'], e['label'])} ({int(e['score'] * 100)}%)" 
        for e in emotions[:3]
    ])
    
    # Prompt adaptado para personas con TEA
    prompt = f"""
Este mensaje ha sido enviado por una persona dentro del espectro autista (TEA). Las emociones detectadas automáticamente (con sus porcentajes de confianza) son: {emotion_str}.

Ten en cuenta que la persona puede:
- Ser muy literal y preferir respuestas claras y directas
- Sentirse incómoda con sarcasmo o lenguaje figurado
- Necesitar empatía sin condescendencia
- Beneficiarse de explicaciones estructuradas y lógicas

Por favor, responde en español, de manera amable, calmada, comprensiva y clara. Usa frases cortas y evita ambigüedades.

Mensaje del usuario: {user_input}

Asistente:
"""

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistral-small",  # Usa mistral-medium para mejor calidad
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 300
    }

    try:
        app.logger.info(f"Enviando solicitud a Mistral API con emociones: {emotion_str}")
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15  # Timeout de 15 segundos
        )
        response.raise_for_status()
        ai_response = response.json()["choices"][0]["message"]["content"].strip()
        
        # Si la respuesta del usuario fue en inglés, traducimos la respuesta
        if user_lang == 'en':
            ai_response = translate_text(ai_response, 'es', 'en')
            
        return ai_response
    except requests.exceptions.Timeout:
        app.logger.error("Timeout en la solicitud a Mistral API")
        return "Lo siento, el servicio está tardando demasiado en responder. Por favor, intenta nuevamente."
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error con la API de Mistral: {e}")
        return "Lo siento, ha ocurrido un problema al comunicarse con el servicio. Por favor, intenta más tarde."
    except Exception as e:
        app.logger.error(f"Error inesperado: {e}")
        return "Lo siento, ha ocurrido un error inesperado."

@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint para verificar que el servicio está funcionando."""
    return jsonify({"status": "ok", "message": "El servicio está activo"})

@app.route("/chatbot", methods=["POST"])
def chatbot():
    """Endpoint principal del chatbot para procesar los mensajes de los usuarios."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Se esperaba un cuerpo JSON"}), 400
            
        user_text = data.get("text", "").strip()
        if not user_text:
            return jsonify({"error": "El campo 'text' es obligatorio"}), 400

        app.logger.info(f"Mensaje recibido: {user_text[:50]}{'...' if len(user_text) > 50 else ''}")
        
        # Detectar idioma
        user_lang = detect_language(user_text)
        app.logger.info(f"Idioma detectado: {user_lang}")
        
        # Si el texto está en inglés, lo traducimos para el clasificador de emociones
        text_for_classification = user_text
        if user_lang == 'en':
            text_for_classification = translate_text(user_text, 'en', 'es')
        
        # Detectar emociones
        emotions = emotion_classifier(text_for_classification)
        primary_emotion = emotions[0]["label"]
        
        app.logger.info(f"Emoción principal detectada: {primary_emotion}")
        
        # Obtener respuesta empática
        ai_response = generate_mistral_response(user_text, emotions, user_lang)

        # Construir respuesta
        response_data = {
            "emotions": [
                {
                    "name": e["label"],
                    "name_es": EMOTION_MAPPING.get(e["label"], e["label"]),
                    "confidence": round(e["score"] * 100, 2)
                } 
                for e in emotions[:3]
            ],
            "response": ai_response,
            "language": user_lang
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"Error en el endpoint /chatbot: {e}", exc_info=True)
        return jsonify({"error": "Ha ocurrido un error interno en el servidor"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.logger.info(f"Iniciando servidor en el puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")