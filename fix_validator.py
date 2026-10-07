import re
from pathlib import Path

# Читаем файл валидатора
filepath = Path("agents/validator_ai_v2.py")
content = filepath.read_text(encoding="utf-8")

# Добавляем список стоп-слов перед функцией check_keyword_density
stop_words_list = """
# Список стоп-слов (не считаются ключами)
STOP_WORDS = {'что', 'при', 'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'о', 'а', 'но', 'же', 'ли', 'бы', 'то', 'как', 'так', 'не', 'ни', 'да', 'или', 'если', 'когда', 'где', 'кто', 'что', 'какой', 'который', 'чей', 'сколько', 'почему', 'зачем', 'как', 'где', 'когда', 'почему'}

"""

# Вставляем после импортов
import_end = content.find("def load_rules():")
if import_end != -1:
    content = content[:import_end] + stop_words_list + content[import_end:]

# Заменяем функцию check_keyword_density на улучшенную версию
old_function = '''def check_keyword_density(parsed: Dict, keywords: List[str]) -> Tuple[bool, str]:
    """Legacy SEO: проверка плотности ключевых слов"""
    text_lower = parsed["text"].lower()
    total_words = parsed["words"]
    
    issues = []
    for keyword in keywords:
        keyword_lower = keyword.lower()
        count = text_lower.count(keyword_lower)
        density = (count / total_words * 100) if total_words > 0 else 0
        
        if density > MAX_KEYWORD_DENSITY:
            issues.append(f"Переспам ключа '{keyword}': {density:.2f}% (максимум {MAX_KEYWORD_DENSITY}%)")
    
    if issues:
        return False, "; ".join(issues)
    return True, "Плотность ключей в норме"'''

new_function = '''def check_keyword_density(parsed: Dict, keywords: List[str]) -> Tuple[bool, str]:
    """Legacy SEO: проверка плотности ключевых слов (с учётом стоп-слов)"""
    text_lower = parsed["text"].lower()
    total_words = parsed["words"]
    
    issues = []
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        # Пропускаем стоп-слова
        if keyword_lower in STOP_WORDS or len(keyword_lower) <= 2:
            continue
        
        count = text_lower.count(keyword_lower)
        density = (count / total_words * 100) if total_words > 0 else 0
        
        if density > MAX_KEYWORD_DENSITY:
            issues.append(f"Переспам ключа '{keyword}': {density:.2f}% (максимум {MAX_KEYWORD_DENSITY}%)")
    
    if issues:
        return False, "; ".join(issues)
    return True, "Плотность ключей в норме"'''

content = content.replace(old_function, new_function)

# Записываем обратно
filepath.write_text(content, encoding="utf-8")
print("✅ Валидатор исправлен: добавлены стоп-слова")
