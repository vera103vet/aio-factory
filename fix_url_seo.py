from pathlib import Path

filepath = Path("agents/url_seo_specialist.py")
content = filepath.read_text(encoding="utf-8")

# ИСПРАВЛЕНИЕ 1: Поиск по корню слова в категориях
old_category = """def determine_category_slug(topic_name: str) -> str:
    \"\"\"Определяет категорию для иерархического URL (/category/slug.html)\"\"\"
    topic_lower = topic_name.lower()
    if any(kw in topic_lower for kw in ['эпилепсия', 'судорог', 'приступ', 'нервн']): return 'nevrologiya'
    if any(kw in topic_lower for kw in ['корм', 'питан', 'диет', 'рацион']): return 'dietologiya'
    if any(kw in topic_lower for kw in ['перелом', 'травм', 'операци', 'хирург']): return 'khirurgiya'
    if any(kw in topic_lower for kw in ['онколог', 'рак', 'опухоль']): return 'onkologiya'
    if any(kw in topic_lower for kw in ['анализ', 'обследован', 'рентген', 'узи', 'мрт']): return 'diagnostika'
    if any(kw in topic_lower for kw in ['вязк', 'щенност', 'роды', 'плод']): return 'reproduktologiya'
    return 'obshchee'"""

new_category = """def determine_category_slug(topic_name: str) -> str:
    \"\"\"Определяет категорию для иерархического URL (/category/slug.html) — поиск по корням\"\"\"
    topic_lower = topic_name.lower()
    # Используем корни слов для надёжного определения
    if any(kw in topic_lower for kw in ['эпилепс', 'судорог', 'приступ', 'нервн', 'паралич', 'инсульт']): return 'nevrologiya'
    if any(kw in topic_lower for kw in ['корм', 'питан', 'диет', 'рацион']): return 'dietologiya'
    if any(kw in topic_lower for kw in ['перелом', 'травм', 'операци', 'хирург']): return 'khirurgiya'
    if any(kw in topic_lower for kw in ['онколог', 'рак', 'опухол', 'метастаз']): return 'onkologiya'
    if any(kw in topic_lower for kw in ['анализ', 'обследован', 'рентген', 'узи', 'мрт', 'диагност']): return 'diagnostika'
    if any(kw in topic_lower for kw in ['вязк', 'щенност', 'роды', 'плод', 'эмбрион']): return 'reproduktologiya'
    if any(kw in topic_lower for kw in ['сердц', 'карди', 'аритм']): return 'kardiologiya'
    if any(kw in topic_lower for kw in ['кож', 'зуд', 'шерст', 'аллерг', 'дермат']): return 'dermatologiya'
    if any(kw in topic_lower for kw in ['глаз', 'зрен', 'глауком']): return 'oftalmologiya'
    if any(kw in topic_lower for kw in ['зуб', 'пасть', 'десн']): return 'stomatologiya'
    if any(kw in topic_lower for kw in ['усыплен', 'эвтаназ', 'паллиатив']): return 'usyplenie'
    if any(kw in topic_lower for kw in ['вакцин', 'прививк']): return 'vakcinaciya'
    if any(kw in topic_lower for kw in ['блох', 'клещ', 'гельминт', 'паразит']): return 'parazitologiya'
    if any(kw in topic_lower for kw in ['пожил', 'сениор', 'старост']): return 'geriatriya'
    return 'obshchee'"""

content = content.replace(old_category, new_category)

# ИСПРАВЛЕНИЕ 2: Приоритизация главного ключевого слова в slug
old_slug = """def generate_smart_slug(topic_name: str, max_length: int = 60) -> str:
    \"\"\"Генерирует SEO-оптимизированный slug (ключ в начале, без мусора)\"\"\"
    keywords = extract_keywords(topic_name)
    if not keywords:
        return "info"
    
    # Первичное ключевое слово всегда идёт первым
    primary_keyword = keywords[0]
    slug_parts = [primary_keyword]
    current_length = len(primary_keyword)
    
    # Добавляем остальные ключи, пока не достигнем лимита
    for keyword in keywords[1:]:
        new_length = current_length + 1 + len(keyword)
        if new_length <= max_length:
            slug_parts.append(keyword)
            current_length = new_length
        else:
            break
    
    slug = '-'.join(slug_parts)
    slug_translit = transliterate(slug)
    
    # Очистка от множественных дефисов и обрезка
    slug_translit = re.sub(r'-+', '-', slug_translit)
    return slug_translit.strip('-')[:max_length]"""

new_slug = """# Тематические ключевые слова (имеют приоритет в начале slug)
TOPIC_PRIORITY_KEYWORDS = {
    'nevrologiya': ['эпилепс', 'судорог', 'приступ', 'нервн', 'паралич'],
    'dietologiya': ['корм', 'питан', 'диет', 'рацион'],
    'khirurgiya': ['перелом', 'травм', 'операци', 'хирург', 'рана'],
    'onkologiya': ['онколог', 'рак', 'опухол', 'метастаз'],
    'kardiologiya': ['сердц', 'карди', 'аритм'],
    'diagnostika': ['анализ', 'обследован', 'рентген', 'узи', 'мрт', 'диагност'],
    'reproduktologiya': ['вязк', 'щенност', 'роды', 'плод'],
    'dermatologiya': ['кож', 'зуд', 'шерст', 'аллерг', 'дермат'],
    'oftalmologiya': ['глаз', 'зрен', 'глауком'],
    'stomatologiya': ['зуб', 'пасть', 'десн'],
    'usyplenie': ['усыплен', 'эвтаназ', 'паллиатив'],
    'vakcinaciya': ['вакцин', 'прививк'],
    'parazitologiya': ['блох', 'клещ', 'гельминт', 'паразит'],
    'geriatriya': ['пожил', 'сениор', 'старост']
}

def find_primary_keyword(topic_name: str, category: str) -> str:
    \"\"\"Находит главное тематическое ключевое слово для slug\"\"\"
    topic_lower = topic_name.lower()
    priority_keywords = TOPIC_PRIORITY_KEYWORDS.get(category, [])
    
    # Ищем тематическое ключевое слово в названии
    for kw in priority_keywords:
        if kw in topic_lower:
            # Возвращаем полное слово из названия
            for word in re.findall(r'[а-яёa-z0-9]+', topic_lower):
                if kw in word and len(word) > 3:
                    return word
    return None

def generate_smart_slug(topic_name: str, max_length: int = 60) -> str:
    \"\"\"Генерирует SEO-оптимизированный slug (главное ключевое слово в начале)\"\"\"
    category = determine_category_slug(topic_name)
    keywords = extract_keywords(topic_name)
    if not keywords:
        return "info"
    
    # Находим главное тематическое ключевое слово
    primary = find_primary_keyword(topic_name, category)
    
    if primary and primary in keywords:
        # Главное слово идёт первым, остальные — после
        keywords.remove(primary)
        slug_parts = [primary] + keywords
    else:
        slug_parts = keywords
    
    # Собираем slug до достижения лимита
    final_parts = [slug_parts[0]]
    current_length = len(slug_parts[0])
    
    for keyword in slug_parts[1:]:
        new_length = current_length + 1 + len(keyword)
        if new_length <= max_length:
            final_parts.append(keyword)
            current_length = new_length
        else:
            break
    
    slug = '-'.join(final_parts)
    slug_translit = transliterate(slug)
    slug_translit = re.sub(r'-+', '-', slug_translit)
    return slug_translit.strip('-')[:max_length]"""

content = content.replace(old_slug, new_slug)

filepath.write_text(content, encoding="utf-8")
print("URL SEO Specialist исправлен: поиск по корням + приоритизация главного ключа")
