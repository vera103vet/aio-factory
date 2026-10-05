import requests
from bs4 import BeautifulSoup
import json
import yaml
from pathlib import Path

SITES_FILE = Path("config/sites.yaml")
BRAND_PHILOSOPHY = "Пространство спокойствия для людей и безопасности для животных"

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def audit_url(url, site_name):
    """Проверяет одну страницу сайта на соответствие стандартам 2026"""
    score = 100
    issues = []
    checks = {
        "lang_ru": False,
        "meta_title": False,
        "meta_desc": False,
        "canonical": False,
        "schema_org": False,
        "article_tag": False,
        "h1_tag": False,
        "h2_questions": 0,
        "faq_section": False,
        "ymyl_disclaimer": False,
        "brand_philosophy": False,
        "word_count": 0
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        return {"site": site_name, "url": url, "score": 0, "issues": [f"Ошибка загрузки: {e}"], "checks": checks}

    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    checks["word_count"] = len(text.split())

    # 1. Язык
    html_tag = soup.find('html')
    if html_tag and html_tag.get('lang') == 'ru':
        checks["lang_ru"] = True
    else:
        score -= 10
        issues.append("Отсутствует или неверный атрибут lang='ru'")

    # 2. Мета-теги
    if soup.find('title') and len(soup.find('title').get_text()) > 10:
        checks["meta_title"] = True
    else:
        score -= 10
        issues.append("Отсутствует или слишком короткий <title>")

    if soup.find('meta', attrs={'name': 'description'}) and len(soup.find('meta', attrs={'name': 'description'}).get('content', '')) > 50:
        checks["meta_desc"] = True
    else:
        score -= 5
        issues.append("Отсутствует или слишком короткий meta description")

    if soup.find('link', attrs={'rel': 'canonical'}):
        checks["canonical"] = True
    else:
        score -= 5
        issues.append("Отсутствует canonical URL")

    # 3. Schema.org
    if soup.find('script', attrs={'type': 'application/ld+json'}):
        checks["schema_org"] = True
    else:
        score -= 15
        issues.append("Отсутствует микроразметка Schema.org (JSON-LD)")

    # 4. Семантика
    if soup.find('article'):
        checks["article_tag"] = True
    else:
        score -= 10
        issues.append("Отсутствует семантический тег <article>")

    if soup.find('h1'):
        checks["h1_tag"] = True
    else:
        score -= 10
        issues.append("Отсутствует заголовок <h1>")

    h2_tags = soup.find_all('h2')
    for h2 in h2_tags:
        if '?' in h2.get_text():
            checks["h2_questions"] += 1
    
    if checks["h2_questions"] < 2:
        score -= 5
        issues.append("Мало заголовков H2 в форме вопросов (рекомендуется 2+)")

    # 5. FAQ
    for h2 in h2_tags:
        if 'faq' in h2.get_text().lower() or 'вопрос' in h2.get_text().lower():
            checks["faq_section"] = True
            break
    if not checks["faq_section"]:
        score -= 10
        issues.append("Отсутствует блок FAQ (критично для AI-сниппетов)")

    # 6. YMYL Дисклеймер
    if soup.find('aside'):
        checks["ymyl_disclaimer"] = True
    else:
        score -= 10
        issues.append("Отсутствует YMYL-дисклеймер в теге <aside>")

    # 7. Философия бренда
    if BRAND_PHILOSOPHY in text:
        checks["brand_philosophy"] = True
    else:
        score -= 10
        issues.append("Не найдена философия бренда на странице")

    # 8. Длина текста
    if checks["word_count"] < 300:
        score -= 5
        issues.append(f"Текст слишком короткий ({checks['word_count']} слов, мин. 300)")

    return {
        "site": site_name,
        "url": url,
        "score": max(0, score),
        "issues": issues,
        "checks": checks
    }

def run_full_audit():
    print("="*70)
    print("АГЕНТ-АУДИТОР: ПРОВЕРКА САЙТОВ НА СООТВЕТСТВИЕ СТАНДАРТАМ 2026")
    print("="*70)
    
    sites = load_sites()
    results = []
    
    for site_key, site_config in sites.items():
        url = site_config.get('url')
        if not url:
            continue
            
        print(f"\nАудит: {site_key.upper()} ({url})")
        print("-" * 70)
        
        result = audit_url(url, site_key)
        results.append(result)
        
        print(f"Итоговая оценка: {result['score']}/100")
        print(f"Слов на странице: ~{result['checks']['word_count']}")
        
        if result['issues']:
            print(f"\nНайдено проблем ({len(result['issues'])}):")
            for issue in result['issues']:
                print(f"  - {issue}")
        else:
            print("  Отлично! Критических проблем не найдено.")

    # Итоговый сводный отчёт
    print("\n" + "="*70)
    print("СВОДНЫЙ ОТЧЁТ ПО ЭКОСИСТЕМЕ")
    print("="*70)
    
    avg_score = sum(r['score'] for r in results) / len(results) if results else 0
    print(f"Средняя оценка по сети: {avg_score:.1f}/100")
    
    best_site = max(results, key=lambda x: x['score'])
    worst_site = min(results, key=lambda x: x['score'])
    
    print(f"Лидер: {best_site['site']} ({best_site['score']}/100)")
    print(f"Требует внимания: {worst_site['site']} ({worst_site['score']}/100)")
    
    print("\nРЕКОМЕНДАЦИЯ:")
    if avg_score < 70:
        print("Срочно обновить шаблоны сайтов. Сгенерировать новый контент через writer.py и заменить текущий.")
    elif avg_score < 90:
        print("Есть потенциал для улучшения. Сфокусируйтесь на добавлении Schema.org и YMYL-дисклеймеров.")
    else:
        print("Отличная работа! Сайты готовы к масштабированию и AI-индексации.")

if __name__ == "__main__":
    run_full_audit()
