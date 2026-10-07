from pathlib import Path

filepath = Path("agents/registrar_v2.py")
content = filepath.read_text(encoding="utf-8")

# Улучшаем проверку неврологического соответствия
old_neuro = """        if "neurology" in topic_categories and "неврология" in site_themes_str:
            score += 30"""

new_neuro = """        if "neurology" in topic_categories and ("неврология" in site_themes_str or "эпилепсия" in site_themes_str or "судороги" in site_themes_str or "приступ" in site_themes_str):
            score += 30"""

content = content.replace(old_neuro, new_neuro)

# Улучшаем распознавание эмпатии для эпилепсии
old_emotion = """    high_emotion = ["эпилепсия", "диабет", "рак", "онколог", "приступ", "судорог", "срочно", "экстрен", "отравлен", "перелом", "травм", "смерт", "опасн", "инсульт"]"""
new_emotion = """    high_emotion = ["эпилепсия", "диабет", "рак", "онколог", "приступ", "судорог", "срочно", "экстрен", "отравлен", "перелом", "травм", "смерт", "опасн", "инсульт", "первые признаки", "симптомы"]"""

content = content.replace(old_emotion, new_emotion)

filepath.write_text(content, encoding="utf-8")
print("✅ Исправлено: эпилепсия теперь распознаётся как неврология + повышенная эмпатия")
