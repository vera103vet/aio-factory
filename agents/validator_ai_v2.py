import json
import yaml
import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple

# Конфигурация
RULES_FILE = Path("config/seo_rules.yaml")
MAX_KEYWORD_DENSITY = 2.0  # Максимальная плотность ключа (%)


# Список стоп-слов (не считаются ключами)
STOP_WORDS = {'что', 'при', 'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'у', 'о', 'а', 'но', 'же', 'ли', 'бы', 'то', 'как', 'так', 'не', 'ни', 'да', 'или', 'если', 'когда', 'где', 'кто', 'что', 'какой', 'который', 'чей', 'сколько', 'почему', 'зачем', 'как', 'где', 'когда', 'почему'}

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
    """Парсит HTML и извлекает текст и структуру"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    
    return {
        "soup": soup,
        "text": text,
        "words": len(text.split()),
        "sentences": [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10],
        "headings": soup.find_all(['h1', 'h2', 'h3']),
        "links": soup.find_all('a', href=True),
        "images": soup.find_all('img'),
        "tables": soup.find_all('table'),
        "lists": soup.find_all(['ul', 'ol'])
    }

# --- МОДУЛИ ПРОВЕРКИ ---

def check_keyword_density(parsed: Dict, keywords: List[str]) -> Tuple[bool, str]:
    """Legacy SEO: проверка плотности ключевых слов (с учётом стоп-слов)"""
    text_lower = parsed["text"].lower()
    total_words = parsed["words"]
    
    issues = []
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        # Пропускаем стоп-слова
        if keyword_lower in STOP_WORDS or len(keyword_lower) <= 2:
            continue
        
        count = text_lower.count(keyword_lower)
        density = (count / total_words * 100) if total_words > 0 else 0
        
        if density > MAX_KEYWORD_DENSITY:
            issues.append(f"Переспам ключа '{keyword}': {density:.2f}% (максимум {MAX_KEYWORD_DENSITY}%)")
    
    if issues:
        return False, "; ".join(issues)
    return True, "Плотность ключей в норме"

def check_ai_readiness(parsed: Dict) -> Tuple[bool, str]:
    """AI-Readiness: BLUF, FAQ, Schema.org"""
    issues = []
    
    # BLUF-ответ в начале
    first_100_words = ' '.join(parsed["text"].split()[:100]).lower()
    bluf_markers = ['краткий ответ', 'основные', 'главные', 'включает']
    has_bluf = any(m in first_100_words for m in bluf_markers)
    if not has_bluf:
        issues.append("Нет BLUF-ответа в первых 100 словах")
    
    # FAQ-секция
    has_faq = bool(re.search(r'(faq|часто задаваем|вопрос.*ответ)', parsed["text"].lower()))
    if not has_faq:
        issues.append("Нет FAQ-секции")
    
    # Schema.org
    has_schema = bool(parsed["soup"].find('script', attrs={'type': 'application/ld+json'}))
    if not has_schema:
        issues.append("Нет Schema.org разметки")
    
    if issues:
        return False, "; ".join(issues)
    return True, "AI-Readiness проверки пройдены"

def check_emotional_resonance(parsed: Dict) -> Tuple[bool, str]:
    """Emotional Resonance (v13): эмпатия и сторителлинг"""
    text_lower = parsed["text"].lower()
    issues = []
    
    # Эмпатия
    empathy_markers = ['понимаем', 'ваш питомец', 'ваш любимец', 'беспокойство', 'тревога']
    empathy_count = sum(1 for m in empathy_markers if m in text_lower)
    if empathy_count < 2:
        issues.append(f"Низкая эмпатия: найдено только {empathy_count} маркеров (нужно ≥2)")
    
    # Сторителлинг
    story_markers = ['пациент', 'случай', 'история', 'обратился', 'привезли']
    story_count = sum(1 for m in story_markers if m in text_lower)
    if story_count < 1:
        issues.append("Нет сторителлинга (историй пациентов)")
    
    if issues:
        return False, "; ".join(issues)
    return True, "Эмоциональный резонанс на уровне"

def check_actionability(parsed: Dict) -> Tuple[bool, str]:
    """Actionability (v14): деревья решений, чек-листы"""
    text_lower = parsed["text"].lower()
    issues = []
    
    # Дерево решений (улучшенная проверка: "если" и "то" в одном предложении)
    sentences = re.split(r'[.!?]+', text_lower)
    has_decision_tree = False
    for sentence in sentences:
        if 'если' in sentence and ('то' in sentence or 'тогда' in sentence):
            has_decision_tree = True
            break
    
    if not has_decision_tree:
        issues.append("Нет дерева решений 'Если... то...'")
    
    # Чек-лист
    has_checklist = bool(re.search(r'(чек-лист|список|перечень)', text_lower))
    if not has_checklist:
        issues.append("Нет чек-листа действий")
    
    if issues:
        return False, "; ".join(issues)
    return True, "Практическая применимость на уровне"
def check_mobile_ux(parsed: Dict) -> Tuple[bool, str]:
    """Mobile UX (Device Analyst): tel:, viewport"""
    issues = []
    
    # Кликабельный телефон
    tel_links = [a for a in parsed["links"] if a.get('href', '').startswith('tel:')]
    if len(tel_links) == 0:
        issues.append("Нет кликабельного телефона (tel:)")
    
    # Viewport
    viewport = parsed["soup"].find('meta', attrs={'name': 'viewport'})
    if not viewport:
        issues.append("Нет meta viewport")
    
    if issues:
        return False, "; ".join(issues)
    return True, "Mobile UX проверки пройдены"

def check_ethical_compliance(parsed: Dict) -> Tuple[bool, str]:
    """Ethical Compliance (v15): дисклеймер, баланс"""
    text_lower = parsed["text"].lower()
    issues = []
    
    # YMYL-дисклеймер
    has_disclaimer = bool(re.search(r'(не\s+заменяет|требуется\s+консультаци|обратитесь\s+к\s+(ветеринар|врач))', text_lower))
    if not has_disclaimer:
        issues.append("Нет YMYL-дисклеймера")
    
    # Баланс рисков/пользы
    risk_markers = ['риск', 'побочн', 'противопоказан']
    benefit_markers = ['польза', 'эффективн', 'улучшен']
    has_risk = any(m in text_lower for m in risk_markers)
    has_benefit = any(m in text_lower for m in benefit_markers)
    
    if not (has_risk and has_benefit):
        issues.append("Нет баланса рисков и пользы")
    
    if issues:
        return False, "; ".join(issues)
    return True, "Этическое соответствие на уровне"

def check_brand_compliance(parsed: Dict) -> Tuple[bool, str]:
    """Проверка соответствия правилам бренда"""
    rules = load_rules()
    text_lower = parsed["text"].lower()
    issues = []
    
    # Запрещённые элементы
    for forbidden in rules.get("forbidden", []):
        if forbidden.lower() in text_lower:
            issues.append(f"Найден запрещённый элемент: '{forbidden}'")
    
    if issues:
        return False, "; ".join(issues)
    return True, "Правила бренда соблюдены"

# --- ГЛАВНАЯ ФУНКЦИЯ ВАЛИДАЦИИ ---

def validate_single_file(filepath: Path, keywords: List[str] = None) -> Dict:
    """Валидирует один HTML-файл по всем 7 критериям"""
    if not filepath.exists():
        return {"error": f"Файл не найден: {filepath}"}
    
    parsed = parse_html(filepath)
    
    # Если ключи не переданы, берём из названия файла
    if keywords is None:
        keywords = filepath.stem.replace("_", " ").split()[:3]
    
    # Запуск всех 7 проверок
    checks = {
        "keyword_density": check_keyword_density(parsed, keywords),
        "ai_readiness": check_ai_readiness(parsed),
        "emotional_resonance": check_emotional_resonance(parsed),
        "actionability": check_actionability(parsed),
        "mobile_ux": check_mobile_ux(parsed),
        "ethical_compliance": check_ethical_compliance(parsed),
        "brand_compliance": check_brand_compliance(parsed)
    }
    
    # Подсчёт результатов
    passed = sum(1 for v in checks.values() if v[0])
    total = len(checks)
    score = int(passed / total * 100)
    
    # Определение статуса
    if score >= 100:
        status = "PLATINUM — идеальный контент"
    elif score >= 85:
        status = "GOLD — высокое качество"
    elif score >= 70:
        status = "SILVER — хорошее качество"
    elif score >= 50:
        status = "BRONZE — требует доработки"
    else:
        status = "НЕ ПРОШЁЛ — критические проблемы"
    
    return {
        "file": str(filepath),
        "words": parsed["words"],
        "score": score,
        "status": status,
        "checks": {name: {"passed": ok, "message": msg} for name, (ok, msg) in checks.items()},
        "passed": passed,
        "total": total
    }

def run_validator_ai_v2(target_dir: Path = None):
    """Главная функция запуска валидатора"""
    from datetime import datetime
    
    print("="*70)
    print("🛡️ VALIDATOR AI v2: КОНТРОЛЬ КАЧЕСТВА НОВОГО ПОКОЛЕНИЯ")
    print("="*70)
    print(f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f" Проверок: 7 (Legacy SEO + AI-Readiness + Эмпатия + Действия + Mobile + Этика + Бренд)")
    
    # Определяем директорию для проверки
    if target_dir is None:
        target_dir = Path("data/generated_content")
    
    if not target_dir.exists():
        print(f"❌ Директория не найдена: {target_dir}")
        return
    
    # Находим все HTML-файлы
    html_files = list(target_dir.glob("*.html"))
    if not html_files:
        print(f"⚠️ HTML-файлы не найдены в {target_dir}")
        return
    
    print(f"📁 Найдено файлов для проверки: {len(html_files)}")
    
    results = []
    total_score = 0
    
    for filepath in html_files:
        print(f"\n{'='*70}")
        print(f"📄 Проверка: {filepath.name}")
        print(f"{'='*70}")
        
        result = validate_single_file(filepath)
        
        if "error" in result:
            print(f"  ❌ {result['error']}")
            continue
        
        results.append(result)
        total_score += result["score"]
        
        print(f"  📊 Скор: {result['score']}/100")
        print(f"  🏆 Статус: {result['status']}")
        print(f"  📝 Проверок пройдено: {result['passed']}/{result['total']}")
        
        # Детализация по каждой проверке
        for check_name, check_result in result["checks"].items():
            status_icon = "✅" if check_result["passed"] else "❌"
            print(f"    {status_icon} {check_name}: {check_result['message']}")
    
    # Итоговая статистика
    if results:
        avg_score = round(total_score / len(results), 1)
        platinum_count = sum(1 for r in results if r["score"] >= 100)
        gold_count = sum(1 for r in results if 85 <= r["score"] < 100)
        failed_count = sum(1 for r in results if r["score"] < 50)
        
        report = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "version": "Validator AI v2.0",
            "total_files": len(results),
            "average_score": avg_score,
            "platinum_count": platinum_count,
            "gold_count": gold_count,
            "failed_count": failed_count,
            "results": results
        }
        
        # Сохранение отчёта
        report_file = Path("data/validator_report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*70)
        print("🏆 СВОДНЫЙ ОТЧЁТ VALIDATOR AI v2")
        print("="*70)
        print(f" Средний скор: {avg_score}/100")
        print(f"🥇 PLATINUM: {platinum_count} файлов")
        print(f"🥈 GOLD: {gold_count} файлов")
        print(f"❌ НЕ ПРОШЛИ: {failed_count} файлов")
        print(f"\n📁 Полный отчёт сохранён: {report_file}")
        print("="*70)
    else:
        print("\n️ Нет результатов для сводного отчёта")

if __name__ == "__main__":
    run_validator_ai_v2()
