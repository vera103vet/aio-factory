import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
BRAND_PHILOSOPHY = "Пространство спокойствия для людей и безопасности для животных"
OUTPUT_FILE = Path("data/audit_report.json")

STOP_WORDS = {"и", "в", "на", "с", "по", "для", "из", "к", "у", "о", "а", "но", "или", "что", "это", "так", "же", "вы", "мы", "они", "он", "она", "оно", "я", "ты", "не", "бы", "ли", "ни", "то", "как", "где", "когда", "если", "или", "а", "но", "да", "нет"}

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def load_registry():
    with open(REGISTRY, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_keyword_density(text, keywords):
    """Вычисляет плотность ключевых слов"""
    words = re.findall(r'\b\w+\b', text.lower())
    total_words = len([w for w in words if w not in STOP_WORDS and len(w) > 2])
    
    densities = {}
    for keyword in keywords:
        keyword_lower = keyword.lower()
        count = text.lower().count(keyword_lower)
        density = (count / total_words * 100) if total_words > 0 else 0
        densities[keyword] = {
            "count": count,
            "density": round(density, 2),
            "status": "ok" if density <= 2.5 else "warning" if density <= 4.0 else "critical"
        }
    
    return densities, total_words

def check_open_graph(soup):
    """Проверяет Open Graph теги"""
    og_tags = {
        "og:title": bool(soup.find('meta', attrs={'property': 'og:title'})),
        "og:description": bool(soup.find('meta', attrs={'property': 'og:description'})),
        "og:image": bool(soup.find('meta', attrs={'property': 'og:image'})),
        "og:url": bool(soup.find('meta', attrs={'property': 'og:url'})),
        "og:type": bool(soup.find('meta', attrs={'property': 'og:type'}))
    }
    return og_tags

def check_twitter_card(soup):
    """Проверяет Twitter Card теги"""
    twitter_tags = {
        "twitter:card": bool(soup.find('meta', attrs={'name': 'twitter:card'})),
        "twitter:title": bool(soup.find('meta', attrs={'name': 'twitter:title'})),
        "twitter:description": bool(soup.find('meta', attrs={'name': 'twitter:description'})),
        "twitter:image": bool(soup.find('meta', attrs={'name': 'twitter:image'}))
    }
    return twitter_tags

def check_images_alt(soup):
    """Проверяет alt-тексты изображений"""
    images = soup.find_all('img')
    total = len(images)
    with_alt = sum(1 for img in images if img.get('alt') and img.get('alt').strip())
    without_alt = total - with_alt
    
    return {
        "total": total,
        "with_alt": with_alt,
        "without_alt": without_alt,
        "percentage": round((with_alt / total * 100) if total > 0 else 0, 1)
    }

def check_internal_links(soup, base_url):
    """Проверяет внутреннюю перелинковку"""
    links = soup.find_all('a', href=True)
    internal = [l for l in links if base_url in l['href']]
    external = [l for l in links if base_url not in l['href'] and l['href'].startswith('http')]
    
    return {
        "total": len(links),
        "internal": len(internal),
        "external": len(external)
    }

def check_external_authority_links(soup):
    """Проверяет ссылки на авторитетные источники"""
    authority_domains = ["wsava.org", "iris-kidney.com", "ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov", "who.int", "avma.org"]
    links = soup.find_all('a', href=True)
    
    authority_links = []
    for link in links:
        href = link.get('href', '').lower()
        for domain in authority_domains:
            if domain in href:
                authority_links.append({"url": href, "text": link.get_text().strip()[:50]})
                break
    
    return authority_links

def audit_url_v2(url, site_name, registry):
    """Расширенная проверка страницы"""
    score = 100
    critical_issues = []
    important_issues = []
    recommendations = []
    
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
        "word_count": 0,
        "viewport": False,
        "open_graph": {},
        "twitter_card": {},
        "images_alt": {},
        "internal_links": {},
        "authority_links": [],
        "keyword_density": {}
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text
    except Exception as e:
        return {
            "site": site_name,
            "url": url,
            "score": 0,
            "critical_issues": [{"type": "load_error", "description": f"Ошибка загрузки: {e}", "fix": "Проверить доступность сайта"}],
            "important_issues": [],
            "recommendations": [],
            "checks": checks
        }

    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    checks["word_count"] = len(text.split())

    # 1. Базовые проверки
    html_tag = soup.find('html')
    if html_tag and html_tag.get('lang') == 'ru':
        checks["lang_ru"] = True
    else:
        score -= 10
        critical_issues.append({"type": "missing_lang", "description": "Отсутствует lang='ru'", "fix": "Добавить <html lang='ru'>", "impact": "+10"})

    if soup.find('title') and len(soup.find('title').get_text()) > 10:
        checks["meta_title"] = True
    else:
        score -= 10
        critical_issues.append({"type": "missing_title", "description": "Отсутствует <title>", "fix": "Добавить <title>Ключевая тема | 103vet.by</title>", "impact": "+10"})

    if soup.find('meta', attrs={'name': 'description'}) and len(soup.find('meta', attrs={'name': 'description'}).get('content', '')) > 50:
        checks["meta_desc"] = True
    else:
        score -= 5
        important_issues.append({"type": "missing_meta_desc", "description": "Короткий или отсутствующий meta description", "fix": "Добавить <meta name='description' content='...'> (150-160 символов)", "impact": "+5"})

    if soup.find('link', attrs={'rel': 'canonical'}):
        checks["canonical"] = True
    else:
        score -= 5
        important_issues.append({"type": "missing_canonical", "description": "Отсутствует canonical URL", "fix": "Добавить <link rel='canonical' href='URL'>", "impact": "+5"})

    # 2. Schema.org
    if soup.find('script', attrs={'type': 'application/ld+json'}):
        checks["schema_org"] = True
    else:
        score -= 15
        critical_issues.append({"type": "missing_schema", "description": "Отсутствует Schema.org JSON-LD", "fix": "Добавить <script type='application/ld+json'>{...}</script>", "impact": "+15"})

    # 3. Семантика
    if soup.find('article'):
        checks["article_tag"] = True
    else:
        score -= 10
        important_issues.append({"type": "missing_article", "description": "Отсутствует <article>", "fix": "Обернуть контент в <article>...</article>", "impact": "+10"})

    if soup.find('h1'):
        checks["h1_tag"] = True
    else:
        score -= 10
        critical_issues.append({"type": "missing_h1", "description": "Отсутствует <h1>", "fix": "Добавить <h1>Главный заголовок страницы</h1>", "impact": "+10"})

    h2_tags = soup.find_all('h2')
    for h2 in h2_tags:
        if '?' in h2.get_text():
            checks["h2_questions"] += 1
    
    if checks["h2_questions"] < 2:
        score -= 5
        important_issues.append({"type": "few_h2_questions", "description": f"Мало H2-вопросов ({checks['h2_questions']})", "fix": "Добавить 2-3 заголовка H2 в форме вопросов", "impact": "+5"})

    # 4. FAQ
    for h2 in h2_tags:
        if 'faq' in h2.get_text().lower() or 'вопрос' in h2.get_text().lower():
            checks["faq_section"] = True
            break
    if not checks["faq_section"]:
        score -= 10
        critical_issues.append({"type": "missing_faq", "description": "Отсутствует блок FAQ", "fix": "Добавить <section><h2>Часто задаваемые вопросы</h2>...</section>", "impact": "+10"})

    # 5. YMYL
    if soup.find('aside'):
        checks["ymyl_disclaimer"] = True
    else:
        score -= 10
        critical_issues.append({"type": "missing_ymyl", "description": "Отсутствует YMYL-дисклеймер", "fix": "Добавить <aside>Важно: консультируйтесь с ветеринаром...</aside>", "impact": "+10"})

    # 6. Философия бренда
    if BRAND_PHILOSOPHY in text:
        checks["brand_philosophy"] = True
    else:
        score -= 10
        important_issues.append({"type": "missing_philosophy", "description": "Нет философии бренда", "fix": "Добавить 'Пространство спокойствия для людей и безопасности для животных'", "impact": "+10"})

    # 7. Viewport (мобильная адаптивность)
    if soup.find('meta', attrs={'name': 'viewport'}):
        checks["viewport"] = True
    else:
        score -= 10
        critical_issues.append({"type": "missing_viewport", "description": "Отсутствует viewport meta tag", "fix": "Добавить <meta name='viewport' content='width=device-width, initial-scale=1.0'>", "impact": "+10"})

    # 8. Open Graph
    checks["open_graph"] = check_open_graph(soup)
    og_missing = [k for k, v in checks["open_graph"].items() if not v]
    if len(og_missing) > 2:
        score -= 5
        recommendations.append({"type": "missing_og", "description": f"Не хватает OG-тегов: {', '.join(og_missing)}", "fix": "Добавить Open Graph мета-теги", "impact": "+5"})

    # 9. Twitter Card
    checks["twitter_card"] = check_twitter_card(soup)
    tw_missing = [k for k, v in checks["twitter_card"].items() if not v]
    if len(tw_missing) > 2:
        recommendations.append({"type": "missing_twitter", "description": f"Не хватает Twitter-тегов: {', '.join(tw_missing)}", "fix": "Добавить Twitter Card мета-теги", "impact": "+3"})

    # 10. Изображения с alt
    checks["images_alt"] = check_images_alt(soup)
    if checks["images_alt"]["without_alt"] > 0:
        score -= 3
        important_issues.append({"type": "missing_alt", "description": f"{checks['images_alt']['without_alt']} изображений без alt", "fix": "Добавить alt='описание' ко всем <img>", "impact": "+3"})

    # 11. Внутренняя перелинковка
    checks["internal_links"] = check_internal_links(soup, url)
    if checks["internal_links"]["internal"] < 3:
        recommendations.append({"type": "few_internal_links", "description": f"Мало внутренних ссылок ({checks['internal_links']['internal']})", "fix": "Добавить 3-5 внутренних ссылок на связанные темы", "impact": "+5"})

    # 12. Ссылки на авторитеты
    checks["authority_links"] = check_external_authority_links(soup)
    if len(checks["authority_links"]) == 0:
        recommendations.append({"type": "no_authority_links", "description": "Нет ссылок на авторитеты (WSAVA, IRIS)", "fix": "Добавить ссылки на wsave.org", "impact": "+5 E-E-A-T"})

    # 13. Плотность ключевых слов
    keywords = [t["primary_keyword"] for t in registry if t["target_site"] == site_name]
    if keywords:
        densities, total_words = calculate_keyword_density(text, keywords)
        checks["keyword_density"] = densities
        
        for kw, data in densities.items():
            if data["status"] == "critical":
                score -= 10
                critical_issues.append({"type": "keyword_spam", "description": f"Переспам ключа '{kw}': {data['density']}%", "fix": "Снизить плотность до 2-2.5%", "impact": "+10"})
            elif data["status"] == "warning":
                important_issues.append({"type": "keyword_warning", "description": f"Высокая плотность '{kw}': {data['density']}%", "fix": "Рекомендуется снизить до 2%", "impact": "+5"})

    # Ограничение длины текста
    if checks["word_count"] < 300:
        score -= 5
        important_issues.append({"type": "short_content", "description": f"Текст короткий ({checks['word_count']} слов)", "fix": "Увеличить объём до 500+ слов", "impact": "+5"})

    return {
        "site": site_name,
        "url": url,
        "score": max(0, score),
        "critical_issues": critical_issues,
        "important_issues": important_issues,
        "recommendations": recommendations,
        "checks": checks
    }

def run_full_audit_v2():
    print("="*70)
    print("АГЕНТ-АУДИТОР v2: РАСШИРЕННАЯ ПРОВЕРКА С JSON-ОТЧЁТОМ")
    print("="*70)
    
    sites = load_sites()
    registry = load_registry()
    results = []
    
    for site_key, site_config in sites.items():
        url = site_config.get('url')
        if not url:
            continue
            
        print(f"\nАудит: {site_key.upper()} ({url})")
        print("-" * 70)
        
        result = audit_url_v2(url, site_key, registry)
        results.append(result)
        
        print(f"Оценка: {result['score']}/100")
        print(f"Слов: ~{result['checks']['word_count']}")
        print(f"Критичных проблем: {len(result['critical_issues'])}")
        print(f"Важных проблем: {len(result['important_issues'])}")
        print(f"Рекомендаций: {len(result['recommendations'])}")
        
        if result['checks']['keyword_density']:
            print("\nПлотность ключевых слов:")
            for kw, data in result['checks']['keyword_density'].items():
                status_icon = "OK" if data["status"] == "ok" else ("WARN" if data["status"] == "warning" else "CRIT")
                print(f"  [{status_icon}] '{kw}': {data['density']}% ({data['count']} вхождений)")

    # Сохраняем JSON-отчёт
    report = {
        "audit_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "auditor_version": "2.0",
        "summary": {
            "avg_score": round(sum(r['score'] for r in results) / len(results), 1) if results else 0,
            "best_site": max(results, key=lambda x: x['score'])['site'] if results else None,
            "worst_site": min(results, key=lambda x: x['score'])['site'] if results else None,
            "total_critical": sum(len(r['critical_issues']) for r in results),
            "total_important": sum(len(r['important_issues']) for r in results),
            "total_recommendations": sum(len(r['recommendations']) for r in results)
        },
        "sites": results
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Сводный отчёт
    print("\n" + "="*70)
    print("СВОДНЫЙ ОТЧЁТ ПО ЭКОСИСТЕМЕ")
    print("="*70)
    print(f"Средняя оценка: {report['summary']['avg_score']}/100")
    print(f"Лидер: {report['summary']['best_site']}")
    print(f"Требует внимания: {report['summary']['worst_site']}")
    print(f"Всего критичных проблем: {report['summary']['total_critical']}")
    print(f"Всего важных проблем: {report['summary']['total_important']}")
    print(f"Всего рекомендаций: {report['summary']['total_recommendations']}")
    print(f"\nJSON-отчёт сохранён в: {OUTPUT_FILE}")
    
    return report

if __name__ == "__main__":
    run_full_audit_v2()
