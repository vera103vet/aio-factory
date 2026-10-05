import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/network_audit_v2.json")

PHONE_PATTERNS = [
    r'\+?\d[\d\s\-\(\)]{7,}\d',
    r'8[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'
]
EMAIL_PATTERN = r'[\w\.-]+@[\w\.-]+\.\w+'
ADDRESS_KW = ['ул.', 'улица', 'пр.', 'проспект', 'дом', 'д.', 'кв.']

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
        print(f"  Ошибка {url}: {e}")
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
        "url": url,
        "links": soup.find_all('a', href=True)
    }

# СУПЕРСИЛА 1: АНАЛИЗ СИЛЫ САЙТА
def analyze_strength(sites_parsed, sites_cfg):
    results = {}
    for key, data in sites_parsed.items():
        if not data:
            continue
        outgoing = 0
        for link in data["links"]:
            href = link.get('href', '')
            for ok, od in sites_cfg.items():
                ou = od.get('url', '')
                if ok != key and ou and ou in href:
                    outgoing += 1
        results[key] = {
            "outgoing": outgoing,
            "incoming": 0,
            "role": "unknown",
            "strength": 0
        }
    for key, data in results.items():
        inc = 0
        for ok, od in results.items():
            if ok != key:
                op = sites_parsed.get(ok)
                if op:
                    for link in op["links"]:
                        href = link.get('href', '')
                        ku = sites_cfg[key].get('url', '')
                        if ku and ku in href:
                            inc += 1
        data["incoming"] = inc
        out = data["outgoing"]
        if out > 3 and inc > 3:
            data["role"] = "ХАБ"
            data["strength"] = 90
        elif out > inc:
            data["role"] = "ДОНОР"
            data["strength"] = 70 + min(out, 30)
        elif inc > out:
            data["role"] = "АКЦЕПТОР"
            data["strength"] = 50 + min(inc, 40)
        else:
            data["role"] = "СИРОТА"
            data["strength"] = 15
    return results

# СУПЕРСИЛА 3: МОСТОВЫЕ СТРАНИЦЫ
def analyze_bridges(sites_parsed, sites_cfg):
    results = {}
    for key, data in sites_parsed.items():
        if not data:
            continue
        bridges = []
        for link in data["links"]:
            href = link.get('href', '')
            linked = []
            for ok, od in sites_cfg.items():
                if ok != key:
                    ou = od.get('url', '')
                    if ou and ou in href:
                        linked.append(ok)
            if linked:
                bridges.append({
                    "url": href[:80],
                    "text": link.get_text().strip()[:40],
                    "to": linked
                })
        results[key] = {
            "count": len(bridges),
            "bridges": bridges[:5]
        }
    return results

# СУПЕРСИЛА 4: КОНСИСТЕНТНОСТЬ БРЕНДА
def check_brand(sites_parsed):
    data = {}
    for key, p in sites_parsed.items():
        if not p:
            continue
        text = p["text"]
        phones = set()
        for pat in PHONE_PATTERNS:
            phones.update(re.findall(pat, text))
        emails = set(re.findall(EMAIL_PATTERN, text))
        addr = ""
        for kw in ADDRESS_KW:
            if kw in text.lower():
                idx = text.lower().find(kw)
                s = max(0, idx - 30)
                e = min(len(text), idx + 50)
                addr = text[s:e].strip()
                break
        data[key] = {
            "phones": list(phones)[:3],
            "emails": list(emails)[:3],
            "addr": addr[:80]
        }
    issues = []
    keys = list(data.keys())
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            k1, k2 = keys[i], keys[j]
            d1, d2 = data[k1], data[k2]
            if d1["phones"] and d2["phones"]:
                common = set(d1["phones"]) & set(d2["phones"])
                if not common:
                    issues.append({
                        "type": "phone_mismatch",
                        "sites": [k1, k2],
                        "fix": "Унифицировать телефоны"
                    })
    return data, issues

# СУПЕРСИЛА 6: ГЛУБИНА КОНТЕНТА
def check_depth(sites_parsed):
    results = {}
    for key, p in sites_parsed.items():
        if not p:
            continue
        w = p["words"]
        if w >= 800:
            level, score = "ГЛУБОКИЙ", 100
        elif w >= 500:
            level, score = "СРЕДНИЙ", 70
        elif w >= 300:
            level, score = "ПОВЕРХНОСТНЫЙ", 40
        else:
            level, score = "КРИТИЧЕСКИ МАЛО", 10
        results[key] = {
            "words": w,
            "level": level,
            "score": score
        }
    return results

# СУПЕРСИЛА 7: СВЕЖЕСТЬ
def check_freshness(sites_parsed):
    results = {}
    date_pat = r'\d{2}[./]\d{2}[./]\d{4}|\d{4}[./]\d{2}[./]\d{2}'
    for key, p in sites_parsed.items():
        if not p:
            continue
        soup = p["soup"]
        meta_date = None
        for meta in soup.find_all('meta'):
            n = meta.get('name', '').lower()
            pr = meta.get('property', '').lower()
            if 'date' in n or 'date' in pr:
                meta_date = meta.get('content')
                break
        text_dates = re.findall(date_pat, p["text"])
        if meta_date:
            status = "есть мета-дата"
        elif text_dates:
            status = "даты в тексте"
        else:
            status = "даты не найдены"
        results[key] = {
            "meta_date": meta_date,
            "text_dates": text_dates[:3],
            "status": status
        }
    return results

# СУПЕРСИЛА 2: СИРОТСКИЕ СТРАНИЦЫ
def find_orphans(sites_parsed, sites_cfg):
    all_urls = {}
    for key, p in sites_parsed.items():
        if not p:
            continue
        for link in p["links"]:
            href = link.get('href', '')
            if href.startswith('http'):
                all_urls[href] = all_urls.get(href, 0) + 1
    orphans = []
    for key, p in sites_parsed.items():
        if not p:
            continue
        ku = sites_cfg[key].get('url', '')
        if ku and ku not in all_urls:
            orphans.append({
                "site": key,
                "url": ku,
                "fix": "Добавить ссылки на эту страницу из других сайтов"
            })
    return orphans

# СУПЕРСИЛА 5: ТЕМ. КЛАСТЕРЫ
def analyze_clusters(registry, sites_cfg):
    clusters = {}
    for key in sites_cfg:
        topics = [t for t in registry if t.get("target_site") == key]
        if not topics:
            clusters[key] = {"hub": None, "spokes": 0, "status": "пусто"}
            continue
        hub = topics[0]["topic"]
        spokes = len(topics) - 1
        if spokes >= 2:
            status = "сильный кластер"
        elif spokes == 1:
            status = "слабый кластер"
        else:
            status = "нет кластера"
        clusters[key] = {
            "hub": hub,
            "spokes": spokes,
            "status": status
        }
    return clusters

# СУПЕРСИЛА 8: ЛОКАЛЬНОЕ SEO (NAP)
def check_nap(sites_parsed):
    results = {}
    for key, p in sites_parsed.items():
        if not p:
            continue
        text = p["text"]
        phones = set()
        for pat in PHONE_PATTERNS:
            phones.update(re.findall(pat, text))
        emails = set(re.findall(EMAIL_PATTERN, text))
        addr = ""
        for kw in ADDRESS_KW:
            if kw in text.lower():
                idx = text.lower().find(kw)
                s = max(0, idx - 30)
                e = min(len(text), idx + 50)
                addr = text[s:e].strip()
                break
        results[key] = {
            "phones": list(phones)[:3],
            "emails": list(emails)[:3],
            "addr": addr[:80]
        }
    issues = []
    keys = list(results.keys())
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            k1, k2 = keys[i], keys[j]
            p1, p2 = results[k1], results[k2]
            if p1["phones"] and p2["phones"]:
                common = set(p1["phones"]) & set(p2["phones"])
                if not common:
                    issues.append({
                        "type": "phone_mismatch",
                        "sites": [k1, k2],
                        "fix": "Унифицировать телефоны"
                    })
            if p1["addr"] and p2["addr"]:
                if p1["addr"] != p2["addr"]:
                    issues.append({
                        "type": "addr_mismatch",
                        "sites": [k1, k2],
                        "fix": "Унифицировать адрес"
                    })
    return results, issues

# СУПЕРСИЛА 9: КОНВЕРСИЯ
def check_conversion(sites_parsed):
    cta_kw = ['позвонить', 'записаться', 'заказать', 'форма', 'callback']
    form_kw = ['<form', 'input', 'textarea']
    results = {}
    for key, p in sites_parsed.items():
        if not p:
            continue
        soup = p["soup"]
        text = p["text"].lower()
        has_cta = any(kw in text for kw in cta_kw)
        has_form = any(kw in str(soup).lower() for kw in form_kw)
        has_phone = bool(re.search(r'\+?\d[\d\s\-]{7,}', text))
        score = sum([has_cta, has_form, has_phone]) * 33
        results[key] = {
            "cta": has_cta,
            "form": has_form,
            "phone": has_phone,
            "score": min(100, score)
        }
    return results

# СУПЕРСИЛА 10: СТРУКТ. ДАННЫЕ
def check_schema(sites_parsed):
    types = ["Organization", "LocalBusiness", "Article", "FAQPage", "VeterinaryCare"]
    results = {}
    for key, p in sites_parsed.items():
        if not p:
            continue
        soup = p["soup"]
        scripts = soup.find_all('script', attrs={'type': 'application/ld+json'})
        found = []
        for s in scripts:
            content = s.get_text().lower()
            for t in types:
                if t.lower() in content and t not in found:
                    found.append(t)
        results[key] = {
            "found": found,
            "missing": [t for t in types if t not in found],
            "score": len(found) * 20
        }
    return results

# ГЛАВНАЯ ФУНКЦИЯ
def run_network_audit_v2():
    print("="*70)
    print("АГЕНТ-СЕТЕВОЙ АУДИТОР v2: 10 СУПЕРСИЛ")
    print("="*70)
    sites_cfg = load_sites()
    registry = load_registry()
    print(f"Сайтов: {len(sites_cfg)} | Тем: {len(registry)}")
    sites_parsed = {}
    for key, cfg in sites_cfg.items():
        url = cfg.get('url')
        if url:
            print(f"Загрузка {key}...")
            html = fetch_html(url)
            sites_parsed[key] = parse_site(html, url)
    r1 = analyze_strength(sites_parsed, sites_cfg)
    r2 = find_orphans(sites_parsed, sites_cfg)
    r3 = analyze_bridges(sites_parsed, sites_cfg)
    r4_data, r4_issues = check_brand(sites_parsed)
    r5 = analyze_clusters(registry, sites_cfg)
    r6 = check_depth(sites_parsed)
    r7 = check_freshness(sites_parsed)
    r8_data, r8_issues = check_nap(sites_parsed)
    r9 = check_conversion(sites_parsed)
    r10 = check_schema(sites_parsed)
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Network Audit v2.0",
        "strength": r1,
        "orphans": r2,
        "bridges": r3,
        "brand": {"data": r4_data, "issues": r4_issues},
        "clusters": r5,
        "depth": r6,
        "freshness": r7,
        "nap": {"data": r8_data, "issues": r8_issues},
        "conversion": r9,
        "schema": r10
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n" + "="*70)
    print("СВОДНЫЙ ОТЧЁТ")
    print("="*70)
    print("\n1. СИЛА САЙТОВ:")
    for k, v in r1.items():
        print(f"  {k}: {v['role']} (сила {v['strength']}, исх:{v['outgoing']}, вх:{v['incoming']})")
    print(f"\n2. СИРОТЫ: {len(r2)}")
    for o in r2:
        print(f"  - {o['site']}: {o['url']}")
    print("\n3. МОСТЫ:")
    for k, v in r3.items():
        print(f"  {k}: {v['count']} мостов")
    print(f"\n4. БРЕНД: {len(r4_issues)} проблем")
    print("\n5. КЛАСТЕРЫ:")
    for k, v in r5.items():
        print(f"  {k}: {v['status']} (хаб: {v['hub']}, лучей: {v['spokes']})")
    print("\n6. ГЛУБИНА:")
    for k, v in r6.items():
        print(f"  {k}: {v['level']} ({v['words']} слов)")
    print("\n7. СВЕЖЕСТЬ:")
    for k, v in r7.items():
        print(f"  {k}: {v['status']}")
    print(f"\n8. NAP: {len(r8_issues)} проблем")
    print("\n9. КОНВЕРСИЯ:")
    for k, v in r9.items():
        print(f"  {k}: CTA={v['cta']}, форма={v['form']}, тел={v['phone']} ({v['score']}%)")
    print("\n10. SCHEMA:")
    for k, v in r10.items():
        print(f"  {k}: найдено {v['found']}, нет {v['missing']}")
    print(f"\nJSON сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_network_audit_v2()
