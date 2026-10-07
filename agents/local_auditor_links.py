#!/usr/bin/env python3
"""
Local Auditor: Links
Проверяет ссылки на странице
"""

import argparse
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Проверка ссылок")
    parser.add_argument("--file", required=True, help="Путь к HTML файлу")
    args = parser.parse_args()
    
    html_file = Path(args.file)
    if not html_file.exists():
        print(f"❌ Файл не найден: {html_file}")
        sys.exit(1)
    
    html_content = html_file.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    links = soup.find_all('a', href=True)
    issues = []
    warnings = []
    
    # Проверка пустых ссылок
    empty_links = [link for link in links if not link.get('href').strip()]
    if empty_links:
        issues.append(f"Найдено {len(empty_links)} пустых ссылок")
    
    # Проверка ссылок без текста
    no_text_links = [link for link in links if not link.get_text(strip=True)]
    if no_text_links:
        warnings.append(f"Найдено {len(no_text_links)} ссылок без текста")
    
    # Проверка внешних ссылок без target="_blank"
    external_links = [link for link in links if link['href'].startswith('http')]
    no_target = [link for link in external_links if not link.get('target')]
    if no_target:
        warnings.append(f"Найдено {len(no_target)} внешних ссылок без target='_blank'")
    
    # Проверка наличия внутренних ссылок
    internal_links = [link for link in links if not link['href'].startswith('http')]
    if not internal_links:
        warnings.append("Отсутствуют внутренние ссылки")
    
    if issues:
        print(f"❌ Links: {len(issues)} проблем")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    elif warnings:
        print(f"⚠️  Links: OK ({len(links)} ссылок), но {len(warnings)} предупреждений")
        sys.exit(0)
    else:
        print(f"✅ Links: OK ({len(links)} ссылок проверено)")
        sys.exit(0)

if __name__ == "__main__":
    main()
