from pathlib import Path

filepath = Path("agents/chief_editor.py")
content = filepath.read_text(encoding="utf-8")

# Заменяем проверку "человеческие лекарства" на более гибкую
old_check = """    # Проверяем "человеческие лекарства"
    if 'человеческ' in text_lower and 'лекарств' in text_lower:
        human_meds_index = text_lower.find('человеческ')
        context_start = max(0, human_meds_index - 100)
        context_end = min(len(text_lower), human_meds_index + 150)
        context = text_lower[context_start:context_end]
        
        warning_words = ['нельзя', 'не давайте', 'запрещено', 'токсичн', 'опасн']
        has_warning = any(w in context for w in warning_words)
        
        if not has_warning:
            issues.append("КРИТИЧЕСКАЯ ОШИБКА: Упомянуты человеческие лекарства без предупреждения!")"""

new_check = """    # Проверяем "человеческие лекарства/препараты" (гибкая проверка)
    has_human_mention = False
    human_mention_index = -1
    
    # Ищем "человеческ" рядом с "лекарств" или "препарат"
    if 'человеческ' in text_lower:
        human_idx = text_lower.find('человеческ')
        context_start = max(0, human_idx - 50)
        context_end = min(len(text_lower), human_idx + 150)
        context = text_lower[context_start:context_end]
        
        if 'лекарств' in context or 'препарат' in context:
            has_human_mention = True
            human_mention_index = human_idx
    
    if has_human_mention:
        context_start = max(0, human_mention_index - 100)
        context_end = min(len(text_lower), human_mention_index + 200)
        context = text_lower[context_start:context_end]
        
        warning_words = ['нельзя', 'не давайте', 'запрещено', 'токсичн', 'опасн', 'вредн', 'не следует']
        has_warning = any(w in context for w in warning_words)
        
        if not has_warning:
            issues.append("КРИТИЧЕСКАЯ ОШИБКА: Упомянуты человеческие лекарства/препараты без предупреждения!")"""

content = content.replace(old_check, new_check)

filepath.write_text(content, encoding="utf-8")
print("Chief Editor исправлен: проверка расширена на слово 'препараты'")
