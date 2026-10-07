from pathlib import Path

filepath = Path("agents/validator_ai_v2.py")
lines = filepath.read_text(encoding="utf-8").split('\n')

new_lines = []
skip_until_next_def = False

for line in lines:
    # Когда находим начало функции check_actionability — пропускаем старую версию
    if 'def check_actionability(' in line:
        skip_until_next_def = True
        # Вставляем новую версию функции
        new_lines.append('def check_actionability(parsed: Dict) -> Tuple[bool, str]:')
        new_lines.append('    """Actionability (v14): деревья решений, чек-листы"""')
        new_lines.append('    text_lower = parsed["text"].lower()')
        new_lines.append('    issues = []')
        new_lines.append('    ')
        new_lines.append('    # Дерево решений (улучшенная проверка: "если" и "то" в одном предложении)')
        new_lines.append("    sentences = re.split(r'[.!?]+', text_lower)")
        new_lines.append('    has_decision_tree = False')
        new_lines.append('    for sentence in sentences:')
        new_lines.append("        if 'если' in sentence and ('то' in sentence or 'тогда' in sentence):")
        new_lines.append('            has_decision_tree = True')
        new_lines.append('            break')
        new_lines.append('    ')
        new_lines.append("    if not has_decision_tree:")
        new_lines.append("        issues.append(\"Нет дерева решений 'Если... то...'\")")
        new_lines.append('    ')
        new_lines.append('    # Чек-лист')
        new_lines.append("    has_checklist = bool(re.search(r'(чек-лист|список|перечень)', text_lower))")
        new_lines.append('    if not has_checklist:')
        new_lines.append('        issues.append("Нет чек-листа действий")')
        new_lines.append('    ')
        new_lines.append('    if issues:')
        new_lines.append('        return False, "; ".join(issues)')
        new_lines.append('    return True, "Практическая применимость на уровне"')
        continue
    
    # Пропускаем строки старой функции до следующей def или конца отступа
    if skip_until_next_def:
        if line.startswith('def ') or (line.strip() and not line.startswith(' ') and not line.startswith('\t')):
            skip_until_next_def = False
            new_lines.append(line)
        elif line.strip() == '' or line.startswith('    '):
            continue  # пропускаем
        else:
            skip_until_next_def = False
            new_lines.append(line)
    else:
        new_lines.append(line)

filepath.write_text('\n'.join(new_lines), encoding="utf-8")
print("✅ Функция check_actionability заменена на улучшенную версию")
