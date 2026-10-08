#!/usr/bin/env python3
"""
SEO Quality Auditor v1.0
Второй страж: проверяет сгенерированный контент на переспам и каннибализацию
"""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter

class SEOQualityAuditor:
    def __init__(self, project_dir: str, content_map_file: str):
        self.project_dir = Path(project_dir)
        self.content_map_file = Path(content_map_file)
        self.report = {
            "status": "pending",
            "pages_checked": 0,
            "pages_passed": 0,
            "pages_failed": 0,
            "issues": []
        }
        self.page_texts = {} # Для проверки на каннибализацию
        
    def load_content_map(self) -> dict:
        """Загружает карту контента с SEO-правилами"""
        with open(self.content_map_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def extract_text(self, html_file: Path) -> str:
        """Извлекает чистый текст из HTML (без тегов и скриптов)"""
        soup = BeautifulSoup(html_file.read_text(encoding='utf-8'), 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        return soup.get_text(separator=' ', strip=True).lower()
        
    def check_keyword_density(self, text: str, seo_rules: dict, filename: str) -> list:
        """Проверяет плотность и частоту ключевых слов"""
        issues = []
        words = re.findall(r'\b\w+\b', text)
        total_words = len(words)
        
        if total_words == 0:
            issues.append(f"{filename}: Пустой текст")
            return issues
            
        primary_kw = seo_rules.get('primary_keyword', '').lower()
        max_freq = seo_rules.get('max_frequency', 3)
        
        if primary_kw:
            # Считаем точные вхождения (упрощенно)
            count = text.count(primary_kw)
            density = (count / total_words) * 100
            
            if count > max_freq:
                issues.append(f"{filename}: Переспам ключевого слова '{primary_kw}'. Найдено: {count}, лимит: {max_freq}")
            
            if density > 3.5:
                issues.append(f"{filename}: Высокая плотность ключа '{primary_kw}': {density:.2f}% (лимит 3.5%)")
                
        return issues

    def check_cannibalization(self) -> list:
        """Проверяет страницы на семантическое пересечение (каннибализацию)"""
        issues = []
        filenames = list(self.page_texts.keys())
        
        for i in range(len(filenames)):
            for j in range(i + 1, len(filenames)):
                file1, file2 = filenames[i], filenames[j]
                text1, text2 = self.page_texts[file1], self.page_texts[file2]
                
                # Простая проверка: если более 60% уникальных слов одной страницы есть в другой
                words1 = set(re.findall(r'\b\w{4,}\b', text1)) # Слова длиннее 3 букв
                words2 = set(re.findall(r'\b\w{4,}\b', text2))
                
                if len(words1) > 0 and len(words2) > 0:
                    overlap = len(words1.intersection(words2)) / min(len(words1), len(words2))
                    if overlap > 0.65: # Порог каннибализации 65%
                        issues.append(f"Риск каннибализации: {file1} и {file2} слишком похожи (пересечение {overlap*100:.1f}%)")
                        
        return issues

    def audit(self) -> dict:
        """Запускает полный аудит проекта"""
        print("="*70)
        print("🛡️ ЗАПУК SEO QUALITY AUDITOR v1.0")
        print("="*70)
        
        try:
            content_map = self.load_content_map()
        except FileNotFoundError:
            print("❌ Ошибка: Файл content_map_enriched.json не найден!")
            return self.report
            
        html_files = sorted(self.project_dir.glob("*.html"))
        
        if not html_files:
            print(f"⚠️ В папке {self.project_dir} не найдено HTML-файлов для проверки.")
            return self.report
            
        print(f"🔍 Найдено файлов для проверки: {len(html_files)}")
        
        # 1. Проверка каждой страницы на переспам
        for html_file in html_files:
            self.report["pages_checked"] += 1
            text = self.extract_text(html_file)
            self.page_texts[html_file.name] = text
            
            # Находим правила для этой страницы (по имени файла или slug)
            # Для простоты ищем страницу, чей slug содержится в имени файла, или берем по порядку
            page_rules = None
            for page in content_map.get('pages', []):
                if page['slug'].replace('/', '-') in html_file.stem or str(page['page_id']) in html_file.stem:
                    page_rules = page.get('seo', {})
                    break
            
            if not page_rules:
                # Fallback: если не нашли точное совпадение, берем пустые правила (проверим только общие)
                page_rules = {'primary_keyword': '', 'max_frequency': 5}
                
            issues = self.check_keyword_density(text, page_rules, html_file.name)
            
            if issues:
                self.report["pages_failed"] += 1
                self.report["issues"].extend(issues)
                print(f"   ❌ {html_file.name}: Найдены проблемы")
                for issue in issues:
                    print(f"      → {issue}")
            else:
                self.report["pages_passed"] += 1
                print(f"   ✅ {html_file.name}: OK")
                
        # 2. Проверка на каннибализацию между всеми страницами
        print("\n🔍 Проверка на каннибализацию...")
        cannibal_issues = self.check_cannibalization()
        if cannibal_issues:
            self.report["pages_failed"] += len(cannibal_issues) # Условно считаем как ошибки
            self.report["issues"].extend(cannibal_issues)
            for issue in cannibal_issues:
                print(f"   ⚠️ {issue}")
        else:
            print("   ✅ Каннибализация не обнаружена")
            
        # Итоговый статус
        if self.report["pages_failed"] == 0:
            self.report["status"] = "PASSED"
            print("\n🎉 АУДИТ ПРОЙДЕН УСПЕШНО! Контент готов к следующему этапу.")
        else:
            self.report["status"] = "FAILED"
            print(f"\n⚠️ АУДИТ НЕ ПРОЙДЕН. Найдено проблем: {len(self.report['issues'])}")
            
        # Сохраняем отчёт
        report_file = self.project_dir / "seo_audit_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        print(f"📄 Отчёт сохранён: {report_file}")
        print("="*70)
        
        return self.report

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='SEO Quality Auditor')
    parser.add_argument('--dir', required=True, help='Папка с HTML-файлами')
    parser.add_argument('--map', required=True, help='Путь к content_map_enriched.json')
    args = parser.parse_args()
    
    auditor = SEOQualityAuditor(args.dir, args.map)
    auditor.audit()
