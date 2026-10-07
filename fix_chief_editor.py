from pathlib import Path

filepath = Path("agents/chief_editor.py")
content = filepath.read_text(encoding="utf-8")

# Заменяем функцию check_sanity на улучшенную версию
old_sanity = """def check_sanity(parsed: Dict) -> Tuple[bool, str, List[str]]:
    text_lower = parsed["text"].lower()
    issues = []
    
    dangerous_advice = [
        (r'дайте.*парацетамол', 'Парацетамол токсичен для животных!'),
        (r'дайте.*аспирин', 'Аспирин опасен для животных!'),
        (r'дайте.*ибупрофен', 'Ибупрофен токсичен для животных!'),
        (r'человеческ.*лекарств', 'Нельзя давать человеческие лекарства без назначения врача!')
    ]
    
    for pattern, message in dangerous_advice:
        if re.search(pattern, text_lower):
            issues.append("КРИТИЧЕСКАЯ ОШИБКА: " + message)
    
    has_disclaimer = bool(re.search(r'(не\s+заменяет|требуется\s+консультаци|обратитесь\s+к\s+(ветеринар|врач))', text_lower))
    if not has_disclaimer:
        issues.append("Отсутствует обязательный медицинский дисклеймер")
    
    if issues:
        return False, "Найдены критические проблемы безопасности", issues
    return True, "Логическая и ветеринарная вменяемость подтверждена", []"""

new_sanity = """def check_sanity(parsed: Dict) -> Tuple[bool, str, List[str]]:
    text_lower = parsed["text"].lower()
    issues = []
    
    # Опасные лекарства
    dangerous_drugs = ['парацетамол', 'аспирин', 'ибупрофен']
    
    # Проверяем каждое опасное лекарство
    for drug in dangerous_drugs:
        if drug in text_lower:
            # Ищем контекст вокруг упоминания
            drug_index = text_lower.find(drug)
            context_start = max(0, drug_index - 100)
            context_end = min(len(text_lower), drug_index + 100)
            context = text_lower[context_start:context_end]
            
            # Проверяем, есть ли слова предупреждения в контексте
            warning_words = ['токсичен', 'токсичны', 'опасен', 'опасны', 'нельзя', 'не давайте', 'запрещено', 'вреден']
            has_warning = any(w in context for w in warning_words)
            
            # Если нет предупреждения — это ошибка
            if not has_warning:
                issues.append("КРИТИЧЕСКАЯ ОШИБКА: Упомянут " + drug + " без предупреждения о токсичности!")
    
    # Проверяем "человеческие лекарства"
    if 'человеческ' in text_lower and 'лекарств' in text_lower:
        human_meds_index = text_lower.find('человеческ')
        context_start = max(0, human_meds_index - 100)
        context_end = min(len(text_lower), human_meds_index + 150)
        context = text_lower[context_start:context_end]
        
        warning_words = ['нельзя', 'не давайте', 'запрещено', 'токсичн', 'опасн']
        has_warning = any(w in context for w in warning_words)
        
        if not has_warning:
            issues.append("КРИТИЧЕСКАЯ ОШИБКА: Упомянуты человеческие лекарства без предупреждения!")
    
    # Проверяем наличие дисклеймера
    has_disclaimer = bool(re.search(r'(не\s+заменяет|требуется\s+консультаци|обратитесь\s+к\s+(ветеринар|врач))', text_lower))
    if not has_disclaimer:
        issues.append("Отсутствует обязательный медицинский дисклеймер")
    
    if issues:
        return False, "Найдены критические проблемы безопасности", issues
    return True, "Логическая и ветеринарная вменяемость подтверждена", []"""

content = content.replace(old_sanity, new_sanity)

filepath.write_text(content, encoding="utf-8")
print("Chief Editor исправлен: добавлена проверка контекста для ложных срабатываний")
