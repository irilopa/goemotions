import os
import sys
from pathlib import Path

# Configuración mejorada del PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ["PYTHONPATH"] = str(PROJECT_ROOT)

# Imports absolutos desde la raíz del proyecto
from flask import Flask
from flask_cors import CORS
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.routes import register_routes

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    settings.validate()
    setup_logging(app)
    register_routes(app)
    
    return app

# Crear la aplicación para wsgi/asgi servers
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.logger.info(f"Iniciando servidor en el puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")
