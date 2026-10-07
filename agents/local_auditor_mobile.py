#!/usr/bin/env python3
"""
Local Auditor: Mobile
Проверяет мобильную адаптацию
"""

import argparse
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Проверка мобильной адаптации")
    parser.add_argument("--file", required=True, help="Путь к HTML файлу")
    args = parser.parse_args()
    
    html_file = Path(args.file)
    if not html_file.exists():
        print(f"❌ Файл не найден: {html_file}")
        sys.exit(1)
    
    html_content = html_file.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    issues = []
    warnings = []
    
    # Проверка viewport
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    if not viewport:
        issues.append("Отсутствует meta viewport")
    else:
        content = viewport.get('content', '')
        if 'width=device-width' not in content:
            issues.append("Viewport не содержит width=device-width")
        if 'initial-scale' not in content:
            warnings.append("Viewport не содержит initial-scale")
    
    # Проверка мобильной навигации
    nav = soup.find('nav')
    if nav:
        burger = nav.find(class_=lambda x: x and 'burger' in x.lower())
        if not burger:
            warnings.append("Не найдена мобильная навигация (burger menu)")
    
    if issues:
        print(f" Mobile: {len(issues)} проблем")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    elif warnings:
        print(f"⚠️  Mobile: OK, но {len(warnings)} предупреждений")
        sys.exit(0)
    else:
        print("✅ Mobile: OK (мобильная адаптация корректна)")
        sys.exit(0)

if __name__ == "__main__":
    main()
