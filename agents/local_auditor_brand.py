#!/usr/bin/env python3
"""
Local Auditor: Brand
Проверяет элементы брендинга
"""

import argparse
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Проверка элементов брендинга")
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
    
    # Проверка логотипа
    logo = soup.find('img', class_=lambda x: x and 'logo' in x.lower())
    if not logo:
        logo = soup.find('a', class_=lambda x: x and 'logo' in x.lower())
    if not logo:
        warnings.append("Не найден элемент с классом 'logo'")
    
    # Проверка названия компании в title
    title = soup.find('title')
    if title:
        title_text = title.get_text().lower()
        if '103vet' not in title_text and 'вет' not in title_text:
            warnings.append("Название компании не найдено в <title>")
    
    # Проверка копирайта в футере
    footer = soup.find('footer')
    if footer:
        copyright_text = footer.get_text().lower()
        if '©' not in copyright_text and 'copyright' not in copyright_text:
            warnings.append("Не найден копирайт в футере")
    else:
        warnings.append("Отсутствует тег <footer>")
    
    if issues:
        print(f" Brand: {len(issues)} проблем")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    elif warnings:
        print(f"⚠️  Brand: OK, но {len(warnings)} предупреждений")
        sys.exit(0)
    else:
        print("✅ Brand: OK (элементы брендинга на месте)")
        sys.exit(0)

if __name__ == "__main__":
    main()
