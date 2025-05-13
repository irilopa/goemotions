from .chatbot import chatbot_bp

def register_routes(app):
    app.register_blueprint(chatbot_bp)
