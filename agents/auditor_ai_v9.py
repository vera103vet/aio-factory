import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/audit_ai_v9.json")

COMPETITORS = {
    "general": {"url": "https://vetline.by/", "name": "Ветлайн (General)"},
    "specialized": {"url": "https://animalhelp.by/", "name": "AnimalHelp (Specialized)"},
    "clinic": {"url": "https://vet.by/", "name": "Вет.by (Clinic)"}
}

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return None

def analyze_ai_readiness(html, url):
    if not html:
        return {"score": 0, "error": "Не удалось загрузить"}
    
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    score = 0
    features = []
    missing = []
    
    has_date = bool(re.search(r'202[5-6]|обновлено|дата', text, re.IGNORECASE))
    if has_date:
        score += 20
        features.append("Есть маркеры свежести/дат")
    else:
        missing.append("Нет дат публикации/обновления")
    
    has_schema = bool(soup.find('script', attrs={'type': 'application/ld+json'}))
    if has_schema:
        score += 20
        features.append("Есть Schema.org разметка")
    else:
        missing.append("Отсутствует Schema.org")
    
    has_auth = bool(re.search(r'wsava|iris|протокол', text, re.IGNORECASE))
    if has_auth:
        score += 20
        features.append("Есть ссылки на авторитеты (WSAVA/IRIS)")
    else:
        missing.append("Нет ссылок на ветеринарные авторитеты")
    
    has_tables = bool(soup.find('table'))
    if has_tables:
        score += 20
        features.append("Есть таблицы с данными")
    else:
        missing.append("Нет таблиц (низкий Information Gain)")
    
    word_count = len(text.split())
    if word_count >= 800:
        score += 20
        features.append(f"Глубокий контент ({word_count} слов)")
    elif word_count >= 500:
        score += 10
        features.append(f"Средний контент ({word_count} слов)")
    else:
        missing.append(f"Поверхностный контент ({word_count} слов)")
    
    return {
        "url": url,
        "score": score,
        "word_count": word_count,
        "features": features,
        "missing": missing
    }

# СУПЕРСИЛА 1: СКАНИРОВАНИЕ КОНКУРЕНТОВ
def scan_competitors():
    results = {}
    for key, comp in COMPETITORS.items():
        print(f"  Сканирование конкурента: {comp['name']} ({comp['url']})")
        html = fetch_html(comp['url'])
        if html:
            analysis = analyze_ai_readiness(html, comp['url'])
            results[key] = {
                "name": comp['name'],
                "analysis": analysis
            }
        else:
            results[key] = {
                "name": comp['name'],
                "error": "Сайт недоступен"
            }
    return results

# СУПЕРСИЛА 2: СРАВНИТЕЛЬНЫЙ AI-СКОРИНГ
def compare_with_competitors(our_sites_data, competitors_data):
    comparisons = []
    for site_key, our_data in our_sites_data.items():
        our_score = our_data.get("score", 0)
        best_competitor = None
        best_score = 0
        gaps = []
        
        for comp_key, comp_data in competitors_data.items():
            if "error" in comp_data:
                continue
            comp_score = comp_data["analysis"].get("score", 0)
            if comp_score > best_score:
                best_score = comp_score
                best_competitor = comp_data["name"]
            
            # Находим разрывы
            comp_features = set(comp_data["analysis"].get("features", []))
            our_features = set(our_data.get("features", []))
            missing = comp_features - our_features
            for m in missing:
                gaps.append({
                    "competitor": comp_data["name"],
                    "feature": m
                })
        
        comparisons.append({
            "our_site": site_key,
            "our_score": our_score,
            "best_competitor": best_competitor,
            "best_competitor_score": best_score,
            "gap": best_score - our_score,
            "gaps": gaps
        })
    
    return comparisons

# СУПЕРСИЛА 3: ПРОГНОЗ ПЕРЕХВАТА ТРАФИКА
def predict_traffic_capture(comparisons):
    predictions = []
    for comp in comparisons:
        gap = comp["gap"]
        if gap <= 0:
            status = "Мы лидируем"
            potential_gain = 0
        elif gap <= 20:
            status = "Легко догнать"
            potential_gain = 15
        elif gap <= 40:
            status = "Реально обогнать"
            potential_gain = 30
        else:
            status = "Требуется стратегия"
            potential_gain = 50
        
        predictions.append({
            "site": comp["our_site"],
            "current_gap": gap,
            "status": status,
            "potential_traffic_gain_percent": potential_gain,
            "actions_needed": len(comp["gaps"])
        })
    
    return predictions

# ГЛАВНАЯ ФУНКЦИЯ
def run_ai_audit_v9():
    print("="*70)
    print("АГЕНТ COMPETITIVE AI GAP ANALYSIS v9: СТРАТЕГИЧЕСКАЯ РАЗВЕДКА")
    print("="*70)
    
    sites = load_sites()
    print(f"Наших сайтов: {len(sites)}")
    print(f"Конкурентов для анализа: {len(COMPETITORS)}")
    
    # Шаг 1: Сканируем конкурентов
    print("\n" + "="*70)
    print("ШАГ 1: СКАНИРОВАНИЕ КОНКУРЕНТОВ")
    print("="*70)
    competitors_data = scan_competitors()
    
    for key, data in competitors_data.items():
        if "error" in data:
            print(f"  {data['name']}: {data['error']}")
        else:
            a = data["analysis"]
            print(f"  {data['name']}: AI-скор {a['score']}/100, слов: {a['word_count']}")
    
    # Шаг 2: Анализируем наши сайты
    print("\n" + "="*70)
    print("ШАГ 2: АНАЛИЗ НАШИХ САЙТОВ")
    print("="*70)
    our_sites_data = {}
    for key, cfg in sites.items():
        url = cfg.get('url')
        if not url:
            continue
        html = fetch_html(url)
        if html:
            analysis = analyze_ai_readiness(html, url)
            our_sites_data[key] = analysis
            print(f"  {key.upper()}: AI-скор {analysis['score']}/100")
    
    # Шаг 3: Сравнение
    print("\n" + "="*70)
    print("ШАГ 3: СРАВНИТЕЛЬНЫЙ АНАЛИЗ")
    print("="*70)
    comparisons = compare_with_competitors(our_sites_data, competitors_data)
    
    for comp in comparisons:
        print(f"\n  {comp['our_site'].upper()}:")
        print(f"    Наш скор: {comp['our_score']}")
        print(f"    Лучший конкурент: {comp['best_competitor']} ({comp['best_competitor_score']})")
        print(f"    Разрыв: {comp['gap']} баллов")
        if comp['gaps']:
            print(f"    Что нужно добавить:")
            for g in comp['gaps'][:3]:
                print(f"      - {g['feature']} (как у {g['competitor']})")
    
    # Шаг 4: Прогноз перехвата трафика
    print("\n" + "="*70)
    print("ШАГ 4: ПРОГНОЗ ПЕРЕХВАТА AI-ТРАФИКА")
    print("="*70)
    predictions = predict_traffic_capture(comparisons)
    
    for pred in predictions:
        status_icon = "✅" if pred["status"] == "Мы лидируем" else "⚠️"
        print(f"  {status_icon} {pred['site'].upper()}: {pred['status']}")
        print(f"     Потенциальный рост трафика: +{pred['potential_traffic_gain_percent']}%")
        print(f"     Действий нужно: {pred['actions_needed']}")
    
    # Сохранение JSON-отчёта
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Competitive AI Gap Analysis v9.0",
        "competitors": competitors_data,
        "our_sites": our_sites_data,
        "comparisons": comparisons,
        "predictions": predictions,
        "summary": {
            "avg_our_score": round(sum(d.get("score", 0) for d in our_sites_data.values()) / len(our_sites_data), 1) if our_sites_data else 0,
            "avg_competitor_score": round(sum(d["analysis"]["score"] for d in competitors_data.values() if "analysis" in d) / max(1, sum(1 for d in competitors_data.values() if "analysis" in d)), 1),
            "total_gaps": sum(len(c["gaps"]) for c in comparisons),
            "sites_leading": sum(1 for p in predictions if p["status"] == "Мы лидируем")
        }
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print("СВОДНЫЙ ОТЧЁТ COMPETITIVE GAP ANALYSIS v9")
    print("="*70)
    print(f"Средний AI-скор наших сайтов: {report['summary']['avg_our_score']}/100")
    print(f"Средний AI-скор конкурентов: {report['summary']['avg_competitor_score']}/100")
    print(f"Всего разрывов для закрытия: {report['summary']['total_gaps']}")
    print(f"Сайтов, где мы лидируем: {report['summary']['sites_leading']}")
    print(f"\nПолный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit_v9()
