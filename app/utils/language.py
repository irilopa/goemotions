def detect_language(text: str) -> str:
    """Detecta si el texto está en español o inglés."""
    spanish_words = {
        'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
        'y', 'o', 'pero', 'porque', 'como', 'qué', 'quién',
        'cuándo', 'dónde', 'cómo'
    }
    
    words = set(text.lower().split())
    spanish_count = len(words.intersection(spanish_words))
    
    return 'es' if spanish_count > 0 else 'en'
