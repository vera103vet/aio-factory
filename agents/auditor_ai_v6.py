import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime, timedelta

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/audit_ai_v6.json")
CURRENT_YEAR = 2026

# Устаревшие термины/протоколы (сигналы устаревания)
OUTDATED_SIGNALS = {
    "2015": "протокол 2015 года",
    "2016": "протокол 2016 года",
    "2017": "протокол 2017 года",
    "2018": "протокол 2018 года",
    "2019": "протокол 2019 года",
    "2020": "протокол 2020 года",
    "устаревш": "устаревший подход",
    "ранее считалось": "устаревшее мнение",
    "традиционно применяли": "устаревшая практика"
}

# Маркеры актуальности
FRESHNESS_SIGNALS = [
    "по состоянию на 2026",
    "последние исследования",
    "современный протокол",
    "актуальные рекомендации",
    "обновлено",
    "2025",
    "2026"
]

# Авторитетные источники с датами обновлений
AUTHORITY_UPDATE_DATES = {
    "wsava": "2025-06",
    "iris": "2024-12",
    "avma": "2025-03",
    "who.int": "2025-01"
}

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def load_registry():
    with open(REGISTRY, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return None

def parse_site(html, url):
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    return {
        "soup": soup,
        "text": text,
        "words": len(text.split()),
        "url": url
    }

# СУПЕРСИЛА 1: ДЕТЕКТОР ДАТ ПУБЛИКАЦИИ
def detect_publication_dates(soup, text):
    dates_found = []
    
    # 1. Мета-теги
    for meta in soup.find_all('meta'):
        name = meta.get('name', '').lower()
        prop = meta.get('property', '').lower()
        content = meta.get('content', '')
        if 'date' in name or 'date' in prop:
            if content:
                dates_found.append({
                    "source": "meta",
                    "date": content,
                    "type": "publication"
                })
    
    # 2. Даты в тексте (форматы: 15.03.2026, 2026-03-15, март 2026)
    date_patterns = [
        r'\d{2}[./]\d{2}[./]\d{4}',
        r'\d{4}[./-]\d{2}[./-]\d{2}',
        r'(январь|февраль|март|апрель|май|июнь|июль|август|сентябрь|октябрь|ноябрь|декабрь)\s+20\d{2}',
        r'обновлено[:\s]+\d{2}[./]\d{2}[./]\d{4}'
    ]
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            dates_found.append({
                "source": "text",
                "date": m,
                "type": "mention"
            })
    
    # 3. Schema.org даты
    for script in soup.find_all('script', attrs={'type': 'application/ld+json'}):
        try:
            data = json.loads(script.get_text())
            if 'datePublished' in data:
                dates_found.append({
                    "source": "schema",
                    "date": data['datePublished'],
                    "type": "publication"
                })
            if 'dateModified' in data:
                dates_found.append({
                    "source": "schema",
                    "date": data['dateModified'],
                    "type": "modification"
                })
        except:
            pass
    
    return dates_found

# СУПЕРСИЛА 2: ОЦЕНКА СВЕЖЕСТИ
def evaluate_freshness(dates_found, text):
    if not dates_found:
        return {
            "score": 0,
            "status": "даты не найдены",
            "oldest": None,
            "newest": None,
            "age_days": None
        }
    
    # Ищем самую свежую дату
    years_found = []
    for d in dates_found:
        year_match = re.search(r'20\d{2}', d['date'])
        if year_match:
            years_found.append(int(year_match.group()))
    
    if not years_found:
        return {
            "score": 20,
            "status": "даты найдены, но год не определён",
            "oldest": None,
            "newest": None,
            "age_days": None
        }
    
    newest_year = max(years_found)
    age_years = CURRENT_YEAR - newest_year
    
    # Оценка свежести
    if age_years == 0:
        score = 100
        status = "актуальный контент"
    elif age_years == 1:
        score = 75
        status = "относительно свежий"
    elif age_years == 2:
        score = 50
        status = "требует обновления"
    else:
        score = 20
        status = "устаревший контент"
    
    return {
        "score": score,
        "status": status,
        "newest_year": newest_year,
        "age_years": age_years,
        "total_dates": len(dates_found)
    }

# СУПЕРСИЛА 3: ДЕТЕКТОР УСТАРЕВАНИЯ
def detect_outdated_content(text):
    issues = []
    text_lower = text.lower()
    for signal, description in OUTDATED_SIGNALS.items():
        if signal in text_lower:
            issues.append(description)
    return {
        "score": max(0, 100 - len(issues) * 25),
        "issues": issues,
        "fix": "Замените устаревшие упоминания на актуальные протоколы 2025-2026" if issues else "OK"
    }

# СУПЕРСИЛА 4: МАРКЕРЫ АКТУАЛЬНОСТИ
def check_freshness_signals(text):
    found = []
    text_lower = text.lower()
    for signal in FRESHNESS_SIGNALS:
        if signal in text_lower:
            found.append(signal)
    score = min(100, len(found) * 20)
    return {
        "score": score,
        "found": found,
        "fix": "Добавьте маркеры актуальности: 'по состоянию на 2026', 'обновлено', 'последние исследования'" if score < 60 else "OK"
    }

# СУПЕРСИЛА 5: ПРОГНОЗ СРОКА ГОДНОСТИ
def predict_content_lifespan(freshness_score, outdated_score, signals_score):
    avg = (freshness_score + outdated_score + signals_score) // 3
    if avg >= 80:
        lifespan_months = 18
        status = "долгосрочный контент"
    elif avg >= 60:
        lifespan_months = 12
        status = "средний срок"
    elif avg >= 40:
        lifespan_months = 6
        status = "требует скорого обновления"
    else:
        lifespan_months = 2
        status = "критически устарел"
    next_update = (datetime.now() + timedelta(days=lifespan_months*30)).strftime("%Y-%m-%d")
    return {
        "lifespan_months": lifespan_months,
        "status": status,
        "next_update_recommended": next_update,
        "avg_score": avg
    }

# ГЛАВНАЯ ФУНКЦИЯ
def run_ai_audit_v6():
    print("="*70)
    print("АГЕНТ TEMPORAL RELEVANCE v6: ОЦЕНКА СРОКА ГОДНОСТИ КОНТЕНТА")
    print("="*70)
    sites = load_sites()
    registry = load_registry()
    print(f"Сайтов: {len(sites)} | Тем: {len(registry)}")
    results = []
    for key, cfg in sites.items():
        url = cfg.get('url')
        if not url:
            continue
        print(f"\n{'='*70}")
        print(f"Анализ: {key.upper()} ({url})")
        print(f"{'='*70}")
        html = fetch_html(url)
        if not html:
            print(f"  Ошибка загрузки {url}")
            continue
        parsed = parse_site(html, url)
        dates = detect_publication_dates(parsed["soup"], parsed["text"])
        print(f"  Найдено дат: {len(dates)}")
        for d in dates[:3]:
            print(f"    - [{d['source']}] {d['date']} ({d['type']})")
        freshness = evaluate_freshness(dates, parsed["text"])
        print(f"  Свежесть: {freshness['score']}/100 ({freshness['status']})")
        outdated = detect_outdated_content(parsed["text"])
        print(f"  Актуальность: {outdated['score']}/100")
        if outdated['issues']:
            for issue in outdated['issues'][:3]:
                print(f"    ⚠️ {issue}")
        signals = check_freshness_signals(parsed["text"])
        print(f"  Маркеры актуальности: {signals['score']}/100")
        if signals['found']:
            print(f"    Найдено: {', '.join(signals['found'])}")
        lifespan = predict_content_lifespan(
            freshness['score'], outdated['score'], signals['score']
        )
        print(f"  Прогноз срока годности: {lifespan['lifespan_months']} мес.")
        print(f"  Статус: {lifespan['status']}")
        print(f"  След. обновление до: {lifespan['next_update_recommended']}")
        total_score = (freshness['score'] + outdated['score'] + signals['score']) // 3
        print(f"\n  ОБЩИЙ AI-СКОР v6: {total_score}/100")
        results.append({
            "site": key,
            "url": url,
            "dates_found": len(dates),
            "dates": dates[:5],
            "freshness": freshness,
            "outdated": outdated,
            "signals": signals,
            "lifespan": lifespan,
            "total_score": total_score
        })
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Temporal Relevance Audit v6.0",
        "summary": {
            "avg_score": round(sum(r["total_score"] for r in results) / len(results), 1) if results else 0,
            "total_sites": len(results),
            "sites_needing_update": sum(1 for r in results if r["total_score"] < 50)
        },
        "sites": results
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n" + "="*70)
    print("СВОДНЫЙ ОТЧЁТ TEMPORAL RELEVANCE v6")
    print("="*70)
    print(f"Средний AI-скор v6: {report['summary']['avg_score']}/100")
    print(f"Проанализировано сайтов: {report['summary']['total_sites']}")
    print(f"Требуют обновления: {report['summary']['sites_needing_update']}")
    print(f"\nПолный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit_v6()
