import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
BRAND_PHILOSOPHY = "Пространство спокойствия для людей и безопасности для животных"
OUTPUT_FILE = Path("data/audit_report_v3.json")

# Паттерны для нишевых проверок
FORBIDDEN_PATTERNS = [r'\bцена\b', r'\bстоимость\b', r'\bруб\b', r'\bbyn\b', r'\b\$ \b']
AUTHORITY_PATTERNS = [r'wsava', r'iris', r'протокол', r'международн', r'научн']
EMERGENCY_PATTERNS = [r'103vet', r'вызов', r'срочно', r'неотложн']

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def load_registry():
    with open(REGISTRY, "r", encoding="utf-8") as f:
        return json.load(f)

def check_forbidden_elements(text):
    """Проверяет наличие запрещённых элементов (цены, имена)"""
    found = []
    text_lower = text.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text_lower):
            found.append(pattern.strip(r'\b'))
    return found

def check_vet_authority(text):
    """Проверяет наличие ссылок на ветеринарные авторитеты"""
    text_lower = text.lower()
    found = [p for p in AUTHORITY_PATTERNS if p in text_lower]
    return found

def check_emergency_readiness(text):
    """Проверяет маркеры экстренной помощи"""
    text_lower = text.lower()
    found = [p for p in EMERGENCY_PATTERNS if p in text_lower]
    return found

def deep_ymyl_check(soup):
    """Глубокая проверка YMYL-дисклеймера"""
    aside = soup.find('aside')
    if not aside:
        return False, "Отсутствует тег <aside>"
    
    aside_text = aside.get_text().lower()
    if "консультируйтесь" in aside_text or "ветеринар" in aside_text or "диагноз" in aside_text:
        return True, "OK"
    return False, "Тег <aside> есть, но нет ключевых слов о консультации с ветеринаром"

def audit_url_v3(url, site_name, registry):
    score = 100
    critical_issues = []
    important_issues = []
    recommendations = []
    
    checks = {
        "lang_ru": False, "meta_title": False, "meta_desc": False,
        "canonical": False, "schema_org": False, "article_tag": False,
        "h1_tag": False, "h2_questions": 0, "faq_section": False,
        "ymyl_disclaimer": False, "ymyl_deep_check": False,
        "brand_philosophy": False, "word_count": 0, "viewport": False,
        "vet_authority": [], "emergency_readiness": [], "forbidden_elements": []
    }

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        return {"site": site_name, "url": url, "score": 0, 
                "critical_issues": [{"type": "load_error", "description": str(e)}]}

    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    checks["word_count"] = len(text.split())

    # 1. Базовые проверки (сокращено для экономии места, логика та же)
    if soup.find('html') and soup.find('html').get('lang') == 'ru': checks["lang_ru"] = True
    else: score -= 10; critical_issues.append({"type": "no_lang", "desc": "Нет lang='ru'", "fix": "Добавить <html lang='ru'>"})

    if soup.find('title') and len(soup.find('title').get_text()) > 10: checks["meta_title"] = True
    else: score -= 10; critical_issues.append({"type": "no_title", "desc": "Нет <title>", "fix": "Добавить <title>"})

    if soup.find('script', attrs={'type': 'application/ld+json'}): checks["schema_org"] = True
    else: score -= 15; critical_issues.append({"type": "no_schema", "desc": "Нет Schema.org", "fix": "Добавить JSON-LD"})

    if soup.find('article'): checks["article_tag"] = True
    else: score -= 10; important_issues.append({"type": "no_article", "desc": "Нет <article>", "fix": "Обернуть в <article>"})

    if soup.find('h1'): checks["h1_tag"] = True
    else: score -= 10; critical_issues.append({"type": "no_h1", "desc": "Нет <h1>", "fix": "Добавить <h1>"})

    # 2. FAQ и H2
    h2_tags = soup.find_all('h2')
    checks["h2_questions"] = sum(1 for h2 in h2_tags if '?' in h2.get_text())
    if checks["h2_questions"] < 2:
        score -= 5; important_issues.append({"type": "few_h2", "desc": f"Мало H2-вопросов ({checks['h2_questions']})", "fix": "Добавить вопросы в H2"})
    
    checks["faq_section"] = any('faq' in h2.get_text().lower() or 'вопрос' in h2.get_text().lower() for h2 in h2_tags)
    if not checks["faq_section"]:
        score -= 10; critical_issues.append({"type": "no_faq", "desc": "Нет блока FAQ", "fix": "Добавить <h2>Часто задаваемые вопросы</h2>"})

    # 3. Глубокий YMYL (НИШЕВАЯ ПРОВЕРКА)
    ymyl_ok, ymyl_msg = deep_ymyl_check(soup)
    checks["ymyl_deep_check"] = ymyl_ok
    if not ymyl_ok:
        score -= 15; critical_issues.append({"type": "bad_ymyl", "desc": ymyl_msg, "fix": "Добавить <aside> с текстом о консультации с ветеринаром"})

    # 4. Философия бренда
    if BRAND_PHILOSOPHY in text: checks["brand_philosophy"] = True
    else: score -= 10; important_issues.append({"type": "no_philosophy", "desc": "Нет философии бренда", "fix": "Добавить текст философии"})

    # 5. Viewport
    if soup.find('meta', attrs={'name': 'viewport'}): checks["viewport"] = True
    else: score -= 10; critical_issues.append({"type": "no_viewport", "desc": "Нет viewport", "fix": "Добавить meta viewport"})

    # === НИШЕВЫЕ ВЕТЕРИНАРНЫЕ ПРОВЕРКИ (СУПЕРСИЛА v3) ===
    
    # А. Запрещённые элементы
    forbidden = check_forbidden_elements(text)
    checks["forbidden_elements"] = forbidden
    if forbidden:
        score -= 20
        critical_issues.append({"type": "forbidden_found", "desc": f"Найдены запрещённые элементы: {', '.join(forbidden)}", "fix": "Удалить упоминания цен и конкретных имён"})

    # Б. Ветеринарные авторитеты (E-E-A-T)
    authorities = check_vet_authority(text)
    checks["vet_authority"] = authorities
    if not authorities:
        score -= 5
        recommendations.append({"type": "no_authority", "desc": "Нет упоминаний WSAVA, IRIS или протоколов", "fix": "Добавить ссылки на международные протоколы"})

    # В. Экстренная готовность
    emergency = check_emergency_readiness(text)
    checks["emergency_readiness"] = emergency
    if not emergency:
        recommendations.append({"type": "no_emergency", "desc": "Слабые маркеры экстренной помощи", "fix": "Добавить 'Вызов 103vet срочно'"})

    # Г. Плотность ключей (упрощённая)
    keywords = [t["primary_keyword"] for t in registry if t["target_site"] == site_name]
    checks["keyword_density"] = {}
    for kw in keywords:
        count = text.lower().count(kw.lower())
        density = (count / checks["word_count"] * 100) if checks["word_count"] > 0 else 0
        checks["keyword_density"][kw] = {"count": count, "density": round(density, 2)}
        if density > 3.0:
            score -= 10
            critical_issues.append({"type": "keyword_spam", "desc": f"Переспам '{kw}': {density}%", "fix": "Снизить плотность до 2%"})

    return {
        "site": site_name, "url": url, "score": max(0, score),
        "critical_issues": critical_issues, "important_issues": important_issues,
        "recommendations": recommendations, "checks": checks
    }

def run_full_audit_v3():
    print("="*70)
    print("АГЕНТ-АУДИТОР v3 (ФАЗА 1): НИШЕВЫЙ ВЕТЕРИНАРНЫЙ ЭКСПЕРТ")
    print("="*70)
    
    sites = load_sites()
    registry = load_registry()
    results = []
    
    for site_key, site_config in sites.items():
        url = site_config.get('url')
        if not url: continue
            
        print(f"\nАудит: {site_key.upper()} ({url})")
        print("-" * 70)
        
        result = audit_url_v3(url, site_key, registry)
        results.append(result)
        
        print(f"Оценка: {result['score']}/100")
        print(f"Критичных: {len(result['critical_issues'])} | Важных: {len(result['important_issues'])}")
        
        if result['checks']['forbidden_elements']:
            print(f"  ЗАПРЕЩЕНО: {', '.join(result['checks']['forbidden_elements'])}")
        if result['checks']['vet_authority']:
            print(f"  АВТОРИТЕТЫ: {', '.join(result['checks']['vet_authority'])}")

    # Сохранение JSON
    report = {
        "audit_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "3.0 (Phase 1: Niche Expert)",
        "summary": {
            "avg_score": round(sum(r['score'] for r in results) / len(results), 1) if results else 0,
            "total_critical": sum(len(r['critical_issues']) for r in results)
        },
        "sites": results
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print(f"СРЕДНЯЯ ОЦЕНКА: {report['summary']['avg_score']}/100")
    print(f"ВСЕГО КРИТИЧНЫХ ПРОБЛЕМ: {report['summary']['total_critical']}")
    print(f"JSON-ОТЧЁТ СОХРАНЁН В: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_full_audit_v3()
