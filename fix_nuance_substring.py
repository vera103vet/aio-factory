from pathlib import Path

filepath = Path("agents/domain_expert_critic.py")
content = filepath.read_text(encoding="utf-8")

# Заменяем функцию check_expert_nuances на версию с поиском по подстроке
old_func = """def check_expert_nuances(text_lower: str, rules: Dict) -> Tuple[bool, List[str]]:
    missing = []
    for nuance in rules.get("mandatory_expert_nuances", []):
        all_words = [w for w in nuance.split() if len(w) > 3]
        found_count = sum(1 for w in all_words if w in text_lower)
        if found_count < 2:
            missing.append("Отсутствует нюанс: '" + nuance + "'")
    return len(missing) == 0, missing"""

new_func = """def check_expert_nuances(text_lower: str, rules: Dict) -> Tuple[bool, List[str]]:
    missing = []
    for nuance in rules.get("mandatory_expert_nuances", []):
        all_words = [w for w in nuance.split() if len(w) > 4]
        found_count = 0
        for w in all_words:
            # Проверяем точное совпадение ИЛИ подстроку (для разных форм слов)
            if w in text_lower:
                found_count += 1
            else:
                # Проверяем, есть ли корень слова в тексте (первые 6 символов)
                root = w[:6] if len(w) > 6 else w
                if any(root in word for word in text_lower.split()):
                    found_count += 1
        if found_count < 2:
            missing.append("Отсутствует нюанс: '" + nuance + "'")
    return len(missing) == 0, missing"""

content = content.replace(old_func, new_func)

filepath.write_text(content, encoding="utf-8")
print("Поиск нюансов улучшен: теперь ищет по корням слов (дезориентация/дезориентирована)")
