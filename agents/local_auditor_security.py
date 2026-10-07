#!/usr/bin/env python3
"""
Local Auditor: Security
Проверяет безопасность HTML
"""

import argparse
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Проверка безопасности")
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
    
    # Проверка внешних скриптов без integrity
    external_scripts = soup.find_all('script', src=True)
    no_integrity = [s for s in external_scripts if not s.get('integrity')]
    if no_integrity:
        warnings.append(f"Найдено {len(no_integrity)} внешних скриптов без integrity")
    
    # Проверка форм без HTTPS
    forms = soup.find_all('form', action=True)
    http_forms = [f for f in forms if f['action'].startswith('http://')]
    if http_forms:
        issues.append(f"Найдено {len(http_forms)} форм с HTTP (нужен HTTPS)")
    
    # Проверка target="_blank" без rel="noopener"
    links = soup.find_all('a', target='_blank')
    no_rel = [link for link in links if 'noopener' not in link.get('rel', [])]
    if no_rel:
        warnings.append(f"Найдено {len(no_rel)} ссылок с target='_blank' без rel='noopener'")
    
    # Проверка iframe
    iframes = soup.find_all('iframe')
    if iframes:
        warnings.append(f"Найдено {len(iframes)} iframe (потенциальный риск)")
    
    if issues:
        print(f"❌ Security: {len(issues)} проблем")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    elif warnings:
        print(f"⚠️  Security: OK, но {len(warnings)} предупреждений")
        sys.exit(0)
    else:
        print("✅ Security: OK (базовая безопасность обеспечена)")
        sys.exit(0)

if __name__ == "__main__":
    main()
