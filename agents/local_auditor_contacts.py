#!/usr/bin/env python3
"""
Local Auditor: Contacts
Проверяет наличие контактной информации
"""

import argparse
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Проверка контактной информации")
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
    
    # Проверка телефона
    phone_pattern = re.compile(r'(\+?\d[\d\s\-\(\)]{7,}\d)')
    phones = phone_pattern.findall(html_content)
    if not phones:
        # Проверяем tel: ссылки
        tel_links = soup.find_all('a', href=re.compile(r'^tel:'))
        if not tel_links:
            issues.append("Не найден номер телефона")
    
    # Проверка email
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    emails = email_pattern.findall(html_content)
    if not emails:
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
        if not mailto_links:
            warnings.append("Не найден email адрес")
    
    # Проверка адреса
    address_keywords = ['ул.', 'улица', 'пр.', 'проспект', 'г.', 'город']
    has_address = any(keyword in html_content.lower() for keyword in address_keywords)
    if not has_address:
        warnings.append("Не найден физический адрес")
    
    if issues:
        print(f"❌ Contacts: {len(issues)} проблем")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    elif warnings:
        print(f"⚠️  Contacts: OK, но {len(warnings)} предупреждений")
        sys.exit(0)
    else:
        print(f"✅ Contacts: OK (найдено {len(phones)} телефонов, {len(emails)} email)")
        sys.exit(0)

if __name__ == "__main__":
    main()
