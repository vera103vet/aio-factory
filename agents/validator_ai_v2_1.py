import sys
import argparse
from pathlib import Path

# Импортируем существующую функциональность
sys.path.insert(0, str(Path(__file__).parent))
from validator_ai_v2 import validate_html_file

def parse_args():
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(description='Validator AI v2.1: Проверка HTML')
    parser.add_argument('--file', type=str, help='Путь к HTML-файлу для проверки')
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("="*70)
    print("VALIDATOR AI v2.1: Проверка HTML-файла")
    print("="*70)
    
    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"❌ ОШИБКА: Файл не найден: {filepath}")
            sys.exit(1)
        
        print(f"📄 Файл: {filepath}")
        print("="*70)
        
        # Вызываем существующую функцию валидации
        validate_html_file(filepath)
    else:
        print("⚠️  Файл не указан. Использую последний файл из data/generated_content/")
        # Вызываем без аргументов — использует последний файл
        validate_html_file()

if __name__ == "__main__":
    main()
