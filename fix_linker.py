from pathlib import Path

filepath = Path("agents/linker_ai_v5.py")
content = filepath.read_text(encoding="utf-8")

# 1. Понижаем порог релевантности
content = content.replace("MIN_RELEVANCE_SCORE = 0.6", "MIN_RELEVANCE_SCORE = 0.25")

# 2. Исправляем баг в insert_links_into_html
old_insert = """def insert_links_into_html(parsed: Dict, links_to_insert: List[Dict]) -> str:
    \"\"\"Вставляет ссылки в HTML-контент\"\"\"
    soup = parsed["soup"]
    body = parsed["body"]
    
    if not body:
        return str(soup)
    
    links_inserted = 0
    
    for link_info in links_to_insert:
        if links_inserted >= MAX_LINKS_PER_PAGE:
            break
        
        anchor_text = link_info["anchor"]
        target_url = link_info["url"]
        target_topic = link_info["topic"]
        
        # Находим текст в HTML
        for element in body.find_all(string=True):
            if anchor_text.lower() in str(element).lower():
                # Создаём ссылку
                link_tag = soup.new_tag('a', href=target_url)
                link_tag.string = anchor_text
                link_tag['title'] = "Подробнее: " + target_topic
                
                # Заменяем текст на ссылку
                element.replace_with(str(element).replace(anchor_text, str(link_tag)))
                links_inserted += 1
                break
    
    return str(soup)"""

new_insert = """def insert_links_into_html(parsed: Dict, links_to_insert: List[Dict]) -> str:
    \"\"\"Вставляет ссылки в HTML-контент (безопасный метод)\"\"\"
    soup = parsed["soup"]
    body = parsed["body"]
    
    if not body:
        return str(soup)
    
    links_inserted = 0
    html_str = str(soup)
    
    for link_info in links_to_insert:
        if links_inserted >= MAX_LINKS_PER_PAGE:
            break
        
        anchor_text = link_info["anchor"]
        target_url = link_info["url"]
        target_topic = link_info["topic"]
        
        # Создаём HTML-тег ссылки
        link_html = '<a href="' + target_url + '" title="Подробнее: ' + target_topic + '">' + anchor_text + '</a>'
        
        # Заменяем первое вхождение якоря на ссылку (регистронезависимо)
        pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
        new_html, count = pattern.subn(link_html, html_str, count=1)
        
        if count > 0:
            html_str = new_html
            links_inserted += 1
            print("  Вставлена ссылка: " + anchor_text + " -> " + target_url)
    
    return html_str"""

content = content.replace(old_insert, new_insert)

filepath.write_text(content, encoding="utf-8")
print("Linker v5 исправлен: порог снижен до 0.25, баг вставки ссылок исправлен")
