#!/usr/bin/env python3
"""
QA VALIDATOR
Проверяет качество сгенерированных HTML-страниц
"""

import argparse
import json
from pathlib import Path
from datetime import datetime

class QAVValidator:
    def __init__(self, site_dir: str, output_file: str):
        self.site_dir = Path(site_dir)
        self.output_file = Path(output_file)
        self.issues = []
        self.stats = {
            "total_pages": 0,
            "pages_with_css": 0,
            "pages_with_js": 0,
            "pages_with_fonts": 0,
            "pages_with_nav": 0,
            "pages_with_footer": 0,
            "errors": 0,
            "warnings": 0
        }
        
        print("="*70)
        print("QA VALIDATOR: Проверка качества сайта")
        print("="*70)
        print(f"📁 Директория: {self.site_dir}")
        print(f"📊 Отчёт: {self.output_file}")
        print("="*70)
    
    def check_html_file(self, html_file: Path):
        """Проверяет один HTML-файл"""
        self.stats["total_pages"] += 1
        rel_path = html_file.relative_to(self.site_dir)
        content = html_file.read_text(encoding="utf-8")
        
        issues = []
        
        # Проверка 1: Встроенный CSS
        if "<style>" in content:
            self.stats["pages_with_css"] += 1
        else:
            issues.append({"type": "error", "message": "Отсутствует встроенный CSS"})
            self.stats["errors"] += 1
        
        # Проверка 2: JavaScript
        if "<script>" in content:
            self.stats["pages_with_js"] += 1
        else:
            issues.append({"type": "warning", "message": "Отсутствует JavaScript"})
            self.stats["warnings"] += 1
        
        # Проверка 3: Google Fonts
        if "fonts.googleapis.com" in content:
            self.stats["pages_with_fonts"] += 1
        else:
            issues.append({"type": "warning", "message": "Не подключены Google Fonts"})
            self.stats["warnings"] += 1
        
        # Проверка 4: Навигация
        if 'class="nav"' in content:
            self.stats["pages_with_nav"] += 1
        else:
            issues.append({"type": "warning", "message": "Отсутствует навигация"})
            self.stats["warnings"] += 1
        
        # Проверка 5: Футер
        if "<footer>" in content:
            self.stats["pages_with_footer"] += 1
        else:
            issues.append({"type": "warning", "message": "Отсутствует футер"})
            self.stats["warnings"] += 1
        
        # Проверка 6: Мета-теги
        if '<meta name="description"' not in content:
            issues.append({"type": "warning", "message": "Отсутствует meta description"})
            self.stats["warnings"] += 1
        
        # Проверка 7: Viewport
        if "viewport" not in content:
            issues.append({"type": "error", "message": "Отсутствует meta viewport"})
            self.stats["errors"] += 1
        
        # Проверка 8: Title
        if "<title>" not in content:
            issues.append({"type": "error", "message": "Отсутствует <title>"})
            self.stats["errors"] += 1
        
        # Проверка 9: Размер файла
        file_size = html_file.stat().st_size
        if file_size < 5000:
            issues.append({"type": "warning", "message": f"Файл слишком маленький ({file_size} байт)"})
            self.stats["warnings"] += 1
        
        if issues:
            self.issues.append({"file": str(rel_path), "issues": issues})
    
    def run(self):
        """Запускает проверку всех HTML-файлов"""
        html_files = list(self.site_dir.rglob("index.html"))
        
        print(f"\n🔍 Найдено HTML-файлов: {len(html_files)}\n")
        
        for html_file in html_files:
            self.check_html_file(html_file)
        
        # Сохраняем отчёт
        report = {
            "timestamp": datetime.now().isoformat(),
            "site_dir": str(self.site_dir),
            "stats": self.stats,
            "issues": self.issues
        }
        
        self.output_file.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # Выводим результаты
        print("\n" + "="*70)
        print("ИТОГОВЫЙ ОТЧЁТ")
        print("="*70)
        print(f"📊 Всего страниц: {self.stats['total_pages']}")
        print(f"✅ С встроенным CSS: {self.stats['pages_with_css']}")
        print(f"✅ С JavaScript: {self.stats['pages_with_js']}")
        print(f"✅ С Google Fonts: {self.stats['pages_with_fonts']}")
        print(f"✅ С навигацией: {self.stats['pages_with_nav']}")
        print(f"✅ С футером: {self.stats['pages_with_footer']}")
        print(f"❌ Ошибок: {self.stats['errors']}")
        print(f"⚠️  Предупреждений: {self.stats['warnings']}")
        print(f"📁 Отчёт сохранён: {self.output_file}")
        print("="*70)
        
        return self.stats["errors"] == 0


def main():
    parser = argparse.ArgumentParser(description="QA Validator")
    parser.add_argument("--site-dir", required=True, help="Директория сайта")
    parser.add_argument("--output", required=True, help="Файл отчёта")
    args = parser.parse_args()
    
    validator = QAVValidator(args.site_dir, args.output)
    success = validator.run()
    
    import sys
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
