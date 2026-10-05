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
OUTPUT_FILE = Path("data/audit_ai_v4.json")

# База сущностей для ветеринарных тем (СУПЕРСИЛА 2)
ENTITY_DB = {
    "эпилепс": ["судорог", "припадк", "ЭЭГ", "фенобарбитал", "невролог", "антиконвульсант"],
    "почек": ["креатинин", "мочевин", "IRIS", "стади", "диет", "фосфор", "нефролог"],
    "онколог": ["биопси", "химиотерапи", "метастаз", "опухол", "гистологи", "стадировани"],
    "кардиолог": ["ЭКГ", "ЭХО", "аритми", "сердечн", "давлен", "кардиолог"],
    "ветеринар": ["осмотр", "диагноз", "лечени", "профилактик", "вакцин"]
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
        "links": soup.find_all('a', href=True),
        "images": soup.find_all('img')
    }

# СУПЕРСИЛА 1: INFORMATION GAIN SCORE
def check_information_gain(soup, text):
    score = 0
    unique_elements = []
    
    # Таблицы (уникальные данные)
    tables = soup.find_all('table')
    if tables:
        score += 25
        unique_elements.append(f"таблицы: {len(tables)}")
    
    # Списки с цифрами (чек-листы)
    numbered_lists = soup.find_all('ol')
    if numbered_lists:
        score += 20
        unique_elements.append(f"нумерованные списки: {len(numbered_lists)}")
    
    # Цитаты протоколов
    protocol_kw = ["протокол", "рекомендаци", "согласно", "исследовани"]
    has_protocols = any(kw in text.lower() for kw in protocol_kw)
    if has_protocols:
        score += 20
        unique_elements.append("ссылки на протоколы")
    
    # Уникальные данные (цифры, проценты, статистика)
    stats = re.findall(r'\d+[\.,]?\d*\s*%', text)
    if len(stats) >= 3:
        score += 15
        unique_elements.append(f"статистика: {len(stats)} значений")
    
    # Изображения с подписями
    figures = soup.find_all('figure')
    if figures:
        score += 10
        unique_elements.append(f"figure-элементы: {len(figures)}")
    
    # Нормализация до 100
    score = min(100, score)
    
    return {
        "score": score,
        "unique_elements": unique_elements,
        "fix": "Добавьте уникальные таблицы, чек-листы, статистику или цитаты протоколов" if score < 60 else "OK"
    }

# СУПЕРСИЛА 2: ENTITY CO-OCCURRENCE
def check_entity_cooccurrence(text, topic_keyword):
    topic_lower = topic_keyword.lower() if topic_keyword else ""
    
    # Находим релевантную группу сущностей
    relevant_entities = []
    for key, entities in ENTITY_DB.items():
        if key in topic_lower:
            relevant_entities = entities
            break
    
    if not relevant_entities:
        # Если тема не найдена в базе, используем общие ветеринарные сущности
        relevant_entities = ["диагноз", "лечение", "симптомы", "профилактика", "осмотр"]
    
    # Проверяем наличие сущностей в тексте
    text_lower = text.lower()
    found_entities = [e for e in relevant_entities if e in text_lower]
    missing_entities = [e for e in relevant_entities if e not in text_lower]
    
    # Оценка плотности сущностей
    entity_density = len(found_entities) / len(relevant_entities) * 100
    
    score = min(100, int(entity_density))
    
    return {
        "score": score,
        "found": found_entities,
        "missing": missing_entities,
        "expected": relevant_entities,
        "fix": f"Добавьте упоминания: {', '.join(missing_entities[:3])}" if missing_entities else "OK"
    }

# СУПЕРСИЛА 3: PROMPT-MATCH (BLUF-структура)
def check_prompt_match(text):
    # Берём первые 200 слов
    first_200_words = ' '.join(text.split()[:200])
    
    # Паттерн идеального ответа для ИИ
    # [Сущность] — это [Определение]. Основные признаки: [Список]
    has_definition = bool(re.search(r'\S+\s+—?\s*это\s+\S+', first_200_words))
    has_list = bool(re.search(r'[:\-]\s*\S+', first_200_words))
    has_structure = bool(re.search(r'(основн|главн|перв|ключев)', first_200_words.lower()))
    
    score = 0
    if has_definition: score += 40
    if has_list: score += 30
    if has_structure: score += 30
    
    # Генерируем идеальный вводный абзац если нужно
    generated_intro = None
    if score < 70:
        generated_intro = f'<p><strong>[Тема статьи]</strong> — это [определение]. Основные признаки включают: [список]. Согласно рекомендациям [авторитет], [факт].</p>'
    
    return {
        "score": score,
        "has_definition": has_definition,
        "has_list": has_list,
        "has_structure": has_structure,
        "generated_intro": generated_intro,
        "fix": "Переструктурируйте первый абзац по формуле: Определение + Список + Авторитет" if score < 70 else "OK"
    }

# СУПЕРСИЛА 4: ANTI-HALLUCINATION ANCHORS
def check_anti_hallucination_anchors(soup, text):
    # Ищем фактические утверждения без якорей доверия
    # Паттерн: "Согласно [источник], [факт]" или "[Факт] [ссылка]"
    
    # Находим все ссылки
    links = soup.find_all('a', href=True)
    authority_domains = ["wsava", "iris", "pubmed", "ncbi", "who.int", "avma"]
    
    authority_links = []
    for link in links:
        href = link.get('href', '').lower()
        for domain in authority_domains:
            if domain in href:
                authority_links.append({
                    "url": href,
                    "text": link.get_text().strip()[:50]
                })
                break
    
    # Проверяем, есть ли в тексте явные цитирования
    citation_patterns = [
        r'согласно\s+\S+',
        r'по\s+данным\s+\S+',
        r'исследовани[яе]\s+показал',
        r'рекомендаци[яи]\s+\S+'
    ]
    
    has_explicit_citations = any(re.search(p, text.lower()) for p in citation_patterns)
    
    score = 0
    if authority_links:
        score += len(authority_links) * 10
    if has_explicit_citations:
        score += 30
    
    score = min(100, score)
    
    return {
        "score": score,
        "authority_links": authority_links[:5],
        "has_explicit_citations": has_explicit_citations,
        "fix": "Добавьте явные цитирования: 'Согласно рекомендациям WSAVA (2025), [факт] [ссылка]'" if score < 50 else "OK"
    }

# СУПЕРСИЛА 5: VISION AI READINESS (Мультимодальная готовность)
def check_vision_ai_readiness(images):
    if not images:
        return {"score": 0, "total": 0, "with_good_alt": 0, "fix": "Добавьте изображения с богатыми описаниями"}
    
    total = len(images)
    good_alt_count = 0
    examples = []
    
    for img in images[:10]:  # Проверяем первые 10
        alt = img.get('alt', '').strip()
        
        # Хороший alt для Vision AI: длинный, контекстный, с деталями
        # Плохой alt: короткий, общий ("собака", "кот")
        if len(alt) > 30 and len(alt.split()) >= 5:
            good_alt_count += 1
            examples.append(alt[:80])
    
    score = int(good_alt_count / total * 100) if total > 0 else 0
    
    return {
        "score": score,
        "total": total,
        "with_good_alt": good_alt_count,
        "examples": examples[:3],
        "fix": "Улучшите alt-тексты: добавьте контекст, породу, действие (например: 'Щенок джек-рассел во время неврологического осмотра')" if score < 50 else "OK"
    }

# ГЛАВНАЯ ФУНКЦИЯ
def run_ai_audit_v4():
    print("="*70)
    print("АГЕНТ DEEP AI-AUDIT v4: ПРОДВИНУТЫЙ АНАЛИЗ AI-ГОТОВНОСТИ")
    print("="*70)
    
    sites = load_sites()
    registry = load_registry()
    
    # Создаём маппинг тем для сайтов
    site_topics = {}
    for topic in registry:
        site = topic.get("target_site", "")
        keyword = topic.get("primary_keyword", "")
        if site not in site_topics:
            site_topics[site] = []
        site_topics[site].append(keyword)
    
    print(f"Сайтов: {len(sites)} | Тем в реестре: {len(registry)}")
    
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
        topic_keyword = site_topics.get(key, [""])[0] if site_topics.get(key) else ""
        
        # Запускаем все 5 суперсил
        s1 = check_information_gain(parsed["soup"], parsed["text"])
        s2 = check_entity_cooccurrence(parsed["text"], topic_keyword)
        s3 = check_prompt_match(parsed["text"])
        s4 = check_anti_hallucination_anchors(parsed["soup"], parsed["text"])
        s5 = check_vision_ai_readiness(parsed["images"])
        
        # Общий AI-скор
        total_score = (s1["score"] + s2["score"] + s3["score"] + s4["score"] + s5["score"]) // 5
        
        # Вероятность цитирования ИИ
        citation_prob = min(100, (s2["score"] + s4["score"]) // 2)
        
        print(f"  Information Gain: {s1['score']}/100")
        print(f"  Entity Co-occurrence: {s2['score']}/100")
        print(f"  Prompt-Match: {s3['score']}/100")
        print(f"  Anti-Hallucination: {s4['score']}/100")
        print(f"  Vision AI: {s5['score']}/100")
        print(f"  ─────────────────")
        print(f"  ОБЩИЙ AI-СКОР: {total_score}/100")
        print(f"  Вероятность цитирования ИИ: {citation_prob}%")
        
        if s2["missing"]:
            print(f"  ⚠️ Недостают сущности: {', '.join(s2['missing'][:3])}")
        if s3["generated_intro"]:
            print(f"  💡 Сгенерированный вводный абзац: {s3['generated_intro'][:100]}...")
        if s4["fix"] != "OK":
            print(f"  ⚠️ {s4['fix']}")
        
        results.append({
            "site": key,
            "url": url,
            "topic": topic_keyword,
            "scores": {
                "information_gain": s1,
                "entity_cooccurrence": s2,
                "prompt_match": s3,
                "anti_hallucination": s4,
                "vision_ai": s5
            },
            "total_ai_score": total_score,
            "citation_probability": citation_prob
        })
    
    # Сохранение JSON-отчёта
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Deep AI-Audit v4.0",
        "summary": {
            "avg_ai_score": round(sum(r["total_ai_score"] for r in results) / len(results), 1) if results else 0,
            "avg_citation_prob": round(sum(r["citation_probability"] for r in results) / len(results), 1) if results else 0,
            "total_sites": len(results)
        },
        "sites": results
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print("СВОДНЫЙ DEEP AI-ОТЧЁТ")
    print("="*70)
    print(f"Средний AI-скор: {report['summary']['avg_ai_score']}/100")
    print(f"Средняя вероятность цитирования ИИ: {report['summary']['avg_citation_prob']}%")
    print(f"Проанализировано сайтов: {report['summary']['total_sites']}")
    print(f"\nПолный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit_v4()
