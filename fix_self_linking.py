from pathlib import Path

filepath = Path("agents/linker_ai_v5.py")
content = filepath.read_text(encoding="utf-8")

# Исправляем извлечение current_topic_name — убираем знаки препинания
old_extract = """    current_topic_name = filepath.stem.replace("_", " ").replace("?", "").strip()"""

new_extract = """    current_topic_name = filepath.stem.replace("_", " ").replace("?", "").replace("!", "").replace(".", "").replace(",", "").strip()"""

content = content.replace(old_extract, new_extract)

# Также исправляем сравнение — нормализуем обе строки
old_compare = """        # Пропускаем текущую тему (self-linking)
        if topic_name.lower() == current_topic_name.lower():
            continue"""

new_compare = """        # Пропускаем текущую тему (self-linking) — нормализуем обе строки
        topic_norm = re.sub(r'[^a-zа-яё0-9]', '', topic_name.lower())
        current_norm = re.sub(r'[^a-zа-яё0-9]', '', current_topic_name.lower())
        if topic_norm == current_norm:
            continue"""

content = content.replace(old_compare, new_compare)

filepath.write_text(content, encoding="utf-8")
print("Self-linking исправлен: нормализация строк при сравнении")
