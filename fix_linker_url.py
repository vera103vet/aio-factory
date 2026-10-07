from pathlib import Path

filepath = Path("agents/linker_ai_v5.py")
content = filepath.read_text(encoding="utf-8")

# Заменяем URL-encoded генерацию на транслитерацию
old_url_func = """def generate_topic_url(topic_name: str, site_key: str, sites: dict) -> str:
    \"\"\"Генерирует URL для темы на основе названия и сайта\"\"\"
    site_url = sites.get(site_key, {}).get("url", "")
    if not site_url:
        return ""
    
    # Убираем trailing slash
    base_url = site_url.rstrip("/")
    
    # Генерируем slug из названия темы
    slug = topic_name.lower()
    slug = re.sub(r'[^\\w\\s-]', '', slug)
    slug = re.sub(r'[\\s_]+', '-', slug)
    slug = slug.strip('-')
    
    # Кодируем кириллицу
    from urllib.parse import quote
    slug_encoded = quote(slug, safe='-')
    
    return base_url + "/" + slug_encoded + ".html\""""

new_url_func = """def transliterate(text: str) -> str:
    \"\"\"Транслитерирует кириллицу в латиницу\"\"\"
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    result = []
    for char in text.lower():
        if char in translit_map:
            result.append(translit_map[char])
        elif char.isascii() and (char.isalnum() or char in '-_'):
            result.append(char)
        else:
            result.append('-')
    return ''.join(result)

def generate_topic_url(topic_name: str, site_key: str, sites: dict) -> str:
    \"\"\"Генерирует читаемый URL для темы\"\"\"
    site_url = sites.get(site_key, {}).get("url", "")
    if not site_url:
        return ""
    
    base_url = site_url.rstrip("/")
    
    # Транслитерируем и создаём slug
    slug = transliterate(topic_name)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')[:100]  # Ограничиваем длину
    
    return base_url + "/" + slug + ".html\""""

content = content.replace(old_url_func, new_url_func)

filepath.write_text(content, encoding="utf-8")
print("Linker v5 исправлен: URL теперь читаемые (транслитерация)")
