import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_LOCALES_CACHE = {}

def load_locale(lang):
    if lang in _LOCALES_CACHE:
        return _LOCALES_CACHE[lang]
        
    file_path = os.path.join(BASE_DIR, f"{lang}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _LOCALES_CACHE[lang] = data
                return data
        except Exception as e:
            print(f"[i18n ERROR] Ошибка синтаксиса в {lang}.json: {e}")
            return {}
    return {}

def t(key, lang="ru"):
    lang_data = load_locale(lang)
    if key in lang_data:
        return lang_data[key]
    
    if lang != "ru":
        ru_data = load_locale("ru")
        if key in ru_data:
            return ru_data[key]
            
    return key