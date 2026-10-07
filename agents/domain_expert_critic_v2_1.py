import sys
import argparse
from pathlib import Path

# Импортируем существующую функциональность
sys.path.insert(0, str(Path(__file__).parent))
from domain_expert_critic import run_expert_critique, test_critic_on_latest_file

def parse_args():
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(description='Domain Expert Critic v2.1: Проверка экспертизы')
    parser.add_argument('--file', type=str, help='Путь к HTML-файлу для проверки')
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("="*70)
    print("DOMAIN EXPERT CRITIC v2.1: Проверка ветеринарной экспертизы")
    print("="*70)
    
    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"❌ ОШИБКА: Файл не найден: {filepath}")
            sys.exit(1)
        
        print(f"📄 Файл: {filepath}")
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
        result = run_expert_critique(topic_name, text)
        
        # Выводим результаты
        print(f"\n📚 Категория: {result['category'].upper()}")
        print(f"📜 Протоколы: {', '.join(result['protocols_checked'])}")
        print("-" * 70)
        
        if result['passed']:
            print("✅ ВЕРДИКТ: ОДОБРЕНО ЭКСПЕРТОМ")
            print("   Контент демонстрирует глубокое понимание темы и соответствует актуальным стандартам.")
        else:
            print("❌ ВЕРДИКТ: ТРЕБУЕТСЯ ДОРАБОТКА")
            for issue in result['feedback']:
                print(f"   ⚠️ {issue}")
        
        print("="*70)
    else:
        print("⚠️  Файл не указан. Проверяю последний файл из data/generated_content/")
        test_critic_on_latest_file()

if __name__ == "__main__":
    main()
