from pathlib import Path

filepath = Path("agents/strategist_v2.py")
content = filepath.read_text(encoding="utf-8")

# Исправляем функцию check_cannibalization
old_code = '''def check_cannibalization(topic: str, site: str, registry: Dict) -> Tuple[bool, str]:
    """Проверяет, не занята ли тема другим сайтом (защита от каннибализации)"""
    topics = registry.get("topics", [])'''

new_code = '''def check_cannibalization(topic: str, site: str, registry) -> Tuple[bool, str]:
    """Проверяет, не занята ли тема другим сайтом (защита от каннибализации)"""
    # registry может быть списком или словарём
    if isinstance(registry, list):
        topics = registry
    elif isinstance(registry, dict):
        topics = registry.get("topics", [])
    else:
        topics = []'''

content = content.replace(old_code, new_code)

filepath.write_text(content, encoding="utf-8")
print("✅ Strategist v2 исправлен: корректная обработка registry")
