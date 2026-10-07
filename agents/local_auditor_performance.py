#!/usr/bin/env python3
"""
Local Auditor: Performance
Проверяет производительность страницы
"""

import argparse
import sys
from pathlib import Path
from bs4 import BeautifulSoup

def main():
    parser = argparse.ArgumentParser(description="Проверка производительности")
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
    
    # Проверка размера файла
    file_size = html_file.stat().st_size
    if file_size > 500000:  # 500KB
        issues.append(f"Файл слишком большой: {file_size/1024:.0f}KB (макс. 500KB)")
    elif file_size > 100000:  # 100KB
        warnings.append(f"Файл большой: {file_size/1024:.0f}KB (рекомендуется <100KB)")
    
    # Проверка инлайн-стилей
    inline_styles = soup.find_all(style=True)
    if len(inline_styles) > 10:
        warnings.append(f"Много инлайн-стилей: {len(inline_styles)}")
    
    # Проверка инлайн-скриптов
    inline_scripts = soup.find_all('script')
    inline_scripts = [s for s in inline_scripts if s.string]
    if len(inline_scripts) > 3:
        warnings.append(f"Много инлайн-скриптов: {len(inline_scripts)}")
    
    # Проверка количества элементов
    all_elements = soup.find_all()
    if len(all_elements) > 1000:
        warnings.append(f"Много DOM-элементов: {len(all_elements)}")
    
    if issues:
        print(f"❌ Performance: {len(issues)} проблем")
        for issue in issues:
            print(f"   - {issue}")
        sys.exit(1)
    elif warnings:
        print(f"⚠️  Performance: OK ({file_size/1024:.0f}KB), но {len(warnings)} предупреждений")
        sys.exit(0)
    else:
        print(f"✅ Performance: OK ({file_size/1024:.0f}KB, {len(all_elements)} элементов)")
        sys.exit(0)

if __name__ == "__main__":
    main()
