from pathlib import Path

filepath = Path("agents/domain_expert_critic.py")
content = filepath.read_text(encoding="utf-8")

# Заменяем функцию determine_category на улучшенную
old_func = """def determine_category(topic_name: str, text: str = "") -> str:
    combined = (topic_name + " " + text).lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        scores[category] = score
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'terapiya'"""

new_func = """def determine_category(topic_name: str, text: str = "") -> str:
    combined = (topic_name + " " + text).lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in combined:
                # Усиленный вес для точных совпадений в названии темы
                if kw in topic_name.lower():
                    score += 3
                else:
                    score += 1
        scores[category] = score
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'terapiya'"""

content = content.replace(old_func, new_func)

filepath.write_text(content, encoding="utf-8")
print("Категоризация улучшена: точные совпадения в названии темы получают вес x3")
