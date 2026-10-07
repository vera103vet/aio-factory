#!/usr/bin/env python3
"""
Local Auditor: Images
Проверяет изображения и alt-атрибуты
"""

import argparse
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Проверка изображений")
    parser.add_argument("--file", required=True, help="Путь к HTML файлу")
    args = parser.parse_args()
    
    html_file = Path(args.file)
    if not html_file.exists():
        print(f"❌ Файл не найден: {html_file}")
        sys.exit(1)
    
    html_content = html_file.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    images = soup.find_all('img')
    issues = []
    warnings = []
    
    # Проверка alt-атрибутов
    no_alt = [img for img in images if not img.get('alt')]
    if no_alt:
        issues.append(f"Найдено {len(no_alt)} изображений без alt-атрибута")
    
    # Проверка пустых alt
    empty_alt = [img for img in images if img.get('alt') == '']
    if empty_alt:
        warnings.append(f"Найдено {len(empty_alt)} изображений с пустым alt")
    
    # Проверка ширины/высоты
    no_dimensions = [img for img in images if not (img.get('width') or img.get('height'))]
    if no_dimensions:
        warnings.append(f"Найдено {len(no_dimensions)} изображений без width/height")
    
    if issues:
        print(f"❌ Images: {len(issues)} проблем")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    elif warnings:
        print(f"️  Images: OK ({len(images)} изображений), но {len(warnings)} предупреждений")
        sys.exit(0)
    else:
        print(f"✅ Images: OK ({len(images)} изображений с корректными alt)")
        sys.exit(0)

if __name__ == "__main__":
    main()
