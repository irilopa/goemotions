from transformers import pipeline
import torch
from ..core.config import settings

class EmotionService:
    def __init__(self):
        torch.cuda.is_available = lambda: False
        torch.set_num_threads(4)
        
        self.classifier = pipeline(
            "text-classification",
            model=settings.MODEL_NAME,
            top_k=3,
            device=-1,
            model_kwargs={
                'low_cpu_mem_usage': True,
                'max_memory': {'cpu': "2GB"}
            }
        )

    def analyze(self, text):
        return self.classifier(text)

emotion_service = EmotionService()
