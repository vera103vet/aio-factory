#!/usr/bin/env python3
"""
Local Auditor: Accessibility
Проверяет доступность (a11y)
"""

import argparse
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Проверка доступности")
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
    
    # Проверка семантических тегов
    if not soup.find('main'):
        warnings.append("Отсутствует тег <main>")
    if not soup.find('nav'):
        warnings.append("Отсутствует тег <nav>")
    if not soup.find('footer'):
        warnings.append("Отсутствует тег <footer>")
    
    # Проверка lang атрибута
    html_tag = soup.find('html')
    if html_tag and not html_tag.get('lang'):
        issues.append("Отсутствует атрибут lang у <html>")
    
    # Проверка контрастности ссылок (упрощённо)
    links = soup.find_all('a')
    no_text_links = [link for link in links if not link.get_text(strip=True)]
    if no_text_links:
        issues.append(f"Найдено {len(no_text_links)} ссылок без текста")
    
    # Проверка форм
    forms = soup.find_all('form')
    for form in forms:
        inputs = form.find_all('input')
        for inp in inputs:
            if inp.get('type') not in ['submit', 'button', 'hidden']:
                if not inp.get('aria-label') and not inp.get('id'):
                    warnings.append("Поле формы без label или aria-label")
    
    if issues:
        print(f"❌ Accessibility: {len(issues)} проблем")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    elif warnings:
        print(f"⚠️  Accessibility: OK, но {len(warnings)} предупреждений")
        sys.exit(0)
    else:
        print("✅ Accessibility: OK (базовая доступность обеспечена)")
        sys.exit(0)

if __name__ == "__main__":
    main()
