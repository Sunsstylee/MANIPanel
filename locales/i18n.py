import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_LOCALES_CACHE = {}

def load_locale(lang):
    # Если язык уже загружен в память — отдаем из кэша
    if lang in _LOCALES_CACHE:
        return _LOCALES_CACHE[lang]
        
    file_path = os.path.join(BASE_DIR, f"{lang}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            _LOCALES_CACHE[lang] = json.load(f)
            return _LOCALES_CACHE[lang]
    return {}

def t(key, lang="ru"):
    # 1. Проверяем выбранный язык
    lang_data = load_locale(lang)
    if key in lang_data:
        return lang_data[key]
    
    # 2. Если нет — fallback на русский
    if lang != "ru":
        ru_data = load_locale("ru")
        if key in ru_data:
            return ru_data[key]
            
    # 3. Если и там нет — отдаем сам ключ
    return key