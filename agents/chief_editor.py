import json
import re
import yaml
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple
from datetime import datetime

RULES_FILE = Path("config/seo_rules.yaml")
OUTPUT_DIR = Path("data/generated_content")
MAX_SENTENCE_LENGTH = 25
MAX_PARAGRAPH_LENGTH = 150

def load_rules():
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "brand_philosophy": "Пространство спокойствия для людей и безопасности для животных",
            "forbidden": ["цены", "стоимость", "руб", "конкретные имена врачей"],
            "mandatory_tone": "эмпатичный, профессиональный, успокаивающий"
        }

def parse_html(filepath: Path) -> Dict:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    return {
        "soup": soup,
        "text": text,
        "sentences": [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 5],
        "paragraphs": [p.get_text(strip=True) for p in soup.find_all(['p', 'li']) if len(p.get_text(strip=True).split()) > 5],
        "headings": [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])]
    }

def check_brand_voice(parsed: Dict) -> Tuple[bool, str, List[str]]:
    text_lower = parsed["text"].lower()
    issues = []
    
    empathy_markers = ['понимаем', 'ваш питомец', 'ваш любимец', 'беспокойство', 'тревога', 'забота', 'безопасность']
    empathy_count = sum(1 for m in empathy_markers if m in text_lower)
    if empathy_count < 2:
        issues.append("Низкая эмпатия: найдено только " + str(empathy_count) + " маркеров (нужно >= 2)")
    
    panic_markers = ['катастрофа', 'ужас', 'паника', 'безнадежно']
    panic_count = sum(1 for m in panic_markers if m in text_lower)
    if panic_count >= 1:
        issues.append("Слишком панический тон: найдены маркеры ужаса/паники")
    
    philosophy_keywords = ['спокойствие', 'безопасность', 'профессионализм', 'забота']
    if not any(kw in text_lower for kw in philosophy_keywords):
        issues.append("Не транслируется философия бренда (спокойствие, безопасность, забота)")
    
    if issues:
        return False, "Нарушена тональность бренда", issues
    return True, "Тональность соответствует философии бренда", []

def check_sanity(parsed: Dict) -> Tuple[bool, str, List[str]]:
    text_lower = parsed["text"].lower()
    issues = []
    
    # Опасные лекарства
    dangerous_drugs = ['парацетамол', 'аспирин', 'ибупрофен']
    
    # Проверяем каждое опасное лекарство
    for drug in dangerous_drugs:
        if drug in text_lower:
            # Ищем контекст вокруг упоминания
            drug_index = text_lower.find(drug)
            context_start = max(0, drug_index - 100)
            context_end = min(len(text_lower), drug_index + 100)
            context = text_lower[context_start:context_end]
            
            # Проверяем, есть ли слова предупреждения в контексте
            warning_words = ['токсичен', 'токсичны', 'опасен', 'опасны', 'нельзя', 'не давайте', 'запрещено', 'вреден']
            has_warning = any(w in context for w in warning_words)
            
            # Если нет предупреждения — это ошибка
            if not has_warning:
                issues.append("КРИТИЧЕСКАЯ ОШИБКА: Упомянут " + drug + " без предупреждения о токсичности!")
    
    # Проверяем "человеческие лекарства/препараты" (гибкая проверка)
    has_human_mention = False
    human_mention_index = -1
    
    # Ищем "человеческ" рядом с "лекарств" или "препарат"
    if 'человеческ' in text_lower:
        human_idx = text_lower.find('человеческ')
        context_start = max(0, human_idx - 50)
        context_end = min(len(text_lower), human_idx + 150)
        context = text_lower[context_start:context_end]
        
        if 'лекарств' in context or 'препарат' in context:
            has_human_mention = True
            human_mention_index = human_idx
    
    if has_human_mention:
        context_start = max(0, human_mention_index - 100)
        context_end = min(len(text_lower), human_mention_index + 200)
        context = text_lower[context_start:context_end]
        
        warning_words = ['нельзя', 'не давайте', 'запрещено', 'токсичн', 'опасн', 'вредн', 'не следует']
        has_warning = any(w in context for w in warning_words)
        
        if not has_warning:
            issues.append("КРИТИЧЕСКАЯ ОШИБКА: Упомянуты человеческие лекарства/препараты без предупреждения!")
    
    # Проверяем наличие дисклеймера
    has_disclaimer = bool(re.search(r'(не\s+заменяет|требуется\s+консультаци|обратитесь\s+к\s+(ветеринар|врач))', text_lower))
    if not has_disclaimer:
        issues.append("Отсутствует обязательный медицинский дисклеймер")
    
    if issues:
        return False, "Найдены критические проблемы безопасности", issues
    return True, "Логическая и ветеринарная вменяемость подтверждена", []

def check_readability(parsed: Dict) -> Tuple[bool, str, List[str]]:
    issues = []
    
    long_sentences = [s for s in parsed["sentences"] if len(s.split()) > MAX_SENTENCE_LENGTH]
    if len(long_sentences) > 3:
        issues.append("Слишком много длинных предложений (>" + str(MAX_SENTENCE_LENGTH) + " слов): " + str(len(long_sentences)))
    
    long_paragraphs = [p for p in parsed["paragraphs"] if len(p.split()) > MAX_PARAGRAPH_LENGTH]
    if len(long_paragraphs) > 2:
        issues.append("Слишком много длинных абзацев (>" + str(MAX_PARAGRAPH_LENGTH) + " слов): " + str(len(long_paragraphs)))
    
    if issues:
        return False, "Низкая читабельность", issues
    return True, "Читабельность на отличном уровне", []

def generate_feedback(issues_dict: Dict) -> str:
    feedback = []
    for check_name, (passed, msg, issues) in issues_dict.items():
        if not passed:
            feedback.append("[" + check_name + "] " + msg)
            for issue in issues:
                feedback.append("  - " + issue)
    
    if not feedback:
        return "Текст идеален. Можно публиковать."
    
    return "ТРЕБУЕТСЯ ДОРАБОТКА:\n" + "\n".join(feedback) + "\n\nИНСТРУКЦИЯ ДЛЯ WRITER AI PRO: Исправь указанные выше замечания, сохраняя общую структуру и факты."

def run_chief_editor(filepath: Path = None):
    print("="*70)
    print("CHIEF EDITOR: ГЛАВНЫЙ РЕДАКТОР АВТОНОМНОЙ СИСТЕМЫ")
    print("="*70)
    print("Дата: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    if filepath is None:
        html_files = list(OUTPUT_DIR.glob("*.html"))
        if not html_files:
            print("HTML-файлы не найдены в " + str(OUTPUT_DIR))
            return
        filepath = max(html_files, key=lambda p: p.stat().st_mtime)
    
    print("Проверяем файл: " + str(filepath.name))
    
    parsed = parse_html(filepath)
    
    checks = {
        "Brand Voice": check_brand_voice(parsed),
        "Sanity Check": check_sanity(parsed),
        "Readability": check_readability(parsed)
    }
    
    all_passed = True
    print("\n" + "-"*70)
    print("РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
    print("-"*70)
    
    for check_name, (passed, msg, issues) in checks.items():
        icon = "OK" if passed else "FAIL"
        print("  [" + icon + "] " + check_name + ": " + msg)
        if not passed:
            all_passed = False
            for issue in issues:
                print("      - " + issue)
    
    print("-"*70)
    
    feedback = generate_feedback(checks)
    
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "file": str(filepath.name),
        "passed": all_passed,
        "checks": {k: {"passed": v[0], "message": v[1]} for k, v in checks.items()},
        "feedback": feedback
    }
    
    report_file = Path("data/chief_editor_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\nВЕРДИКТ ГЛАВНОГО РЕДАКТОРА:")
    if all_passed:
        print("ОДОБРЕНО. Контент готов к публикации или передаче в Linker AI v5.")
    else:
        print("ОТКЛОНЕНО. Отправляем на доработку в Writer AI Pro со следующим фидбеком:")
        print("\n" + feedback)
    
    print("\nОтчёт сохранён: " + str(report_file))
    print("="*70)

if __name__ == "__main__":
    run_chief_editor()
