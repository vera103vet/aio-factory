import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime, timedelta

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/audit_ai_v10.json")

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
        "sentences": [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 15],
        "tables": soup.find_all('table'),
        "lists": soup.find_all(['ul', 'ol']),
        "images": soup.find_all('img'),
        "links": soup.find_all('a', href=True)
    }

# КРИТЕРИЙ 1: УНИКАЛЬНОСТЬ ИНФОРМАЦИИ
def check_uniqueness(text, sentences):
    score = 0
    indicators = []
    
    # Проверяем наличие уникальных данных
    # 1. Статистика и цифры
    stats = re.findall(r'\d+[\.,]?\d*\s*%', text)
    if len(stats) >= 3:
        score += 20
        indicators.append(f"Статистика: {len(stats)} значений")
    
    # 2. Оригинальные исследования/кейсы
    case_keywords = ['исследование', 'опыт', 'практика', 'кейс', 'пример из практики']
    has_cases = any(kw in text.lower() for kw in case_keywords)
    if has_cases:
        score += 20
        indicators.append("Есть кейсы/примеры из практики")
    
    # 3. Авторские мнения/рекомендации
    opinion_keywords = ['рекомендуем', 'советуем', 'наш опыт', 'мы считаем']
    has_opinions = any(kw in text.lower() for kw in opinion_keywords)
    if has_opinions:
        score += 15
        indicators.append("Есть авторские рекомендации")
    
    # 4. Уникальные формулировки (не шаблонные)
    generic_phrases = ['является важным', 'играет важную роль', 'следует отметить']
    generic_count = sum(1 for phrase in generic_phrases if phrase in text.lower())
    if generic_count < 3:
        score += 15
        indicators.append("Минимум шаблонных фраз")
    
    return {
        "score": min(70, score),
        "indicators": indicators,
        "fix": "Добавьте уникальные данные: статистику, кейсы из практики, авторские рекомендации" if score < 40 else "OK"
    }

# КРИТЕРИЙ 2: СТРУКТУРИРОВАННОСТЬ
def check_structure(parsed):
    score = 0
    indicators = []
    
    # Таблицы
    if len(parsed["tables"]) >= 1:
        score += 25
        indicators.append(f"Таблицы: {len(parsed['tables'])}")
    
    # Списки
    if len(parsed["lists"]) >= 2:
        score += 20
        indicators.append(f"Списки: {len(parsed['lists'])}")
    
    # Определения (формат "Термин: определение")
    definitions = re.findall(r'\b\w+\s*[:—-]\s*\w+', parsed["text"][:1000])
    if len(definitions) >= 2:
        score += 20
        indicators.append(f"Определения: {len(definitions)}")
    
    # Заголовки (h2, h3)
    headings = parsed["soup"].find_all(['h2', 'h3'])
    if len(headings) >= 3:
        score += 15
        indicators.append(f"Заголовки: {len(headings)}")
    
    # Абзацы (короткие, читаемые)
    short_paragraphs = sum(1 for s in parsed["sentences"] if len(s) < 200)
    if short_paragraphs >= 5:
        score += 10
        indicators.append("Хорошая разбивка на абзацы")
    
    return {
        "score": min(90, score),
        "indicators": indicators,
        "fix": "Добавьте таблицы, списки, четкие определения и заголовки" if score < 50 else "OK"
    }

# КРИТЕРИЙ 3: АВТОРИТЕТНОСТЬ ИСТОЧНИКОВ
def check_authority(parsed):
    score = 0
    indicators = []
    
    # Ссылки на авторитетные домены
    authority_domains = ["wsava", "iris", "pubmed", "ncbi", "who.int", "avma", "doi.org"]
    found_domains = []
    
    for link in parsed["links"]:
        href = link.get('href', '').lower()
        for domain in authority_domains:
            if domain in href and domain not in found_domains:
                found_domains.append(domain)
                break
    
    if len(found_domains) >= 2:
        score += 30
        indicators.append(f"Авторитетные источники: {', '.join(found_domains)}")
    elif len(found_domains) == 1:
        score += 15
        indicators.append(f"Авторитетный источник: {found_domains[0]}")
    
    # Упоминания протоколов и стандартов
    protocol_keywords = ['протокол', 'стандарт', 'рекомендации', 'руководство', 'guideline']
    protocol_count = sum(1 for kw in protocol_keywords if kw in parsed["text"].lower())
    if protocol_count >= 2:
        score += 20
        indicators.append(f"Упоминания протоколов: {protocol_count}")
    
    # Цитирование исследований
    citation_patterns = [r'согласно\s+\S+', r'исследовани[яе]\s+показал', r'по\s+данным\s+\S+']
    citations = sum(1 for pattern in citation_patterns if re.search(pattern, parsed["text"].lower()))
    if citations >= 2:
        score += 20
        indicators.append(f"Цитирования исследований: {citations}")
    
    return {
        "score": min(70, score),
        "indicators": indicators,
        "found_domains": found_domains,
        "fix": "Добавьте ссылки на WSAVA, IRIS, PubMed и цитирования протоколов" if score < 40 else "OK"
    }

# КРИТЕРИЙ 4: ЭМОЦИОНАЛЬНАЯ ВОВЛЕЧЕННОСТЬ
def check_emotional_resonance(text):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # Истории пациентов/кейсы
    story_keywords = ['пациент', 'случай', 'история', 'обратился', 'привезли', 'владельц']
    story_count = sum(1 for kw in story_keywords if kw in text_lower)
    if story_count >= 2:
        score += 25
        indicators.append(f"Истории пациентов: {story_count} упоминаний")
    
    # Эмпатия и забота
    empathy_keywords = ['понимаем', 'сочувствуем', 'забота', 'комфорт', 'спокойствие', 'безопасность']
    empathy_count = sum(1 for kw in empathy_keywords if kw in text_lower)
    if empathy_count >= 2:
        score += 20
        indicators.append(f"Эмпатия: {empathy_count} маркеров")
    
    # Обращение к читателю
    direct_address = sum(1 for kw in ['вы ', 'ваш', 'вашего', 'вашей'] if kw in text_lower)
    if direct_address >= 3:
        score += 15
        indicators.append(f"Прямое обращение к читателю: {direct_address}")
    
    # Избегание холодного академического тона
    cold_markers = ['следует отметить', 'является важным', 'необходимо подчеркнуть']
    cold_count = sum(1 for m in cold_markers if m in text_lower)
    if cold_count < 3:
        score += 15
        indicators.append("Тёплый, человеческий тон")
    
    return {
        "score": min(75, score),
        "indicators": indicators,
        "fix": "Добавьте истории пациентов, эмпатию и прямое обращение к читателю" if score < 40 else "OK"
    }

# КРИТЕРИЙ 5: ПРАКТИЧЕСКАЯ ЦЕННОСТЬ
def check_actionability(text, sentences):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # Чек-листы и пошаговые инструкции
    action_markers = ['шаг', 'во-первых', 'во-вторых', 'далее', 'затем', 'после этого']
    action_count = sum(1 for m in action_markers if m in text_lower)
    if action_count >= 3:
        score += 25
        indicators.append(f"Пошаговые инструкции: {action_count}")
    
    # Конкретные рекомендации "что делать"
    recommendation_patterns = [r'необходимо\s+\S+', r'следует\s+\S+', r'рекомендуем\s+\S+']
    rec_count = sum(1 for p in recommendation_patterns if re.search(p, text_lower))
    if rec_count >= 2:
        score += 20
        indicators.append(f"Конкретные рекомендации: {rec_count}")
    
    # Предупреждения и "красные флаги"
    warning_keywords = ['срочно', 'немедленно', 'опасно', 'тревожный', 'красный флаг']
    warning_count = sum(1 for kw in warning_keywords if kw in text_lower)
    if warning_count >= 1:
        score += 20
        indicators.append(f"Предупреждения: {warning_count}")
    
    # Алгоритмы действий
    algo_keywords = ['алгоритм', 'порядок действий', 'план', 'чек-лист']
    if any(kw in text_lower for kw in algo_keywords):
        score += 15
        indicators.append("Есть алгоритм/чек-лист")
    
    return {
        "score": min(80, score),
        "indicators": indicators,
        "fix": "Добавьте пошаговые инструкции, конкретные рекомендации и предупреждения" if score < 40 else "OK"
    }

# КРИТЕРИЙ 6: ДОЛГОСРОЧНАЯ АКТУАЛЬНОСТЬ (Evergreen Score)
def check_longevity(text):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # Фундаментальные темы (не устаревают)
    evergreen_topics = ['анатомия', 'физиология', 'симптомы', 'диагностика', 'профилактика']
    evergreen_count = sum(1 for t in evergreen_topics if t in text_lower)
    if evergreen_count >= 2:
        score += 30
        indicators.append(f"Фундаментальные темы: {evergreen_count}")
    
    # Отсутствие привязки к конкретному году (кроме ссылок на актуальные протоколы)
    year_patterns = re.findall(r'\b20[12]\d\b', text)
    if len(year_patterns) <= 2:
        score += 20
        indicators.append("Контент не привязан к устаревающим датам")
    else:
        indicators.append(f"Упоминаний лет: {len(year_patterns)} (риск устаревания)")
    
    # Универсальность (применимо к разным ситуациям)
    universal_keywords = ['всегда', 'обычно', 'как правило', 'в большинстве случаев']
    if any(kw in text_lower for kw in universal_keywords):
        score += 15
        indicators.append("Универсальные принципы")
    
    return {
        "score": min(65, score),
        "indicators": indicators,
        "fix": "Сфокусируйтесь на фундаментальных принципах, а не на временных трендах" if score < 30 else "OK"
    }

# КРИТЕРИЙ 7: ЭТИЧЕСКАЯ ЧИСТОТА
def check_ethical_compliance(text):
    score = 0
    issues = []
    text_lower = text.lower()
    
    # Баланс мнений (не абсолютные утверждения)
    balance_markers = ['может', 'возможно', 'в некоторых случаях', 'зависит от', 'индивидуально']
    balance_count = sum(1 for m in balance_markers if m in text_lower)
    if balance_count >= 2:
        score += 25
    else:
        issues.append("Мало маркеров баланса мнений")
    
    # Отсутствие дискриминации
    discriminatory_patterns = ['только для', 'исключительно', 'никогда не']
    disc_count = sum(1 for p in discriminatory_patterns if p in text_lower)
    if disc_count < 2:
        score += 25
    else:
        issues.append("Возможные абсолютные утверждения")
    
    # Прозрачность ограничений
    limitation_keywords = ['ограничения', 'не заменяет', 'требуется консультация', 'индивидуальный подход']
    if any(kw in text_lower for kw in limitation_keywords):
        score += 25
    else:
        issues.append("Нет упоминания ограничений/необходимости консультации")
    
    # Ссылка на специалиста
    if 'ветеринар' in text_lower or 'специалист' in text_lower:
        score += 25
    
    return {
        "score": min(100, score),
        "issues": issues,
        "fix": "Добавьте баланс мнений, упоминание ограничений и необходимость консультации специалиста" if issues else "OK"
    }

# ИТОГОВЫЙ ПРОГНОЗ: СРОК ЖИЗНИ КОНТЕНТА В ОБУЧАЮЩИХ ДАННЫХ
def predict_training_lifespan(total_score):
    if total_score >= 80:
        months = 36
        tier = "PLATINUM — вечный контент для обучения ИИ"
    elif total_score >= 65:
        months = 24
        tier = "GOLD — долгосрочная ценность"
    elif total_score >= 50:
        months = 12
        tier = "SILVER — стандартная ценность"
    elif total_score >= 35:
        months = 6
        tier = "BRONZE — требует обновления"
    else:
        months = 2
        tier = "НЕ ПОДХОДИТ для обучения ИИ"
    
    expiry_date = (datetime.now() + timedelta(days=months*30)).strftime("%Y-%m-%d")
    return {
        "tier": tier,
        "lifespan_months": months,
        "expiry_date": expiry_date,
        "total_score": total_score
    }

# ГЛАВНАЯ ФУНКЦИЯ
def run_ai_audit_v10():
    from datetime import timedelta
    print("="*70)
    print("АГЕНТ AI TRAINING DATA POTENTIAL v10: ГОТОВНОСТЬ К ОБУЧЕНИЮ ИИ")
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
        s1 = check_uniqueness(parsed["text"], parsed["sentences"])
        s2 = check_structure(parsed)
        s3 = check_authority(parsed)
        s4 = check_emotional_resonance(parsed["text"])
        s5 = check_actionability(parsed["text"], parsed["sentences"])
        s6 = check_longevity(parsed["text"])
        s7 = check_ethical_compliance(parsed["text"])
        total = (s1["score"] + s2["score"] + s3["score"] + s4["score"] + s5["score"] + s6["score"] + s7["score"]) // 7
        prediction = predict_training_lifespan(total)
        print(f"  1. Уникальность: {s1['score']}/70")
        print(f"  2. Структурированность: {s2['score']}/90")
        print(f"  3. Авторитетность: {s3['score']}/70")
        print(f"  4. Эмоциональный резонанс: {s4['score']}/75")
        print(f"  5. Практическая ценность: {s5['score']}/80")
        print(f"  6. Долгосрочная актуальность: {s6['score']}/65")
        print(f"  7. Этическая чистота: {s7['score']}/100")
        print(f"  ─────────────────")
        print(f"  ОБЩИЙ TRAINING SCORE: {total}/100")
        print(f"  ТИР: {prediction['tier']}")
        print(f"  Срок жизни в обучающих данных: {prediction['lifespan_months']} мес.")
        print(f"  Дата 'устаревания': {prediction['expiry_date']}")
        if s7["issues"]:
            print(f"  ⚠️ Этические замечания: {', '.join(s7['issues'][:2])}")
        results.append({
            "site": key,
            "url": url,
            "scores": {
                "uniqueness": s1,
                "structure": s2,
                "authority": s3,
                "emotional": s4,
                "actionability": s5,
                "longevity": s6,
                "ethical": s7
            },
            "total_score": total,
            "prediction": prediction
        })
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "AI Training Data Potential v10.0",
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
    print("СВОДНЫЙ ОТЧЁТ AI TRAINING DATA POTENTIAL v10")
    print("="*70)
    print(f"Средний Training Score: {report['summary']['avg_score']}/100")
    print(f"PLATINUM (вечный контент): {report['summary']['platinum_sites']} сайтов")
    print(f"GOLD (долгосрочная ценность): {report['summary']['gold_sites']} сайтов")
    print(f"НЕ ПОДХОДИТ для обучения ИИ: {report['summary']['unsuitable_sites']} сайтов")
    print(f"\nПолный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit_v10()
