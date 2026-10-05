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
OUTPUT_FILE = Path("data/network_audit_report.json")

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def load_registry():
    with open(REGISTRY, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_site_html(url):
    """Загружает HTML сайта"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"  Ошибка загрузки {url}: {e}")
        return None

def extract_keywords_from_html(html):
    """Извлекает ключевые слова из HTML"""
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True).lower()
    
    # Извлекаем фразы 2-4 слова
    words = re.findall(r'\b[а-яёa-z]{3,}\b', text)
    phrases = []
    for i in range(len(words) - 1):
        for length in [2, 3, 4]:
            if i + length <= len(words):
                phrase = ' '.join(words[i:i+length])
                phrases.append(phrase)
    
    return Counter(phrases)

def check_cannibalization(registry):
    """Проверяет каннибализацию ключей между сайтами"""
    issues = []
    keyword_sites = {}
    
    for topic in registry:
        keyword = topic["primary_keyword"].lower()
        site = topic["target_site"]
        
        if keyword not in keyword_sites:
            keyword_sites[keyword] = []
        keyword_sites[keyword].append(site)
    
    # Находим дубликаты
    for keyword, sites in keyword_sites.items():
        if len(sites) > 1:
            issues.append({
                "type": "cannibalization",
                "keyword": keyword,
                "sites": sites,
                "severity": "critical",
                "fix": f"Оставить тему только на одном сайте: {sites[0]}"
            })
    
    return issues

def analyze_cross_linking(sites_data):
    """Анализирует перелинковку между сайтами сети"""
    results = {}
    
    for site_key, data in sites_data.items():
        html = data.get("html")
        if not html:
            continue
        
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True)
        
        internal_links = []
        external_to_network = []
        
        for link in links:
            href = link['href']
            for other_site_key, other_data in sites_data.items():
                if other_site_key != site_key:
                    other_url = other_data.get("url", "")
                    if other_url and other_url in href:
                        external_to_network.append({
                            "target_site": other_site_key,
                            "url": href,
                            "text": link.get_text().strip()[:50]
                        })
        
        results[site_key] = {
            "links_to_network": len(external_to_network),
            "targets": external_to_network
        }
    
    return results

def check_content_uniqueness(sites_data):
    """Проверяет уникальность контента между сайтами"""
    issues = []
    site_texts = {}
    
    for site_key, data in sites_data.items():
        html = data.get("html")
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator=' ', strip=True).lower()
            site_texts[site_key] = text
    
    # Сравниваем попарно
    sites = list(site_texts.keys())
    for i in range(len(sites)):
        for j in range(i + 1, len(sites)):
            site1, site2 = sites[i], sites[j]
            text1, text2 = site_texts[site1], site_texts[site2]
            
            # Простая проверка: общие фразы 5+ слов
            words1 = set(re.findall(r'\b\w+\b', text1))
            words2 = set(re.findall(r'\b\w+\b', text2))
            common = words1 & words2
            
            similarity = len(common) / max(len(words1), len(words2)) * 100
            
            if similarity > 30:  # Порог 30%
                issues.append({
                    "type": "content_overlap",
                    "sites": [site1, site2],
                    "similarity": round(similarity, 1),
                    "severity": "warning",
                    "fix": f"Проверить уникальность контента между {site1} и {site2}"
                })
    
    return issues

def analyze_topic_hierarchy(registry, sites):
    """Анализирует правильность распределения тем по сайтам"""
    issues = []
    
    site_topics = {}
    for topic in registry:
        site = topic["target_site"]
        if site not in site_topics:
            site_topics[site] = []
        site_topics[site].append(topic["topic"])
    
    # Проверяем, что main сайт имеет ключевые коммерческие темы
    main_topics = site_topics.get("main", [])
    commercial_keywords = ["вызов", "ветеринар на дом", "минск", "103vet"]
    
    has_commercial = any(
        any(kw in topic.lower() for kw in commercial_keywords)
        for topic in main_topics
    )
    
    if not has_commercial and main_topics:
        issues.append({
            "type": "wrong_hierarchy",
            "description": "Основной сайт не содержит коммерческих тем",
            "severity": "critical",
            "fix": "Перенести коммерческие темы на main сайт"
        })
    
    # Проверяем, что спутники имеют экспертные темы
    for site_key in ["nevrolog", "usyplenie", "vetminsk"]:
        site_topics_list = site_topics.get(site_key, [])
        expert_keywords = ["хроническ", "онколог", "невролог", "кардиолог"]
        
        has_expert = any(
            any(kw in topic.lower() for kw in expert_keywords)
            for topic in site_topics_list
        )
        
        if not has_expert and site_topics_list:
            issues.append({
                "type": "weak_satellite",
                "site": site_key,
                "description": f"Сайт {site_key} не содержит экспертных тем",
                "severity": "warning",
                "fix": f"Добавить экспертные темы на {site_key}"
            })
    
    return issues

def run_network_audit():
    print("="*70)
    print("АГЕНТ-СЕТЕВОЙ АУДИТОР: АНАЛИЗ ЭКОСИСТЕМЫ САЙТОВ")
    print("="*70)
    
    sites = load_sites()
    registry = load_registry()
    
    print(f"\nЗагружено сайтов: {len(sites)}")
    print(f"Загружено тем в реестре: {len(registry)}")
    
    # 1. Загружаем HTML всех сайтов
    print("\nЗагрузка HTML сайтов...")
    sites_data = {}
    for site_key, site_config in sites.items():
        url = site_config.get('url')
        if url:
            print(f"  Загрузка {site_key}...")
            html = fetch_site_html(url)
            sites_data[site_key] = {"url": url, "html": html}
    
    # 2. Проверка каннибализации
    print("\nПроверка каннибализации ключей...")
    cannibalization_issues = check_cannibalization(registry)
    print(f"  Найдено проблем: {len(cannibalization_issues)}")
    
    # 3. Анализ перелинковки
    print("\nАнализ перелинковки между сайтами...")
    cross_linking = analyze_cross_linking(sites_data)
    for site_key, data in cross_linking.items():
        print(f"  {site_key}: {data['links_to_network']} ссылок на другие сайты сети")
    
    # 4. Проверка уникальности контента
    print("\nПроверка уникальности контента...")
    uniqueness_issues = check_content_uniqueness(sites_data)
    print(f"  Найдено проблем: {len(uniqueness_issues)}")
    
    # 5. Анализ иерархии тем
    print("\nАнализ иерархии тем...")
    hierarchy_issues = analyze_topic_hierarchy(registry, sites)
    print(f"  Найдено проблем: {len(hierarchy_issues)}")
    
    # Сохранение JSON-отчёта
    report = {
        "audit_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Network Audit v1.0",
        "summary": {
            "total_sites": len(sites_data),
            "total_topics": len(registry),
            "cannibalization_issues": len(cannibalization_issues),
            "uniqueness_issues": len(uniqueness_issues),
            "hierarchy_issues": len(hierarchy_issues)
        },
        "cannibalization": cannibalization_issues,
        "cross_linking": cross_linking,
        "uniqueness": uniqueness_issues,
        "hierarchy": hierarchy_issues
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Итоговый отчёт
    print("\n" + "="*70)
    print("СВОДНЫЙ ОТЧЁТ ПО СЕТИ")
    print("="*70)
    print(f"Каннибализация: {len(cannibalization_issues)} проблем")
    print(f"Уникальность контента: {len(uniqueness_issues)} проблем")
    print(f"Иерархия тем: {len(hierarchy_issues)} проблем")
    print(f"\nJSON-отчёт сохранён в: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_network_audit()
