#!/usr/bin/env python3
"""
Local Auditor: Schema
Проверяет микроразметку Schema.org
"""

import argparse
import sys
import json
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Проверка Schema.org разметки")
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
    
    # Проверка JSON-LD
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    if not json_ld_scripts:
        warnings.append("Отсутствует JSON-LD разметка")
    else:
        # Проверяем валидность JSON
        for script in json_ld_scripts:
            try:
                json.loads(script.string)
            except:
                issues.append("Невалидный JSON в JSON-LD")
    
    # Проверка микроданных
    itemscope = soup.find_all(attrs={"itemscope": True})
    if not itemscope and not json_ld_scripts:
        warnings.append("Отсутствует любая микроразметка (JSON-LD или микроданные)")
    
    if issues:
        print(f"❌ Schema: {len(issues)} проблем")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    elif warnings:
        print(f"⚠️  Schema: OK, но {len(warnings)} предупреждений")
        sys.exit(0)
    else:
        print(f"✅ Schema: OK (найдено {len(json_ld_scripts)} JSON-LD блоков)")
        sys.exit(0)

if __name__ == "__main__":
    main()
