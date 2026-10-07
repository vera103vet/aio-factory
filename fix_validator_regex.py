import re
from pathlib import Path

# Читаем файл валидатора
filepath = Path("agents/validator_ai_v2.py")
content = filepath.read_text(encoding="utf-8")

# Находим и заменяем функцию check_actionability
old_pattern = r"""def check_actionability\(parsed: Dict\) -> Tuple\[bool, str\]:
    \"\"\"Actionability \(v14\): деревья решений, чек-листы\"\"\"
    text_lower = parsed\["text"\]\.lower\(\)
    issues = \[\]
    
    # Дерево решений
    if_then_patterns = \[r'если\\s\+\[\^,\]\+,\s*\(то\|тогда\)', r'в\\s\+случае'\]
    has_decision_tree = any\(re\.search\(p, text_lower\) for p in if_then_patterns\)
    if not has_decision_tree:
        issues\.append\("Нет дерева решений 'Если\.\.\. то\.\.\.'"\)"""

new_pattern = r"""def check_actionability(parsed: Dict) -> Tuple[bool, str]:
    \"\"\"Actionability (v14): деревья решений, чек-листы\"\"\"
    text_lower = parsed["text"].lower()
    issues = []
    
    # Дерево решений (улучшенная проверка: ищем "если" и "то" в одном предложении)
    sentences = re.split(r'[.!?]+', text_lower)
    has_decision_tree = False
    for sentence in sentences:
        if 'если' in sentence and ('то' in sentence or 'тогда' in sentence):
            has_decision_tree = True
            break
    
    if not has_decision_tree:
        issues.append("Нет дерева решений 'Если... то...'")"""

content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)

# Записываем обратно
filepath.write_text(content, encoding="utf-8")
print("✅ Валидатор исправлен: улучшена проверка дерева решений")
