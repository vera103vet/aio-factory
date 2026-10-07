from pathlib import Path

filepath = Path("agents/strategist_v2.py")
content = filepath.read_text(encoding="utf-8")

# 1. Понижаем пороги приоритета
content = content.replace(
    'HIGH_POTENTIAL_THRESHOLD = 70',
    'HIGH_POTENTIAL_THRESHOLD = 55'
)
content = content.replace(
    'MEDIUM_POTENTIAL_THRESHOLD = 50',
    'MEDIUM_POTENTIAL_THRESHOLD = 40'
)

# 2. Улучшаем анализ эмоционального потенциала (добавляем больше ключевых слов)
old_emotional = """    emotional_keywords = ['эпилепсия', 'приступ', 'судорог', 'срочно', 'экстрен', 'болезн', 'уход', 'питомец', 'собака', 'кошка']"""
new_emotional = """    emotional_keywords = ['эпилепсия', 'приступ', 'судорог', 'срочно', 'экстрен', 'болезн', 'уход', 'питомец', 'собака', 'кошка', 'перелом', 'отравлен', 'травм', 'смерт', 'опасн', 'помощь', 'спас', 'лечен', 'симптом', 'диагноз']"""
content = content.replace(old_emotional, new_emotional)

# 3. Улучшаем анализ мобильного приоритета
old_mobile = """    mobile_keywords = ['срочно', 'экстрен', 'вызов', 'телефон', 'помощь', 'симптом']"""
new_mobile = """    mobile_keywords = ['срочно', 'экстрен', 'вызов', 'телефон', 'помощь', 'симптом', 'перелом', 'отравлен', 'приступ', 'судорог', 'как помочь', 'что делать']"""
content = content.replace(old_mobile, new_mobile)

# 4. Улучшаем анализ спроса на действия
old_action = """    action_keywords = ['что делать', 'как помочь', 'первая помощь', 'алгоритм', 'чек-лист', 'инструкц']"""
new_action = """    action_keywords = ['что делать', 'как помочь', 'первая помощь', 'алгоритм', 'чек-лист', 'инструкц', 'помочь', 'лечен', 'симптом', 'признак']"""
content = content.replace(old_action, new_action)

filepath.write_text(content, encoding="utf-8")
print("✅ Strategist v2 обновлён: пороги понижены, ключевые слова расширены")
