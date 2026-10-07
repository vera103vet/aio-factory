from pathlib import Path

filepath = Path("agents/domain_expert_critic.py")
content = filepath.read_text(encoding="utf-8")

# Заменяем проверку нюансов на более гибкую
old_check = """def check_expert_nuances(text_lower: str, rules: Dict) -> Tuple[bool, List[str]]:
    missing = []
    for nuance in rules.get("mandatory_expert_nuances", []):
        keywords = nuance.split()[:2]
        if not any(kw in text_lower for kw in keywords):
            missing.append("Отсутствует экспертный нюанс: '" + nuance + "'")
    return len(missing) == 0, missing"""

new_check = """def check_expert_nuances(text_lower: str, rules: Dict) -> Tuple[bool, List[str]]:
    missing = []
    for nuance in rules.get("mandatory_expert_nuances", []):
        # Берём все значимые слова (длиной > 3 символов)
        all_words = [w for w in nuance.split() if len(w) > 3]
        # Нюанс считается найденным, если в тексте есть хотя бы 2 значимых слова из него
        found_count = sum(1 for w in all_words if w in text_lower)
        if found_count < 2:
            missing.append("Отсутствует экспертный нюанс: '" + nuance + "'")
    return len(missing) == 0, missing"""

content = content.replace(old_check, new_check)

filepath.write_text(content, encoding="utf-8")
print("Поиск нюансов улучшен: теперь ищет хотя бы 2 значимых слова из нюанса")
