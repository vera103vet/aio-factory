#!/usr/bin/env python3
"""
Chief Editor v1.1 — адаптер для chief_editor.py
Проверка тональности и читабельности
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from chief_editor import run_chief_editor

def parse_args():
    parser = argparse.ArgumentParser(description='Chief Editor v1.1')
    parser.add_argument('--file', type=str, help='Путь к HTML-файлу')
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
        
        # Запускаем проверку (run_chief_editor сама печатает отчёт)
        result = run_chief_editor(filepath)
        
        if result is None:
            print("\n⚠️  Chief Editor вернул None — проверка не завершена")
        elif result.get('passed', False):
            print("\n✅ Итог: контент ОДОБРЕН главным редактором")
        else:
            print("\n❌ Итог: контент требует доработки")
    else:
        print("⚠️  Файл не указан. Используйте --file <path>")

if __name__ == "__main__":
    main()
