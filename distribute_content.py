import json
import shutil
from pathlib import Path
from difflib import SequenceMatcher

SITE_MAP_FILE = Path("data/site_maps/palliative_site_map.json")
SOURCE_DIR = Path("data/generated_content")
TARGET_DIR = Path("data/sites/достойный_уход")

def load_site_map():
    with open(SITE_MAP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def find_best_match(page_name, html_files):
    """Находит наиболее подходящий HTML-файл по совпадению ключевых слов"""
    page_lower = page_name.lower()
    page_words = set(page_lower.split())
    
    best_match = None
    best_score = 0
    
    for html_file in html_files:
        file_stem = html_file.stem.lower().replace("_", " ")
        file_words = set(file_stem.split())
        
        # Считаем совпадение слов
        common = page_words & file_words
        score = len(common) / max(len(page_words), len(file_words))
        
        if score > best_score:
            best_score = score
            best_match = html_file
    
    return best_match, best_score

def normalize_url_to_path(url):
    """Превращает URL в путь к папке"""
    if url == "/":
        return TARGET_DIR
    url_path = url.strip("/")
    return TARGET_DIR / url_path

def main():
    print("="*70)
    print("DISTRIBUTE CONTENT: Распределение контента по структуре сайта")
    print("="*70)
    
    # Загружаем карту сайта
    site_map = load_site_map()
    pages = site_map["pages"]
    
    # Получаем список всех HTML-файлов в источнике
    html_files = list(SOURCE_DIR.glob("*.html"))
    print(f"📂 Найдено HTML-файлов в источнике: {len(html_files)}")
    print(f" Страниц в карте сайта: {len(pages)}")
    print("-"*70)
    
    distributed = 0
    not_found = 0
    used_files = set()
    
    for page in pages:
        page_name = page["name"]
        page_url = page["url"]
        target_path = normalize_url_to_path(page_url)
        target_file = target_path / "index.html"
        
        # Ищем лучший матч
        best_match, score = find_best_match(page_name, html_files)
        
        if best_match and score > 0.2:
            # Копируем файл
            target_path.mkdir(parents=True, exist_ok=True)
            shutil.copy2(best_match, target_file)
            used_files.add(best_match)
            distributed += 1
            print(f"✅ {page_name}")
            print(f"   {best_match.name} → {target_file.relative_to(TARGET_DIR)}")
            print(f"   Совпадение: {score:.0%}")
        else:
            not_found += 1
            print(f"⚠️  {page_name} — файл не найден (создаём заглушку)")
            target_path.mkdir(parents=True, exist_ok=True)
            # Создаём минимальную заглушку
            target_file.write_text(
                f"<!DOCTYPE html><html lang='ru'><head><meta charset='UTF-8'>"
                f"<title>{page_name} | 103vet.by</title>"
                f"<link rel='stylesheet' href='../../styles.css'></head><body>"
                f"<main><section class='section'><div class='container'>"
                f"<h1>{page_name}</h1>"
                f"<p>Контент находится в разработке.</p>"
                f"</div></section></main></body></html>",
                encoding="utf-8"
            )
    
    print("\n" + "="*70)
    print("ИТОГОВЫЙ ОТЧЁТ")
    print("="*70)
    print(f"✅ Распределено: {distributed} файлов")
    print(f"⚠️  Заглушек создано: {not_found}")
    print(f"📁 Неиспользованных файлов в источнике: {len(html_files) - len(used_files)}")
    print(f"📂 Итоговый путь: {TARGET_DIR}")
    print("="*70)
    
    # Проверяем результат
    final_count = len(list(TARGET_DIR.rglob("*.html")))
    print(f"\n🎯 Всего HTML-файлов в сайте: {final_count}")

if __name__ == "__main__":
    main()
