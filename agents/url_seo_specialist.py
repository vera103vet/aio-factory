import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

REGISTRY_FILE = Path("data/topic_registry.json")
SITES_FILE = Path("config/sites.yaml")

# Стоп-слова для URL
STOP_WORDS = {
    'что', 'как', 'при', 'первый', 'первые', 'признак', 'признаки',
    'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'о',
    'а', 'но', 'же', 'ли', 'бы', 'то', 'так', 'не', 'ни', 'да', 'или',
    'если', 'когда', 'где', 'кто', 'который', 'эта', 'этот', 'эти',
    'делать', 'выбрать', 'помочь', 'помощь', 'является', 'можно'
}

# Карта транслитерации
TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya', ' ': '-'
}

# Категории по ключевым словам (поиск по корням)
CATEGORY_KEYWORDS = {
    'nevrologiya': ['эпилепс', 'судорог', 'приступ', 'нервн', 'паралич', 'инсульт'],
    'dietologiya': ['корм', 'питан', 'диет', 'рацион'],
    'khirurgiya': ['перелом', 'травм', 'операци', 'хирург'],
    'kardiologiya': ['сердц', 'карди', 'аритм'],
    'onkologiya': ['онколог', 'рак', 'опухол', 'метастаз'],
    'dermatologiya': ['кож', 'зуд', 'шерст', 'аллерг', 'дермат'],
    'oftalmologiya': ['глаз', 'зрен', 'глауком'],
    'stomatologiya': ['зуб', 'пасть', 'десн'],
    'ginekologiya': ['течк', 'вязк', 'роды', 'беремен', 'стерилизац', 'пиометр'],
    'reproduktologiya': ['размножен', 'щенност', 'плод', 'эмбрион'],
    'diagnostika': ['диагност', 'анализ', 'обследован', 'рентген', 'узи', 'мрт', 'биохим', 'тест'],
    'usyplenie': ['усыплен', 'эвтаназ', 'прощан', 'паллиатив'],
    'vakcinaciya': ['вакцин', 'прививк'],
    'parazitologiya': ['блох', 'клещ', 'гельминт', 'глист', 'паразит'],
    'geriatriya': ['пожил', 'сениор', 'старост'],
    'exotic': ['кролик', 'попугай', 'хомяк', 'черепах', 'экзот']
}

# Определение типа контента по маркерам в названии
CONTENT_TYPE_MARKERS = {
    'how-to': ['как', 'что делать', 'первая помощь', 'помочь', 'инструкц'],
    'guide': ['руководств', 'полный гид', 'всё о', 'гайд'],
    'vs': ['vs', 'против', 'сравнен', 'отличия', 'разница'],
    'review': ['обзор', 'рейтинг', 'топ', 'лучший', 'тест'],
    'faq': ['вопрос', 'ответ', 'faq', 'часто задаваем'],
    'article': []  # Дефолтный тип для обычных статей
}

def detect_content_type(topic_name: str) -> str:
    """Определяет тип контента по маркерам в названии"""
    topic_lower = topic_name.lower()
    for content_type, markers in CONTENT_TYPE_MARKERS.items():
        if any(marker in topic_lower for marker in markers):
            return content_type
    return 'article'

def transliterate(text: str) -> str:
    """Транслитерирует кириллицу в латиницу"""
    result = []
    for char in text.lower():
        if char in TRANSLIT_MAP:
            result.append(TRANSLIT_MAP[char])
        elif char.isascii() and (char.isalnum() or char == '-'):
            result.append(char)
    return ''.join(result)

def extract_keywords(topic_name: str) -> List[str]:
    """Извлекает ключевые слова"""
    words = re.findall(r'[а-яёa-z0-9]+', topic_name.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]

def find_primary_keyword(topic_name: str, category: str) -> str:
    """Находит главное тематическое ключевое слово"""
    topic_lower = topic_name.lower()
    priority_keywords = CATEGORY_KEYWORDS.get(category, [])
    
    for kw in priority_keywords:
        if kw in topic_lower:
            for word in re.findall(r'[а-яёa-z0-9]+', topic_lower):
                if kw in word and len(word) > 3:
                    return word
    return None

def generate_cyrillic_slug(topic_name: str, category: str, max_length: int = 60) -> str:
    """Генерирует кириллический slug"""
    keywords = extract_keywords(topic_name)
    if not keywords:
        return "статья"
    
    primary = find_primary_keyword(topic_name, category)
    
    if primary and primary in keywords:
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
    
    return '-'.join(final_parts)

def generate_translit_slug(cyrillic_slug: str) -> str:
    """Генерирует транслитерированную версию slug"""
    translit = transliterate(cyrillic_slug)
    translit = re.sub(r'-+', '-', translit)
    return translit.strip('-')[:60]

def determine_category(topic_name: str) -> str:
    """Определяет категорию по корням слов"""
    topic_lower = topic_name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in topic_lower for kw in keywords):
            return category
    return 'obshchee'

def build_url_structure(
    category: str, 
    cyrillic_slug: str, 
    translit_slug: str,
    content_type: str,
    geo: Optional[str] = None
) -> Dict:
    """Строит полную структуру URL с обеими версиями"""
    
    # Кириллический URL (основной для рунета)
    cyrillic_parts = []
    if geo:
        cyrillic_parts.append(geo)
    if content_type != 'article':
        cyrillic_parts.append(content_type)
    cyrillic_parts.append(category)
    cyrillic_parts.append(cyrillic_slug)
    
    cyrillic_url = '/' + '/'.join(cyrillic_parts) + '/'
    
    # Транслитерированный URL (резервный)
    translit_parts = []
    if geo:
        translit_parts.append(transliterate(geo))
    if content_type != 'article':
        translit_parts.append(content_type)
    translit_parts.append(category)
    translit_parts.append(translit_slug)
    
    translit_url = '/' + '/'.join(translit_parts) + '/'
    
    # Canonical URL (всегда кириллический для рунета)
    canonical_url = cyrillic_url
    
    return {
        "cyrillic_url": cyrillic_url,
        "translit_url": translit_url,
        "canonical_url": canonical_url,
        "content_type": content_type,
        "category": category,
        "has_geo": geo is not None
    }

def validate_url_structure(url_data: Dict) -> Dict:
    """Проверяет URL по современным правилам SEO"""
    cyrillic = url_data["cyrillic_url"]
    translit = url_data["translit_url"]
    
    checks = {
        # Проверка кириллического URL
        "cyrillic_length_ok": len(cyrillic) <= 100,
        "cyrillic_no_extension": not cyrillic.endswith('.html'),
        "cyrillic_trailing_slash": cyrillic.endswith('/'),
        "cyrillic_has_category": '/' in cyrillic and len(cyrillic.split('/')) > 2,
        
        # Проверка транслитерированного URL
        "translit_length_ok": len(translit) <= 100,
        "translit_lowercase": translit == translit.lower(),
        "translit_no_special_chars": not re.search(r'[?&%#$@!]', translit),
        "translit_hyphens_not_underscores": '_' not in translit,
        
        # Проверка canonical
        "canonical_matches_cyrillic": url_data["canonical_url"] == cyrillic,
        
        # Итоговая валидация
        "is_valid": all([
            len(cyrillic) <= 100,
            not cyrillic.endswith('.html'),
            cyrillic.endswith('/'),
            len(translit) <= 100,
            translit == translit.lower()
        ])
    }
    
    return checks

def process_registry(geo: Optional[str] = None):
    """Главная функция: обрабатывает все темы в реестре"""
    print("="*70)
    print("URL SEO SPECIALIST v2.0: СОВРЕМЕННАЯ ОПТИМИЗАЦИЯ URL")
    print("="*70)
    print("Дата: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    if geo:
        print("Локальное SEO: " + geo)
    
    topics = load_registry()
    if not topics:
        print("Реестр тем пуст.")
        return
    
    updated_count = 0
    print(f"Найдено тем для обработки: {len(topics)}\n")
    
    for topic in topics:
        topic_name = topic.get("name", "")
        if not topic_name:
            continue
        
        # Определяем параметры
        category = determine_category(topic_name)
        content_type = detect_content_type(topic_name)
        
        # Генерируем slug'и
        cyrillic_slug = generate_cyrillic_slug(topic_name, category)
        translit_slug = generate_translit_slug(cyrillic_slug)
        
        # Строим структуру URL
        url_data = build_url_structure(
            category, 
            cyrillic_slug, 
            translit_slug,
            content_type,
            geo
        )
        
        # Валидация
        validation = validate_url_structure(url_data)
        
        # Обновляем тему в реестре
        if topic.get("url_data") != url_data:
            topic["url_data"] = url_data
            topic["url_validation"] = validation
            topic["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            updated_count += 1
            
            status = "✅" if validation["is_valid"] else "⚠️"
            print(f"{status} Тема: {topic_name[:50]}...")
            print(f"   Тип: {content_type} | Категория: {category}")
            print(f"   Кириллица: {url_data['cyrillic_url']}")
            print(f"   Транслит: {url_data['translit_url']}")
            print(f"   Canonical: {url_data['canonical_url']}")
            print()
    
    if updated_count > 0:
        save_registry(topics)
        print(f"🎉 Успешно обновлено URL для {updated_count} тем.")
        print("Реестр сохранён: data/topic_registry.json")
    else:
        print("Все URL уже оптимизированы и актуальны.")
    
    print("="*70)

def load_registry():
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("topics", []) if isinstance(data, dict) else data
    return []

def save_registry(topics):
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump({"topics": topics}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # Можно передать город как аргумент для локального SEO
    # Пример: python url_seo_specialist.py --geo=минск
    import sys
    geo = None
    if '--geo=' in sys.argv:
        for arg in sys.argv:
            if arg.startswith('--geo='):
                geo = arg.split('=')[1].lower()
                break
    
    process_registry(geo)
