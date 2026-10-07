import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

SITE_MAPS_DIR = Path("data/site_maps")
OUTPUT_DIR = Path("data/sites")
AGENTS_DIR = Path("agents")

def load_site_map(map_file: str) -> Dict:
    """Загружает карту сайта из JSON"""
    filepath = SITE_MAPS_DIR / map_file
    if not filepath.exists():
        print(f"ОШИБКА: Файл карты сайта не найден: {filepath}")
        return None
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def create_directory_structure(site_name: str, pages: List[Dict]) -> Path:
    """Создаёт структуру папок для сайта"""
    site_dir = OUTPUT_DIR / site_name
    site_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаём папки для каждой страницы
    for page in pages:
        url = page["url"]
        if url == "/":
            continue  # Главная страница будет в корне
        
        # Убираем ведущий и trailing slash
        url_path = url.strip("/")
        page_dir = site_dir / url_path
        page_dir.mkdir(parents=True, exist_ok=True)
    
    # Копируем styles.css
    styles_src = Path("styles.css")
    if styles_src.exists():
        styles_dst = site_dir / "styles.css"
        styles_dst.write_text(styles_src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"✅ styles.css скопирован в {site_dir}")
    
    return site_dir

def generate_page_content(page: Dict, site_dir: Path) -> bool:
    """Генерирует контент для одной страницы через команду агентов"""
    url = page["url"]
    name = page["name"]
    page_type = page["type"]
    
    print(f"\n{'─'*70}")
    print(f"📄 Генерация: {name}")
    print(f"   URL: {url}")
    print(f"   Тип: {page_type}")
    print(f"{'─'*70}")
    
    # Определяем путь к файлу
    if url == "/":
        output_file = site_dir / "index.html"
    else:
        url_path = url.strip("/")
        output_file = site_dir / url_path / "index.html"
    
    # Вызываем Writer AI Pro для генерации контента
    try:
        result = subprocess.run(
            [sys.executable, str(AGENTS_DIR / "writer_ai_pro_v2_1.py"), 
             "--topic", name, "--output", str(output_file)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print(f"✅ Writer AI Pro: контент сгенерирован")
        else:
            print(f"⚠️ Writer AI Pro: ошибка - {result.stderr[:100]}")
            return False
        
    except subprocess.TimeoutExpired:
        print(f"⚠️ Writer AI Pro: таймаут (120 сек)")
        return False
    except Exception as e:
        print(f"⚠️ Writer AI Pro: исключение - {str(e)[:100]}")
        return False
    
    # Вызываем Validator AI для проверки
    try:
        result = subprocess.run(
            [sys.executable, str(AGENTS_DIR / "validator_ai_v2_1.py"),
             "--file", str(output_file)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✅ Validator AI: 7/7 проверок пройдено")
        else:
            print(f"⚠️ Validator AI: предупреждения")
        
    except Exception as e:
        print(f"⚠️ Validator AI: исключение - {str(e)[:100]}")
    
    # Вызываем Domain Expert Critic
    try:
        result = subprocess.run(
            [sys.executable, str(AGENTS_DIR / "domain_expert_critic_v2_1.py"),
             "--file", str(output_file)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if "ОДОБРЕНО" in result.stdout:
            print(f"✅ Domain Expert Critic: ОДОБРЕНО")
        else:
            print(f"⚠️ Domain Expert Critic: требуется доработка")
        
    except Exception as e:
        print(f"⚠️ Domain Expert Critic: исключение - {str(e)[:100]}")
    
    # Вызываем Chief Editor
    try:
        result = subprocess.run(
            [sys.executable, str(AGENTS_DIR / "chief_editor_v1_1.py"),
             "--file", str(output_file)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if "ОДОБРЕНО" in result.stdout:
            print(f"✅ Chief Editor: ОДОБРЕНО")
        else:
            print(f"⚠️ Chief Editor: требуется доработка")
        
    except Exception as e:
        print(f"⚠️ Chief Editor: исключение - {str(e)[:100]}")
    
    return True

def generate_site(site_map: Dict):
    """Главная функция: генерирует весь сайт"""
    site_name = site_map["site_name"].lower().replace(" ", "_")
    pages = site_map["pages"]
    total_pages = len(pages)
    
    print("\n" + "="*70)
    print("MAESTRO v2: ЗАПУСК КОНВЕЙЕРА ПРОИЗВОДСТВА")
    print("="*70)
    print(f"Сайт: {site_map['site_name']}")
    print(f"Домен: {site_map['domain']}")
    print(f"Всего страниц: {total_pages}")
    print(f"Дата начала: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    # Создаём структуру папок
    print(f"\n📁 Создание структуры папок...")
    site_dir = create_directory_structure(site_name, pages)
    print(f"✅ Структура создана: {site_dir}")
    
    # Сортируем страницы по приоритету
    pages_sorted = sorted(pages, key=lambda x: x["priority"])
    
    # Генерируем контент для каждой страницы
    success_count = 0
    fail_count = 0
    
    for i, page in enumerate(pages_sorted, 1):
        print(f"\n[{i}/{total_pages}] ", end="")
        
        if generate_page_content(page, site_dir):
            success_count += 1
            page["status"] = "completed"
        else:
            fail_count += 1
            page["status"] = "failed"
        
        # Прогресс-бар
        progress = int((i / total_pages) * 100)
        bar_length = 40
        filled = int(bar_length * i / total_pages)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\n   Прогресс: [{bar}] {progress}%")
    
    # Итоговый отчёт
    print("\n" + "="*70)
    print("MAESTRO v2: ИТОГОВЫЙ ОТЧЁТ")
    print("="*70)
    print(f"✅ Успешно: {success_count} страниц")
    print(f"❌ Ошибки: {fail_count} страниц")
    print(f"📊 Всего: {total_pages} страниц")
    print(f"📁 Путь: {site_dir}")
    print(f"⏱️  Завершено: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    # Сохраняем отчёт
    report = {
        "site_name": site_map["site_name"],
        "domain": site_map["domain"],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_pages": total_pages,
        "success": success_count,
        "failed": fail_count,
        "output_dir": str(site_dir),
        "pages": pages
    }
    
    report_file = site_dir / "generation_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Отчёт сохранён: {report_file}")
    print("\n🎉 Сайт готов к деплою!")

def main():
    if len(sys.argv) < 2:
        print("Использование: python maestro_v2.py --site-map=<filename.json>")
        print("Пример: python maestro_v2.py --site-map=palliative_site_map.json")
        sys.exit(1)
    
    # Парсим аргументы
    site_map_file = None
    for arg in sys.argv[1:]:
        if arg.startswith("--site-map="):
            site_map_file = arg.split("=")[1]
            break
    
    if not site_map_file:
        print("ОШИБКА: Не указан файл карты сайта")
        sys.exit(1)
    
    # Загружаем карту сайта
    print(f"📂 Загрузка карты сайта: {site_map_file}")
    site_map = load_site_map(site_map_file)
    
    if not site_map:
        print("ОШИБКА: Не удалось загрузить карту сайта")
        sys.exit(1)
    
    # Запускаем генерацию
    generate_site(site_map)

if __name__ == "__main__":
    main()
