import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "GoEmotions API"
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY")
    MODEL_NAME: str = "j-hartmann/emotion-english-distilroberta-base"
    MAX_TOKENS: int = 300
    CACHE_SIZE: int = 100
    LOG_DIR: str = "logs"
    LOG_FILE: str = "app.log"
    LOG_FORMAT: str = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    MAX_BYTES: int = 10000
    BACKUP_COUNT: int = 3
    
    def validate(self):
        if not self.MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY es requerida")

settings = Settings()
