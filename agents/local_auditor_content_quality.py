#!/usr/bin/env python3
"""
Local Auditor: Content Quality
Проверяет качество и объём контента
"""

import argparse
import sys
import re
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Проверка качества контента")
    parser.add_argument("--file", required=True, help="Путь к HTML файлу")
    args = parser.parse_args()
    
    html_file = Path(args.file)
    if not html_file.exists():
        print(f" Файл не найден: {html_file}")
        sys.exit(1)
    
    html_content = html_file.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Удаляем скрипты и стили
    for script in soup(['script', 'style']):
        script.decompose()
    
    text = soup.get_text(separator=' ', strip=True)
    words = text.split()
    word_count = len(words)
    
    issues = []
    warnings = []
    
    # Проверка объёма
    if word_count < 300:
        issues.append(f"Мало контента: {word_count} слов (мин. 300)")
    elif word_count < 500:
        warnings.append(f"Мало контента: {word_count} слов (рекомендуется 500+)")
    
    # Проверка абзацев
    paragraphs = soup.find_all('p')
    if len(paragraphs) < 3:
        warnings.append(f"Мало абзацев: {len(paragraphs)} (рекомендуется 3+)")
    
    # Проверка заголовков
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if len(headings) < 2:
        warnings.append(f"Мало заголовков: {len(headings)} (рекомендуется 2+)")
    
    # Проверка списков
    lists = soup.find_all(['ul', 'ol'])
    if not lists:
        warnings.append("Отсутствуют списки (рекомендуется для структуры)")
    
    if issues:
        print(f"❌ Content Quality: {len(issues)} проблем")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    elif warnings:
        print(f"⚠️  Content Quality: OK ({word_count} слов), но {len(warnings)} предупреждений")
        sys.exit(0)
    else:
        print(f"✅ Content Quality: OK ({word_count} слов, {len(paragraphs)} абзацев)")
        sys.exit(0)

if __name__ == "__main__":
    main()
