import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/audit_ai_v12.json")

# БАЗА ВЕТЕРИНАРНЫХ ТЕРМИНОВ С ЛОКАЛИЗАЦИЕЙ
VET_TERMS = {
    "эпилепсия": {"en": "epilepsy", "be": "эпілепсія", "difficulty": "low"},
    "судороги": {"en": "seizures", "be": "судоргі", "difficulty": "low"},
    "ХБП": {"en": "CKD (Chronic Kidney Disease)", "be": "ХНН", "difficulty": "high"},
    "фенобарбитал": {"en": "phenobarbital", "be": "фенобарбітал", "difficulty": "medium"},
    "IRIS": {"en": "IRIS", "be": "IRIS", "difficulty": "low"},
    "WSAVA": {"en": "WSAVA", "be": "WSAVA", "difficulty": "low"},
    "креатинин": {"en": "creatinine", "be": "крэатынін", "difficulty": "medium"},
    "мочевина": {"en": "urea", "be": "мачавіна", "difficulty": "medium"},
    "биопсия": {"en": "biopsy", "be": "біяпсія", "difficulty": "low"},
    "химиотерапия": {"en": "chemotherapy", "be": "хіміятэрапія", "difficulty": "medium"},
    "ЭЭГ": {"en": "EEG", "be": "ЭЭГ", "difficulty": "low"},
    "ЭКГ": {"en": "ECG", "be": "ЭКГ", "difficulty": "low"},
    "аритмия": {"en": "arrhythmia", "be": "арытмія", "difficulty": "medium"}
}

# КУЛЬТУРНЫЕ МАРКЕРЫ ДЛЯ РАЗНЫХ РЫНКОВ
CULTURAL_MARKERS = {
    "ru": ["вы", "ваш питомец", "ветеринар", "клиника", "Минск"],
    "en": ["you", "your pet", "veterinarian", "clinic", "Minsk"],
    "be": ["вы", "ваш хатні жывёла", "ветэрынар", "клініка", "Мінск"]
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
        "url": url,
        "sentences": [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10],
        "links": soup.find_all('a', href=True),
        "meta": soup.find_all('meta'),
        "html_tag": soup.find('html')
    }

# КРИТЕРИЙ 1: TRANSLATION READINESS SCORE (Готовность к переводу)
def check_translation_readiness(text, sentences):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Простые предложения (легче переводить)
    avg_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
    if avg_length <= 20:
        score += 25
        indicators.append(f"Короткие предложения (средн. {int(avg_length)} слов)")
    elif avg_length <= 30:
        score += 15
    
    # 2. Минимум идиом и сложных оборотов
    idioms = ['тем не менее', 'в свою очередь', 'имеет место', 'является собой']
    idiom_count = sum(1 for idiom in idioms if idiom in text_lower)
    if idiom_count <= 2:
        score += 20
        indicators.append("Минимум идиом")
    
    # 3. Явные связи между предложениями (потому что, поэтому, однако)
    connectors = ['потому что', 'поэтому', 'однако', 'кроме того', 'например', 'таким образом']
    conn_count = sum(1 for c in connectors if c in text_lower)
    if conn_count >= 3:
        score += 20
        indicators.append(f"Явные связки: {conn_count}")
    
    # 4. Отсутствие двусмысленностей (омонимов без контекста)
    ambiguous_words = ['лук', 'коса', 'норма', 'класс']
    ambiguous_count = sum(1 for w in ambiguous_words if w in text_lower.split())
    if ambiguous_count <= 1:
        score += 15
        indicators.append("Минимум двусмысленностей")
    
    # 5. Использование стандартной терминологии
    standard_terms = ['диагноз', 'лечение', 'симптомы', 'профилактика', 'осмотр']
    standard_count = sum(1 for t in standard_terms if t in text_lower)
    if standard_count >= 3:
        score += 20
        indicators.append(f"Стандартные термины: {standard_count}")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "avg_sentence_length": int(avg_length),
        "fix": "Упростите предложения, избегайте идиом, добавьте связки" if score < 50 else "OK"
    }

# КРИТЕРИЙ 2: ENTITY LOCALIZATION (Локализация сущностей)
def check_entity_localization(text):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # Проверяем наличие ветеринарных терминов из базы
    found_terms = []
    difficult_terms = []
    
    for term, data in VET_TERMS.items():
        if term.lower() in text_lower:
            found_terms.append(term)
            if data["difficulty"] == "high":
                difficult_terms.append(term)
    
    # Оценка: чем больше терминов с английскими аналогами, тем лучше
    if len(found_terms) >= 5:
        score += 30
        indicators.append(f"Вет. терминов: {len(found_terms)}")
    elif len(found_terms) >= 3:
        score += 15
    
    # Если есть сложные термины — проверяем, есть ли расшифровка
    if difficult_terms:
        # Проверяем, есть ли аббревиатуры с расшифровкой
        has_expansion = bool(re.search(r'\([А-ЯЁ]{2,}\)', text))
        if has_expansion:
            score += 20
            indicators.append("Сложные термины расшифрованы")
        else:
            indicators.append(f"Сложные термины без расшифровки: {difficult_terms[:3]}")
    
    # Наличие международных аббревиатур (IRIS, WSAVA, EEG, ECG)
    intl_abbrevs = ['IRIS', 'WSAVA', 'EEG', 'ECG', 'MRI', 'CT']
    found_intl = [a for a in intl_abbrevs if a in text]
    if len(found_intl) >= 2:
        score += 25
        indicators.append(f"Международные аббревиатуры: {', '.join(found_intl)}")
    elif len(found_intl) >= 1:
        score += 10
    
    # Английские термины в скобках (помогают переводчикам)
    en_in_brackets = re.findall(r'\([a-z]{3,}\)', text_lower)
    if len(en_in_brackets) >= 2:
        score += 15
        indicators.append(f"Английские термины в скобках: {len(en_in_brackets)}")
    
    return {
        "score": min(90, score),
        "indicators": indicators,
        "found_terms": found_terms[:5],
        "fix": "Добавьте международные аббревиатуры и расшифровки сложных терминов" if score < 40 else "OK"
    }

# КРИТЕРИЙ 3: CULTURAL ADAPTATION (Культурная адаптация)
def check_cultural_adaptation(text):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Нейтральность культурных отсылок
    # Избегаем специфических отсылок, непонятных за пределами региона
    culture_specific = ['наши бабушки', 'по старинке', 'у нас принято']
    cs_count = sum(1 for cs in culture_specific if cs in text_lower)
    if cs_count == 0:
        score += 25
        indicators.append("Культурно нейтральный контент")
    
    # 2. Универсальные единицы измерения (кг, см, °C, а не фунты/дюймы)
    universal_units = re.findall(r'\d+\s*(кг|см|мм|°C|мл|л)', text)
    if len(universal_units) >= 3:
        score += 20
        indicators.append(f"Универсальные единицы: {len(universal_units)}")
    
    # 3. Отсутствие региональных сленгов
    slang_markers = ['типа', 'короче', 'блин', 'прикинь']
    slang_count = sum(1 for s in slang_markers if s in text_lower)
    if slang_count == 0:
        score += 20
        indicators.append("Нет регионального сленга")
    
    # 4. Уважительное отношение к животным (важно для западных рынков)
    respect_markers = ['питомец', 'любимец', 'член семьи', 'друг']
    respect_count = sum(1 for m in respect_markers if m in text_lower)
    if respect_count >= 2:
        score += 15
        indicators.append(f"Уважительный тон: {respect_count} маркеров")
    
    # 5. Упоминание международных стандартов
    intl_standards = ['международный', 'мировой', 'глобальный', 'ISO', 'европейский']
    intl_count = sum(1 for s in intl_standards if s in text_lower)
    if intl_count >= 1:
        score += 10
        indicators.append("Упоминание международных стандартов")
    
    return {
        "score": min(90, score),
        "indicators": indicators,
        "fix": "Сделайте контент культурно нейтральным, используйте универсальные единицы" if score < 40 else "OK"
    }

# КРИТЕРИЙ 4: MULTILINGUAL SCHEMA.ORG (Мультиязычная разметка)
def check_multilingual_schema(parsed):
    score = 0
    indicators = []
    soup = parsed["soup"]
    
    # 1. Наличие hreflang-тегов (указание языковых версий)
    hreflangs = soup.find_all('link', attrs={'hreflang': True})
    if len(hreflangs) >= 2:
        score += 30
        indicators.append(f"hreflang-теги: {len(hreflangs)}")
    elif len(hreflangs) == 1:
        score += 10
        indicators.append("Есть hreflang (но мало)")
    
    # 2. Атрибут lang в html-теге
    html_tag = parsed["html_tag"]
    if html_tag and html_tag.get('lang'):
        score += 20
        indicators.append(f"lang-атрибут: {html_tag.get('lang')}")
    else:
        indicators.append("Отсутствует lang-атрибут в <html>")
    
    # 3. Schema.org с полем inLanguage
    has_schema = False
    has_inlanguage = False
    for script in soup.find_all('script', attrs={'type': 'application/ld+json'}):
        try:
            data = json.loads(script.get_text())
            has_schema = True
            if 'inLanguage' in data:
                has_inlanguage = True
        except:
            pass
    
    if has_schema and has_inlanguage:
        score += 25
        indicators.append("Schema.org с inLanguage")
    elif has_schema:
        score += 10
        indicators.append("Schema.org есть, но без inLanguage")
    else:
        indicators.append("Schema.org отсутствует")
    
    # 4. Meta-тег content-language
    content_lang = soup.find('meta', attrs={'http-equiv': 'content-language'})
    if content_lang:
        score += 15
        indicators.append("content-language мета-тег")
    
    # 5. OpenGraph с locale
    og_locale = soup.find('meta', attrs={'property': 'og:locale'})
    if og_locale:
        score += 10
        indicators.append(f"og:locale: {og_locale.get('content')}")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "has_schema": has_schema,
        "has_hreflang": len(hreflangs) > 0,
        "fix": "Добавьте hreflang, lang-атрибут и Schema.org с inLanguage" if score < 40 else "OK"
    }

# КРИТЕРИЙ 5: CROSS-LANGUAGE CITATION POTENTIAL (Потенциал кросс-языкового цитирования)
def check_cross_language_citation(text, parsed):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Наличие международных источников (домены .org, .edu, .int)
    intl_domains = ['.org', '.edu', '.int', 'who.int', 'pubmed', 'ncbi']
    found_intl = []
    for link in parsed["links"]:
        href = link.get('href', '').lower()
        for domain in intl_domains:
            if domain in href and domain not in found_intl:
                found_intl.append(domain)
                break
    if len(found_intl) >= 2:
        score += 25
        indicators.append(f"Международные домены: {', '.join(found_intl)}")
    elif len(found_intl) >= 1:
        score += 10
    
    # 2. Упоминание международных организаций
    intl_orgs = ['WHO', 'WOAH', 'OIE', 'FAO', 'UN', 'European', 'EU']
    org_count = sum(1 for org in intl_orgs if org in text)
    if org_count >= 2:
        score += 20
        indicators.append(f"Международные организации: {org_count}")
    
    # 3. DOI-ссылки на научные статьи
    doi_links = re.findall(r'doi\.org|10\.\d{4,}', text)
    if len(doi_links) >= 1:
        score += 20
        indicators.append(f"DOI-ссылки: {len(doi_links)}")
    
    # 4. Английские термины рядом с русскими (помогают ИИ-переводчикам)
    en_terms_nearby = re.findall(r'[а-яё]+\s+\([a-z]{3,}\)', text_lower)
    if len(en_terms_nearby) >= 2:
        score += 15
        indicators.append(f"Термины с английским аналогом: {len(en_terms_nearby)}")
    
    # 5. Универсальные факты (не зависят от региона)
    universal_facts = re.findall(r'\d+[\.,]?\d*\s*(%|мл|л|кг|°C|мм)', text)
    if len(universal_facts) >= 3:
        score += 15
        indicators.append(f"Универсальные факты с единицами: {len(universal_facts)}")
    
    # 6. Отсутствие региональных ограничений в тексте
    regional_limits = ['только в Беларуси', 'только для Минска', 'исключительно в РБ']
    has_limits = any(rl in text_lower for rl in regional_limits)
    if not has_limits:
        score += 5
        indicators.append("Нет региональных ограничений")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "fix": "Добавьте международные источники, DOI-ссылки и английские аналоги терминов" if score < 40 else "OK"
    }

# ИТОГОВЫЙ ПРОГНОЗ: МУЛЬТИЯЗЫЧНЫЙ ПОТЕНЦИАЛ
def predict_multilingual_potential(total_score):
    if total_score >= 80:
        tier = "PLATINUM — готов к глобальному AI-поиску"
        reach = "Глобальный (EN/RU/BE/DE/FR)"
    elif total_score >= 65:
        tier = "GOLD — высокий потенциал цитирования"
        reach = "Региональный (RU/BE/UK)"
    elif total_score >= 50:
        tier = "SILVER — стандартная готовность"
        reach = "Локальный (RU/BE)"
    elif total_score >= 35:
        tier = "BRONZE — требует локализации"
        reach = "Только RU"
    else:
        tier = "НЕ ГОТОВ для мультиязычного поиска"
        reach = "Изолированный"
    
    return {
        "tier": tier,
        "potential_reach": reach,
        "total_score": total_score
    }

# ГЛАВНАЯ ФУНКЦИЯ
def run_ai_audit_v12():
    print("="*70)
    print("АГЕНТ MULTI-LANGUAGE AI READINESS v12: МУЛЬТИЯЗЫЧНАЯ ГОТОВНОСТЬ")
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
        s1 = check_translation_readiness(parsed["text"], parsed["sentences"])
        s2 = check_entity_localization(parsed["text"])
        s3 = check_cultural_adaptation(parsed["text"])
        s4 = check_multilingual_schema(parsed)
        s5 = check_cross_language_citation(parsed["text"], parsed)
        total = (s1["score"] + s2["score"] + s3["score"] + s4["score"] + s5["score"]) // 5
        prediction = predict_multilingual_potential(total)
        print(f"  1. Готовность к переводу: {s1['score']}/100")
        print(f"  2. Локализация сущностей: {s2['score']}/90")
        print(f"  3. Культурная адаптация: {s3['score']}/90")
        print(f"  4. Мультиязычная разметка: {s4['score']}/100")
        print(f"  5. Кросс-языковое цитирование: {s5['score']}/100")
        print(f"  ─────────────────")
        print(f"  ОБЩИЙ ML-SCORE: {total}/100")
        print(f"  ТИР: {prediction['tier']}")
        print(f"  Потенциальный охват: {prediction['potential_reach']}")
        results.append({
            "site": key,
            "url": url,
            "scores": {
                "translation": s1,
                "localization": s2,
                "cultural": s3,
                "schema": s4,
                "cross_language": s5
            },
            "total_score": total,
            "prediction": prediction
        })
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Multi-Language AI Readiness v12.0",
        "summary": {
            "avg_score": round(sum(r["total_score"] for r in results) / len(results), 1) if results else 0,
            "total_sites": len(results),
            "platinum_sites": sum(1 for r in results if r["total_score"] >= 80),
            "gold_sites": sum(1 for r in results if 65 <= r["total_score"] < 80),
            "unsuitable_sites": sum(1 for r in results if r["total_score"] < 35)
        },
        "sites": results
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n" + "="*70)
    print("СВОДНЫЙ ОТЧЁТ MULTI-LANGUAGE AI READINESS v12")
    print("="*70)
    print(f"Средний ML-Score: {report['summary']['avg_score']}/100")
    print(f"PLATINUM (глобальный охват): {report['summary']['platinum_sites']} сайтов")
    print(f"GOLD (региональный охват): {report['summary']['gold_sites']} сайтов")
    print(f"НЕ ГОТОВ для мультиязычного поиска: {report['summary']['unsuitable_sites']} сайтов")
    print(f"\nПолный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit_v12()
