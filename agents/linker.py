import json
import yaml
import re
from pathlib import Path

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def load_registry():
    with open(REGISTRY, "r", encoding="utf-8") as f:
        return json.load(f)

def find_natural_anchor_positions(text, keywords):
    """Находит естественные места для вставки ссылок"""
    positions = []
    text_lower = text.lower()
    
    for keyword in keywords:
        # Ищем вхождения ключевых слов
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        for match in re.finditer(pattern, text_lower):
            start = match.start()
            # Проверяем, что это не часть HTML-тега
            if start > 0 and text[start-1] not in ['<', '/']:
                positions.append({
                    "keyword": keyword,
                    "position": start,
                    "context": text[max(0, start-20):start+len(keyword)+20]
                })
    
    return positions

def generate_internal_links(text, source_site, sites, registry):
    """Генерирует внутренние ссылки по правилам экосистемы"""
    
    source_config = sites.get(source_site)
    if not source_config:
        return {"error": f"Сайт {source_site} не найден в реестре"}
    
    # Определяем, на какие сайты можно ссылаться
    allowed_targets = source_config.get("internal_linking_to", [])
    
    if not allowed_targets:
        return {"message": "Нет разрешённых целей для перелинковки", "links": []}
    
    # Собираем ключевые слова из реестра для целевых сайтов
    link_candidates = []
    for topic in registry:
        target = topic["target_site"]
        if target in allowed_targets:
            link_candidates.append({
                "keyword": topic["primary_keyword"],
                "topic": topic["topic"],
                "url": topic["url"],
                "target_site": target
            })
    
    # Находим естественные позиции для ссылок
    positions = find_natural_anchor_positions(text, [c["keyword"] for c in link_candidates])
    
    # Лимит: не более 5 ссылок на текст
    max_links = 5
    selected_links = []
    
    for pos in positions[:max_links]:
        for candidate in link_candidates:
            if candidate["keyword"].lower() in pos["keyword"].lower():
                selected_links.append({
                    "anchor": pos["keyword"],
                    "url": candidate["url"],
                    "title": candidate["topic"],
                    "position": pos["position"]
                })
                break
    
    # Генерируем HTML со ссылками
    linked_text = text
    offset = 0
    for link in sorted(selected_links, key=lambda x: x["position"]):
        pos = link["position"] + offset
        anchor = link["anchor"]
        url = link["url"]
        title = link["title"]
        
        link_html = f'<a href="{url}" title="{title}">{anchor}</a>'
        linked_text = linked_text[:pos] + link_html + linked_text[pos+len(anchor):]
        offset += len(link_html) - len(anchor)
    
    return {
        "source_site": source_site,
        "allowed_targets": allowed_targets,
        "links_added": len(selected_links),
        "links": selected_links,
        "linked_text": linked_text
    }

if __name__ == "__main__":
    print("="*70)
    print("АГЕНТ-ЛИНКЕР: УМНАЯ ПЕРЕЛИНКОВКА ЭКОСИСТЕМЫ")
    print("="*70)
    
    sites = load_sites()
    registry = load_registry()
    
    print(f"\nЗагружено сайтов: {len(sites)}")
    print(f"Загружено тем в реестре: {len(registry)}")
    
    # Тестовый текст
    test_text = """
    Хроническая болезнь почек у кошек требует особого внимания. 
    Диета при хронической болезни почек у кошек должна быть низкобелковой.
    Если у вашей кошки хроническая болезнь почек, диета и уход играют решающую роль.
    Всегда консультируйтесь с ветеринаром.
    """
    
    print("\n" + "="*70)
    print("ТЕСТ: Генерация ссылок для сайта 'vetminsk'")
    print("="*70)
    
    result = generate_internal_links(test_text, "vetminsk", sites, registry)
    
    print(f"\nИсточник: {result['source_site']}")
    print(f"Разрешённые цели: {result['allowed_targets']}")
    print(f"Добавлено ссылок: {result['links_added']}")
    
    if result['links']:
        print("\nСгенерированные ссылки:")
        for link in result['links']:
            print(f"  - Анкор: '{link['anchor']}'")
            print(f"    URL: {link['url']}")
            print(f"    Заголовок: {link['title']}\n")
    
    print("\nТекст со ссылками:")
    print(result['linked_text'])
