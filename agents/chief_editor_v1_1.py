import sys
import argparse
from pathlib import Path

# Импортируем существующую функциональность
sys.path.insert(0, str(Path(__file__).parent))
from chief_editor import run_chief_editor, test_editor_on_latest_file

def parse_args():
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(description='Chief Editor v1.1: Проверка тональности и читабельности')
    parser.add_argument('--file', type=str, help='Путь к HTML-файлу для проверки')
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("="*70)
    print("CHIEF EDITOR v1.1: Проверка тональности и читабельности")
    print("="*70)
    
    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"❌ ОШИБКА: Файл не найден: {filepath}")
            sys.exit(1)
        
        print(f" Файл: {filepath}")
        print("="*70)
        
        # Читаем файл
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Извлекаем текст из HTML
        import re
        text = re.sub(r'<[^>]+>', ' ', content)
        
        # Определяем тему из имени файла
        topic_name = filepath.stem.replace("_", " ").replace("-", " ").strip()
        
        # Запускаем проверку
        result = run_chief_editor(topic_name, text)
        
        # Выводим результаты
        print(f"\n📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
        print("-" * 70)
        
        if result['passed']:
            print("✅ ВЕРДИКТ: ОДОБРЕНО ГЛАВНЫМ РЕДАКТОРОМ")
            print("   Контент соответствует тональности бренда и стандартам читабельности.")
        else:
            print("❌ ВЕРДИКТ: ТРЕБУЕТСЯ ДОРАБОТКА")
            for issue in result['feedback']:
                print(f"   ️ {issue}")
        
        print("="*70)
    else:
        print("️  Файл не указан. Проверяю последний файл из data/generated_content/")
        test_editor_on_latest_file()

if __name__ == "__main__":
    main()
