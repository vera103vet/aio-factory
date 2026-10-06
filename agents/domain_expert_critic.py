import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

KNOWLEDGE_BASE_DIR = Path("data/expert_knowledge")
REGISTRY_FILE = Path("data/topic_registry.json")
OUTPUT_DIR = Path("data/generated_content")

# === ЖЁСТКИЕ ПРАВИЛА КАТЕГОРИЗАЦИИ ===

HARD_RULES = {
    'nevrologiya': ['эпилепсия', 'судорог', 'приступ', 'нервн', 'паралич', 'инсульт'],
    'dietologiya': ['корм', 'питан', 'диет', 'рацион'],
    'khirurgiya': ['перелом', 'травм', 'операци', 'хирург'],
    'kardiologiya': ['сердц', 'карди', 'аритм'],
    'onkologiya': ['онколог', 'рак', 'опухоль', 'метастаз'],
    'dermatologiya': ['кож', 'зуд', 'шерст', 'аллерг', 'дермат'],
    'oftalmologiya': ['глаз', 'зрен', 'глауком'],
    'stomatologiya': ['зуб', 'пасть', 'десн'],
    'ginekologiya': ['течк', 'вязк', 'роды', 'беремен', 'стерилизац', 'пиометр'],
    'usyplenie': ['усыплен', 'эвтаназ', 'прощан'],
    'vakcinaciya': ['вакцин', 'прививк'],
    'parazitologiya': ['блох', 'клещ', 'гельминт', 'глист', 'паразит'],
    'geriatriya': ['пожил', 'сениор', 'старост'],
    'exotic': ['кролик', 'попугай', 'хомяк', 'черепах', 'экзот']
}

def determine_category(topic_name: str, text: str = "") -> str:
    topic_lower = topic_name.lower()
    # Жёсткие правила по названию темы
    for category, keywords in HARD_RULES.items():
        if any(kw in topic_lower for kw in keywords):
            return category
    # Если не нашли — по тексту
    text_lower = text.lower()
    for category, keywords in HARD_RULES.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return 'terapiya'

# === ЗАГРУЗКА БАЗЫ ЗНАНИЙ ===

def load_expert_rules(category: str) -> Dict:
    filepath = KNOWLEDGE_BASE_DIR / f"{category}.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"category": category, "category_ru": category, "verified_facts": [], "forbidden_outdated_advice": [], "mandatory_expert_nuances": [], "red_flags": [], "forbidden_claims": [], "current_protocols": []}

# === МОДУЛЬ 1: ПРОТОКОЛЫ ===

def check_protocol_compliance(text_lower: str, rules: Dict) -> Tuple[bool, List[str]]:
    issues = []
    for forbidden in rules.get("forbidden_outdated_advice", []):
        keywords = forbidden.split()[:3]
        if all(kw in text_lower for kw in keywords):
            issues.append("Устаревший совет: '" + forbidden + "'")
    return len(issues) == 0, issues

# === МОДУЛЬ 2: НЮАНСЫ (ГИБКИЙ ПОИСК) ===

def check_expert_nuances(text_lower: str, rules: Dict) -> Tuple[bool, List[str]]:
    missing = []
    for nuance in rules.get("mandatory_expert_nuances", []):
        all_words = [w for w in nuance.split() if len(w) > 4]
        found_count = 0
        for w in all_words:
            # Проверяем точное совпадение ИЛИ подстроку (для разных форм слов)
            if w in text_lower:
                found_count += 1
            else:
                # Проверяем, есть ли корень слова в тексте (первые 6 символов)
                root = w[:6] if len(w) > 6 else w
                if any(root in word for word in text_lower.split()):
                    found_count += 1
        if found_count < 2:
            missing.append("Отсутствует нюанс: '" + nuance + "'")
    return len(missing) == 0, missing

# === МОДУЛЬ 3: КРАСНЫЕ ФЛАГИ ===

def check_red_flags(text_lower: str, rules: Dict) -> Tuple[bool, List[str]]:
    issues = []
    for flag in rules.get("red_flags", []):
        keywords = flag.split()[:3]
        if all(kw in text_lower for kw in keywords):
            issues.append("КРАСНЫЙ ФЛАГ: '" + flag + "'")
    return len(issues) == 0, issues

# === МОДУЛЬ 4: ФАКТЧЕКИНГ ===

def check_facts(text_lower: str, rules: Dict) -> Tuple[bool, List[str]]:
    issues = []
    for forbidden in rules.get("forbidden_claims", []):
        keywords = forbidden.split()[:3]
        if all(kw in text_lower for kw in keywords):
            issues.append("ЗАПРЕЩЁННОЕ УТВЕРЖДЕНИЕ: '" + forbidden + "'")
    for fact in rules.get("verified_facts", []):
        claim = fact.get("claim", "").lower()
        is_true = fact.get("is_true", True)
        correction = fact.get("correction")
        claim_keywords = claim.split()[:4]
        found = all(kw in text_lower for kw in claim_keywords)
        if found and not is_true and correction:
            issues.append("ЛОЖНЫЙ ФАКТ: '" + claim + "' → " + correction)
    return len(issues) == 0, issues

# === ГЛАВНАЯ ФУНКЦИЯ ===

def run_expert_critique(topic_name: str, text: str) -> Dict:
    category = determine_category(topic_name, text)
    rules = load_expert_rules(category)
    text_lower = text.lower()
    
    c1_ok, c1_issues = check_protocol_compliance(text_lower, rules)
    c2_ok, c2_issues = check_expert_nuances(text_lower, rules)
    c3_ok, c3_issues = check_red_flags(text_lower, rules)
    c4_ok, c4_issues = check_facts(text_lower, rules)
    
    all_passed = c1_ok and c2_ok and c3_ok and c4_ok
    
    feedback = []
    if not c1_ok:
        feedback.extend(["[ПРОТОКОЛЫ] " + i for i in c1_issues])
    if not c2_ok:
        feedback.extend(["[ГЛУБИНА] " + i for i in c2_issues])
    if not c3_ok:
        feedback.extend(["[КРАСНЫЙ ФЛАГ] " + i for i in c3_issues])
    if not c4_ok:
        feedback.extend(["[ФАКТЧЕКИНГ] " + i for i in c4_issues])
    
    return {
        "category": category,
        "category_ru": rules.get("category_ru", category),
        "protocols_checked": rules.get("current_protocols", []),
        "passed": all_passed,
        "feedback": feedback if feedback else ["Экспертная проверка пройдена."]
    }

# === ЗАПУСК ===

def test_critic_on_latest_file():
    html_files = list(OUTPUT_DIR.glob("*.html"))
    if not html_files:
        print("Нет HTML файлов.")
        return
    
    filepath = max(html_files, key=lambda p: p.stat().st_mtime)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        text = re.sub(r'<[^>]+>', ' ', content)
    
    topic_name = filepath.stem.replace("_", " ").replace("?", "").strip()
    
    print("="*70)
    print("DOMAIN EXPERT CRITIC v2.0: ПРОВЕРКА ВЕТЕРИНАРНОЙ ЭКСПЕРТИЗЫ")
    print("="*70)
    print("Дата: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("Файл: " + filepath.name)
    print("Тема: " + topic_name)
    
    result = run_expert_critique(topic_name, text)
    
    print("\nКатегория: " + result['category_ru'].upper() + " (" + result['category'] + ")")
    print("Протоколы: " + ", ".join(result['protocols_checked']))
    print("-" * 70)
    print("РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
    print("-" * 70)
    
    if result['passed']:
        print("  [OK] Protocol Compliance")
        print("  [OK] Expert Nuances")
        print("  [OK] Red Flags")
        print("  [OK] Fact-Checking")
        print("\nВЕРДИКТ: ОДОБРЕНО ЭКСПЕРТОМ")
    else:
        print("  [" + ("OK" if all('ПРОТОКОЛЫ' not in i for i in result['feedback']) else "FAIL") + "] Protocol Compliance")
        print("  [" + ("OK" if all('ГЛУБИНА' not in i for i in result['feedback']) else "FAIL") + "] Expert Nuances")
        print("  [" + ("OK" if all('КРАСНЫЙ' not in i for i in result['feedback']) else "FAIL") + "] Red Flags")
        print("  [" + ("OK" if all('ФАКТЧЕКИНГ' not in i for i in result['feedback']) else "FAIL") + "] Fact-Checking")
        print("\nВЕРДИКТ: ТРЕБУЕТСЯ ДОРАБОТКА")
        for issue in result['feedback']:
            print("  - " + issue)
    
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "file": filepath.name,
        "topic": topic_name,
        "category": result['category'],
        "passed": result['passed'],
        "feedback": result['feedback']
    }
    report_file = Path("data/domain_expert_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\nОтчёт сохранён: " + str(report_file))
    print("="*70)

if __name__ == "__main__":
    test_critic_on_latest_file()
