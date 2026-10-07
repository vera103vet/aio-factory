#!/usr/bin/env python3
"""
Local Auditor: SEO Basics
Проверяет базовые SEO-элементы
"""

import argparse
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Проверка SEO-элементов")
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
    
    # Проверка <title>
    title = soup.find('title')
    if not title:
        issues.append("Отсутствует <title>")
    elif len(title.get_text().strip()) < 10:
        warnings.append(f"<title> слишком короткий ({len(title.get_text())} симв.)")
    elif len(title.get_text().strip()) > 70:
        warnings.append(f"<title> слишком длинный ({len(title.get_text())} симв.)")
    
    # Проверка meta description
    desc = soup.find('meta', attrs={'name': 'description'})
    if not desc:
        issues.append("Отсутствует meta description")
    elif len(desc.get('content', '')) < 50:
        warnings.append(f"meta description слишком короткий")
    
    # Проверка <h1>
    h1_tags = soup.find_all('h1')
    if not h1_tags:
        issues.append("Отсутствует <h1>")
    elif len(h1_tags) > 1:
        warnings.append(f"Несколько <h1> ({len(h1_tags)})")
    
    # Проверка canonical
    canonical = soup.find('link', rel='canonical')
    if not canonical:
        warnings.append("Отсутствует link canonical")
    
    if issues:
        print(f"❌ SEO Basics: {len(issues)} критических проблем")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    elif warnings:
        print(f"⚠️  SEO Basics: OK, но {len(warnings)} предупреждений")
        sys.exit(0)
    else:
        print("✅ SEO Basics: OK (все базовые элементы на месте)")
        sys.exit(0)

if __name__ == "__main__":
    main()
