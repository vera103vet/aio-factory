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

def find_smart_anchors(text, topic, keyword):
    """Находит умные анкоры: от точных до фрагментарных"""
    
    text_lower = text.lower()
    topic_lower = topic.lower()
    keyword_lower = keyword.lower()
    
    anchors = []
    
    # Приоритет 1: Точное вхождение ключевого слова
    pattern = r'\b' + re.escape(keyword_lower) + r'\b'
    for match in re.finditer(pattern, text_lower):
        pos = match.start()
        if pos > 0 and text[pos-1] not in ['<', '/']:
            anchors.append({
                "text": keyword,
                "position": pos,
                "length": len(keyword),
                "type": "exact",
                "priority": 1
            })
    
    # Приоритет 2: Вхождение темы целиком
    pattern = r'\b' + re.escape(topic_lower) + r'\b'
    for match in re.finditer(pattern, text_lower):
        pos = match.start()
        if pos > 0 and text[pos-1] not in ['<', '/']:
            anchors.append({
                "text": topic,
                "position": pos,
                "length": len(topic),
                "type": "full_topic",
                "priority": 2
            })
    
    # Приоритет 3: Фрагменты ключа (3 слова подряд из ключа)
    keyword_words = keyword_lower.split()
    if len(keyword_words) >= 3:
        for i in range(len(keyword_words) - 2):
            fragment = ' '.join(keyword_words[i:i+3])
            pattern = r'\b' + re.escape(fragment) + r'\b'
            for match in re.finditer(pattern, text_lower):
                pos = match.start()
                if pos > 0 and text[pos-1] not in ['<', '/']:
                    anchors.append({
                        "text": fragment,
                        "position": pos,
                        "length": len(fragment),
                        "type": "3_word_fragment",
                        "priority": 3
                    })
    
    # Приоритет 4: Фрагменты ключа (2 слова подряд из ключа)
    if len(keyword_words) >= 2:
        for i in range(len(keyword_words) - 1):
            fragment = ' '.join(keyword_words[i:i+2])
            # Пропускаем слишком короткие фрагменты
            if len(fragment) < 8:
                continue
            pattern = r'\b' + re.escape(fragment) + r'\b'
            for match in re.finditer(pattern, text_lower):
                pos = match.start()
                if pos > 0 and text[pos-1] not in ['<', '/']:
                    anchors.append({
                        "text": fragment,
                        "position": pos,
                        "length": len(fragment),
                        "type": "2_word_fragment",
                        "priority": 4
                    })
    
    return anchors

def generate_smart_links(text, source_site, sites, registry):
    """Генерирует умные внутренние ссылки с естественными анкорами"""
    
    source_config = sites.get(source_site)
    if not source_config:
        return {"error": f"Сайт {source_site} не найден в реестре"}
    
    allowed_targets = source_config.get("internal_linking_to", [])
    
    if not allowed_targets:
        return {"message": "Нет разрешённых целей для перелинковки", "links": []}
    
    all_anchors = []
    
    for topic in registry:
        target = topic["target_site"]
        
        if target not in allowed_targets:
            continue
        
        anchors = find_smart_anchors(text, topic["topic"], topic["primary_keyword"])
        
        for anchor in anchors:
            all_anchors.append({
                "anchor": anchor["text"],
                "url": topic["url"],
                "title": topic["topic"],
                "position": anchor["position"],
                "length": anchor["length"],
                "target_site": target,
                "anchor_type": anchor["type"],
                "priority": anchor["priority"]
            })
    
    # Удаляем перекрывающиеся анкоры (оставляем самый длинный и приоритетный)
    all_anchors.sort(key=lambda x: (x["priority"], -x["length"], x["position"]))
    
    selected_links = []
    used_ranges = []
    
    for anchor in all_anchors:
        pos = anchor["position"]
        length = anchor["length"]
        end = pos + length
        
        # Проверяем, не перекрывается ли с уже выбранными
        overlap = False
        for used_start, used_end in used_ranges:
            if pos < used_end and end > used_start:
                overlap = True
                break
        
        if not overlap:
            selected_links.append(anchor)
            used_ranges.append((pos, end))
        
        if len(selected_links) >= 5:
            break
    
    # Сортируем по позиции для корректной замены
    selected_links.sort(key=lambda x: x["position"])
    
    # Генерируем HTML со ссылками
    linked_text = text
    offset = 0
    
    for link in selected_links:
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
    print("АГЕНТ-ЛИНКЕР v4: ПОИСК ФРАГМЕНТОВ КЛЮЧА")
    print("="*70)
    
    sites = load_sites()
    registry = load_registry()
    
    print(f"\nЗагружено сайтов: {len(sites)}")
    print(f"Загружено тем в реестре: {len(registry)}")
    
    test_text = """
    Хроническая болезнь почек у кошек требует особого внимания. 
    Диета при хронической болезни почек у кошек должна быть низкобелковой.
    Если у вашей кошки хроническая болезнь почек, диета и уход играют решающую роль.
    Всегда консультируйтесь с ветеринаром.
    """
    
    print("\n" + "="*70)
    print("ТЕСТ: Умная перелинковка для сайта 'main'")
    print("="*70)
    
    result = generate_smart_links(test_text, "main", sites, registry)
    
    print(f"\nИсточник: {result['source_site']}")
    print(f"Разрешённые цели: {result['allowed_targets']}")
    print(f"Добавлено ссылок: {result['links_added']}")
    
    if result['links']:
        print("\nСгенерированные ссылки:")
        for link in result['links']:
            print(f"  - Анкор: '{link['anchor']}' (тип: {link['anchor_type']})")
            print(f"    URL: {link['url']}")
            print(f"    Заголовок: {link['title']}\n")
    
    print("\nТекст со ссылками:")
    print(result['linked_text'])
