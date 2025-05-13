from functools import lru_cache
import requests
from ..core.config import settings

class TranslationService:
    @lru_cache(maxsize=settings.CACHE_SIZE)
    def translate(self, text, source_lang, target_lang):
        if source_lang == target_lang:
            return text
            
        prompt = f"Traduce el siguiente texto de {source_lang} a {target_lang}. Solo devuelve la traducción sin explicaciones:\n\n{text}"
        
        headers = {
            "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
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
        except Exception:
            return text

translation_service = TranslationService()
