#!/usr/bin/env python3
"""
Local Auditor: HTML Structure
Проверяет базовую структуру HTML5
"""

import argparse
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Проверка структуры HTML")
    parser.add_argument("--file", required=True, help="Путь к HTML файлу")
    args = parser.parse_args()
    
    html_file = Path(args.file)
    if not html_file.exists():
        print(f"❌ Файл не найден: {html_file}")
        sys.exit(1)
    
    html_content = html_file.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    issues = []
    
    # Проверка DOCTYPE
    if not html_content.strip().lower().startswith('<!doctype'):
        issues.append("Отсутствует DOCTYPE")
    
    # Проверка <html>
    if not soup.find('html'):
        issues.append("Отсутствует тег <html>")
    
    # Проверка <head>
    if not soup.find('head'):
        issues.append("Отсутствует тег <head>")
    
    # Проверка <body>
    if not soup.find('body'):
        issues.append("Отсутствует тег <body>")
    
    # Проверка <title>
    if not soup.find('title'):
        issues.append("Отсутствует тег <title>")
    
    # Проверка charset
    if not soup.find('meta', charset=True):
        issues.append("Отсутствует meta charset")
    
    # Проверка viewport
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    if not viewport:
        issues.append("Отсутствует meta viewport (мобильная адаптация)")
    
    if issues:
        print(f"❌ HTML Structure: {len(issues)} проблем")
        for issue in issues[:5]:
            print(f"   - {issue}")
        sys.exit(1)
    else:
        print("✅ HTML Structure: OK (валидная структура HTML5)")
        sys.exit(0)

if __name__ == "__main__":
    main()
