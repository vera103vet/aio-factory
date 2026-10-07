from pathlib import Path

filepath = Path("agents/registrar_v2.py")
content = filepath.read_text(encoding="utf-8")

# Добавляем функцию тематического соответствия перед функцией add_topic
topic_matching_code = """
# --- МОДУЛЬ ТЕМАТИЧЕСКОГО СООТВЕТСТВИЯ ---

def get_site_themes(site_key: str) -> list:
    """Возвращает тематики сайта по его ключу"""
    site_themes = {
        "main": ["общая ветеринария", "терапия", "диагностика", "профилактика", "вакцинация", "осмотр", "консультация"],
        "nevrolog": ["неврология", "эпилепсия", "судороги", "нервная система", "мозг", "позвоночник", "паралич", "инсульт"],
        "usyplenie": ["усыпление", "эвтаназия", "конец жизни", "паллиативная помощь", "хронические болезни", "онкология", "неизлечимые"],
        "vetminsk": ["минск", "клиника", "хирургия", "травмы", "переломы", "операции", "скорая помощь"]
    }
    return site_themes.get(site_key, [])

def get_topic_keywords(topic_name: str) -> list:
    """Извлекает ключевые слова из названия темы"""
    topic_lower = topic_name.lower()
    
    # Словарь ключевых слов и их категорий
    keyword_categories = {
        "neurology": ["эпилепсия", "судорог", "приступ", "нервн", "мозг", "позвоночн", "паралич", "инсульт"],
        "emergency": ["перелом", "травм", "скорая", "экстрен", "срочно", "первая помощь"],
        "end_of_life": ["усыпление", "эвтаназия", "конец жизни", "паллиатив", "неизлечим", "терминальн"],
        "oncology": ["рак", "онколог", "опухоль", "злокачествен"],
        "general": ["симптом", "диагноз", "лечен", "болезн", "профилактик", "вакцин", "осмотр"],
        "nutrition": ["корм", "питан", "диет", "рацион", "еда"],
        "surgery": ["операци", "хирург", "наркоз", "шов"]
    }
    
    matched_categories = []
    for category, keywords in keyword_categories.items():
        if any(kw in topic_lower for kw in keywords):
            matched_categories.append(category)
    
    return matched_categories

def find_best_site_for_topic(topic_name: str, sites: dict) -> tuple:
    """Находит лучший сайт для темы и проверяет соответствие"""
    topic_categories = get_topic_keywords(topic_name)
    
    # Сопоставляем категории темы с тематиками сайтов
    site_scores = {}
    for site_key in sites.keys():
        site_themes = get_site_themes(site_key)
        score = 0
        
        # Проверяем совпадение категорий
        if "neurology" in topic_categories and "неврология" in " ".join(site_themes):
            score += 30
        if "emergency" in topic_categories and any(kw in " ".join(site_themes) for kw in ["скорая", "травмы", "хирургия"]):
            score += 25
        if "end_of_life" in topic_categories and any(kw in " ".join(site_themes) for kw in ["усыпление", "паллиатив"]):
            score += 30
        if "oncology" in topic_categories and any(kw in " ".join(site_themes) for kw in ["онкология", "неизлечимые"]):
            score += 25
        if "general" in topic_categories and any(kw in " ".join(site_themes) for kw in ["терапия", "диагностика", "общая"]):
            score += 20
        if "nutrition" in topic_categories and any(kw in " ".join(site_themes) for kw in ["терапия", "профилактика"]):
            score += 15
        if "surgery" in topic_categories and any(kw in " ".join(site_themes) for kw in ["хирургия", "операции"]):
            score += 25
        
        site_scores[site_key] = score
    
    # Выбираем сайт с максимальным скором
    if not site_scores or max(site_scores.values()) == 0:
        return "main", 0, "Тема не соответствует специализации ни одного сайта"
    
    best_site = max(site_scores, key=site_scores.get)
    best_score = site_scores[best_site]
    
    # Проверяем этические ограничения
    topic_lower = topic_name.lower()
    if "усыпление" in " ".join(get_site_themes(best_site)) and any(kw in topic_lower for kw in ["корм", "питание", "диета", "вакцин", "профилактик"]):
        return None, 0, "ЭТИЧЕСКОЕ ОГРАНИЧЕНИЕ: нельзя размещать темы о питании/профилактике на сайте усыпления"
    
    if best_score < 15:
        return "main", best_score, f"Низкое соответствие ({best_score}), рекомендуется main сайт"
    
    return best_site, best_score, "Соответствие подтверждено"

"""

# Вставляем код перед функцией add_topic
insert_point = content.find("def add_topic(")
if insert_point != -1:
    content = content[:insert_point] + topic_matching_code + content[insert_point:]

# Теперь модифицируем функцию add_topic, чтобы она использовала find_best_site_for_topic
old_add_signature = """def add_topic(topic_name: str, site: str, url: str = "") -> Dict:
    \"\"\"Добавляет новую тему с автоматическим обогащением метаданными\"\"\"
    topics = load_registry()"""

new_add_signature = """def add_topic(topic_name: str, site: str = None, url: str = "") -> Dict:
    \"\"\"Добавляет новую тему с автоматическим обогащением метаданными и проверкой соответствия сайта\"\"\"
    topics = load_registry()
    
    # Если сайт не указан, находим лучший автоматически
    if site is None:
        sites = load_sites()
        best_site, score, message = find_best_site_for_topic(topic_name, sites)
        if best_site is None:
            return {"error": message}
        site = best_site
        print(f"🎯 Автоматически выбран сайт: {site} (соответствие: {score})")
        print(f"   Причина: {message}")"""

content = content.replace(old_add_signature, new_add_signature)

filepath.write_text(content, encoding="utf-8")
print("✅ Registrar v2 улучшен: добавлен модуль тематического соответствия")
