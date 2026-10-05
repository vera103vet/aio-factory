import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/audit_ai_predictive.json")

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

# СУПЕРСИЛА 1: BLUF-Check (Прямой ответ в начале)
def check_bluf(text):
    first_300 = text[:300].lower()
    # Ищем маркеры прямого ответа: "это", "является", "включает", цифры, списки
    has_direct_answer = any(x in first_300 for x in ["это ", "является", "включает", "основные", "во-первых"])
    return {
        "has_bluf": has_direct_answer,
        "score": 20 if has_direct_answer else 0,
        "fix": "Добавьте чёткий, прямой ответ на главный вопрос в первом абзаце." if not has_direct_answer else "OK"
    }

# СУПЕРСИЛА 2: AI Snippet Readiness
def check_ai_readiness(soup, text):
    score = 0
    issues = []
    
    # 1. Структурированные списки (AI обожает списки)
    lists = soup.find_all(['ul', 'ol'])
    if len(lists) >= 2:
        score += 30
    else:
        issues.append("Мало структурированных списков (AI любит <ul>/<ol>)")
        
    # 2. Выделения ключевых терминов
    strong_tags = soup.find_all('strong')
    if len(strong_tags) >= 3:
        score += 20
    else:
        issues.append("Используйте <strong> для выделения ключевых терминов")
        
    # 3. Короткие абзацы (читаемость для AI и людей)
    paragraphs = soup.find_all('p')
    short_p = sum(1 for p in paragraphs if len(p.get_text()) < 300)
    if short_p >= 3:
        score += 20
    else:
        issues.append("Разбейте длинные абзацы на более короткие (до 300 символов)")
        
    # 4. Наличие определений (формат "Термин: определение")
    has_definitions = bool(re.search(r'\b\w+\s*[:—-]\s*\w+', text[:1000]))
    if has_definitions:
        score += 30
    else:
        issues.append("Добавьте чёткие определения ключевых терминов в начале текста")
        
    return {"score": score, "issues": issues}

# СУПЕРСИЛА 3: Citation Worthiness (Авторитетность для AI)
def check_citation_worthiness(text):
    authority_domains = ["wsava", "iris", "pubmed", "ncbi", "who.int", "avma"]
    found = [d for d in authority_domains if d in text.lower()]
    score = len(found) * 15
    return {
        "score": min(30, score),
        "found": found,
        "fix": "Добавьте ссылки на международные протоколы (WSAVA, IRIS) для повышения доверия AI." if not found else "OK"
    }

# СУПЕРСИЛА 4: Генератор готовых исправлений (Schema.org)
def generate_schema_snippet(site_name, url):
    return {
        "site": site_name,
        "snippet": f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "VeterinaryCare",
  "name": "103vet.by - {site_name}",
  "url": "{url}",
  "description": "Профессиональная ветеринарная помощь. Пространство спокойствия для людей и безопасности для животных."
}}
</script>"""
    }

# СУПЕРСИЛА 5: Предиктивный скоринг
def calculate_predictive_score(current_score, ai_score, bluf_score, cit_score, issues_count):
    # Максимальный бонус за AI-фичи = 100 баллов
    potential_bonus = (100 - ai_score) + (20 - bluf_score) + (30 - cit_score) + (issues_count * 5)
    potential_score = min(100, current_score + potential_bonus)
    return {
        "current": current_score,
        "potential": potential_score,
        "upside": potential_score - current_score
    }

def run_ai_audit():
    print("="*70)
    print("АГЕНТ AI-АУДИТА v3: ГОТОВНОСТЬ К ИИ И ПРЕДИКТИВНАЯ АНАЛИТИКА")
    print("="*70)
    
    sites = load_sites()
    registry = load_registry()
    results = []
    
    for key, cfg in sites.items():
        url = cfg.get('url')
        if not url: continue
        
        print(f"\nАнализ AI-готовности: {key.upper()}")
        html = fetch_html(url)
        if not html:
            continue
            
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        # Запускаем проверки
        bluf = check_bluf(text)
        ai_read = check_ai_readiness(soup, text)
        cit = check_citation_worthiness(text)
        schema_snippet = generate_schema_snippet(key, url)
        
        # Суммируем AI-оценку (макс 100)
        ai_total_score = bluf["score"] + ai_read["score"] + cit["score"]
        
        # Предикция (берём базовую оценку из предыдущего аудита как основу, здесь упрощённо 50 + ai)
        base_score = 50 
        predictive = calculate_predictive_score(base_score, ai_total_score, bluf["score"], cit["score"], len(ai_read["issues"]))
        
        all_issues = ai_read["issues"]
        if not bluf["has_bluf"]: all_issues.append(bluf["fix"])
        if not cit["found"]: all_issues.append(cit["fix"])
        
        results.append({
            "site": key,
            "url": url,
            "ai_readiness_score": ai_total_score,
            "bluf": bluf,
            "citation": cit,
            "predictive": predictive,
            "issues": all_issues,
            "fix_snippet": schema_snippet
        })
        
        print(f"  AI-готовность: {ai_total_score}/100")
        print(f"  Прогноз роста: {predictive['current']} -> {predictive['potential']} (+{predictive['upside']})")
        if not cit["found"]:
            print(f"  ⚠️ Нет ссылок на авторитеты (WSAVA/IRIS)")

    # Сохранение отчёта
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "AI Audit & Predictive v3.0",
        "summary": {
            "avg_ai_score": round(sum(r["ai_readiness_score"] for r in results) / len(results), 1) if results else 0,
            "total_potential_upside": sum(r["predictive"]["upside"] for r in results)
        },
        "sites": results
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        
    print("\n" + "="*70)
    print("СВОДНЫЙ AI-ОТЧЁТ")
    print("="*70)
    print(f"Средняя AI-готовность: {report['summary']['avg_ai_score']}/100")
    print(f"Суммарный потенциал роста сети: +{report['summary']['total_potential_upside']} баллов")
    print(f"\nГотовые сниппеты для исправления сохранены в JSON.")
    print(f"Файл отчёта: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit()
