import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/audit_ai_v11.json")

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
        "paragraphs": soup.find_all('p'),
        "headings": soup.find_all(['h1', 'h2', 'h3', 'h4']),
        "lists": soup.find_all(['ul', 'ol']),
        "links": soup.find_all('a', href=True)
    }

# КРИТЕРИЙ 1: CONVERSATIONAL TONE SCORE (Разговорный тон)
def check_conversational_tone(text, sentences):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # Разговорные маркеры
    conversational_markers = ['вы ', 'ваш', 'давайте', 'представьте', 'например', 'кстати', 'итак', 'вообще']
    conv_count = sum(1 for m in conversational_markers if m in text_lower)
    if conv_count >= 5:
        score += 30
        indicators.append(f"Разговорные маркеры: {conv_count}")
    elif conv_count >= 3:
        score += 15
        indicators.append(f"Разговорные маркеры: {conv_count}")
    
    # Короткие предложения (легче воспринимать на слух)
    short_sentences = sum(1 for s in sentences if len(s.split()) <= 15)
    ratio = short_sentences / len(sentences) if sentences else 0
    if ratio >= 0.4:
        score += 25
        indicators.append(f"Коротких предложений: {int(ratio*100)}%")
    elif ratio >= 0.25:
        score += 15
    
    # Вопросы к читателю
    questions = sum(1 for s in sentences if s.endswith('?'))
    if questions >= 2:
        score += 20
        indicators.append(f"Вопросов к читателю: {questions}")
    
    # Избегание сложных терминов без объяснения
    complex_terms = re.findall(r'\b[а-яё]{15,}\b', text_lower)
    if len(complex_terms) <= 5:
        score += 15
        indicators.append("Минимум сложных терминов")
    
    return {
        "score": min(90, score),
        "indicators": indicators,
        "fix": "Добавьте разговорные маркеры, короткие предложения и вопросы к читателю" if score < 40 else "OK"
    }

# КРИТЕРИЙ 2: QUESTION-ANSWER FORMAT
def check_qa_format(text, sentences):
    score = 0
    indicators = []
    
    # Наличие вопросов в тексте
    questions = [s for s in sentences if s.endswith('?')]
    if len(questions) >= 3:
        score += 25
        indicators.append(f"Вопросов в тексте: {len(questions)}")
    elif len(questions) >= 1:
        score += 10
    
    # Наличие ответов после вопросов (следующее предложение)
    qa_pairs = 0
    for i, s in enumerate(sentences):
        if s.endswith('?') and i + 1 < len(sentences):
            next_sentence = sentences[i + 1]
            # Ответ должен начинаться с маркера
            answer_markers = ['это', 'да', 'нет', 'во-первых', 'основные', 'главные']
            if any(m in next_sentence.lower() for m in answer_markers):
                qa_pairs += 1
    
    if qa_pairs >= 2:
        score += 30
        indicators.append(f"Пар вопрос-ответ: {qa_pairs}")
    elif qa_pairs >= 1:
        score += 15
    
    # FAQ-секция
    has_faq = bool(re.search(r'(faq|часто задаваем|вопрос.*ответ)', text.lower()))
    if has_faq:
        score += 20
        indicators.append("Есть FAQ-секция")
    
    return {
        "score": min(75, score),
        "indicators": indicators,
        "qa_pairs": qa_pairs,
        "fix": "Добавьте вопросы и прямые ответы на них, создайте FAQ-секцию" if score < 30 else "OK"
    }

# КРИТЕРИЙ 3: READABILITY FOR TTS (Читаемость для синтеза речи)
def check_tts_readability(text, sentences):
    score = 0
    indicators = []
    
    # Средняя длина предложения (оптимум 10-20 слов для TTS)
    avg_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
    if 10 <= avg_length <= 20:
        score += 25
        indicators.append(f"Средняя длина предложения: {int(avg_length)} слов (оптимум)")
    elif 8 <= avg_length <= 25:
        score += 15
        indicators.append(f"Средняя длина: {int(avg_length)} слов")
    else:
        indicators.append(f"Средняя длина: {int(avg_length)} слов (неоптимально для TTS)")
    
    # Отсутствие аббревиатур без расшифровки
    abbreviations = re.findall(r'\b[А-ЯЁ]{2,}\b', text)
    if len(abbreviations) <= 3:
        score += 20
        indicators.append("Минимум аббревиатур")
    
    # Числа прописью (легче читать вслух)
    numbers_written = len(re.findall(r'(один|два|три|четыре|пять|первый|второй)', text.lower()))
    if numbers_written >= 2:
        score += 15
        indicators.append(f"Числа прописью: {numbers_written}")
    
    # Паузы (запятые, точки с запятой)
    pauses = text.count(',') + text.count(';')
    pause_ratio = pauses / len(text.split()) if text else 0
    if 0.1 <= pause_ratio <= 0.2:
        score += 15
        indicators.append("Хороший ритм для чтения вслух")
    
    return {
        "score": min(75, score),
        "indicators": indicators,
        "avg_sentence_length": int(avg_length),
        "fix": "Оптимизируйте длину предложений и добавьте паузы для TTS" if score < 35 else "OK"
    }

# КРИТЕРИЙ 4: LOCAL VOICE SEARCH (Локальный голосовой поиск)
def check_local_voice_search(text, sentences):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # Упоминание города/региона
    city_markers = ['минск', 'минской', 'беларус', 'белорусс']
    city_found = [m for m in city_markers if m in text_lower]
    if len(city_found) >= 2:
        score += 25
        indicators.append(f"Локальные маркеры: {', '.join(city_found)}")
    elif len(city_found) >= 1:
        score += 10
    
    # Фразы "рядом со мной", "поблизости", "в моём районе"
    proximity_phrases = ['рядом', 'поблизости', 'недалеко', 'в вашем районе', 'возле вас']
    prox_count = sum(1 for p in proximity_phrases if p in text_lower)
    if prox_count >= 2:
        score += 25
        indicators.append(f"Фразы близости: {prox_count}")
    elif prox_count >= 1:
        score += 10
    
    # NAP-консистентность (телефон, адрес)
    has_phone = bool(re.search(r'\+?\d[\d\s\-\(\)]{7,}', text))
    has_address = bool(re.search(r'(ул\.|улица|пр\.|проспект|дом|д\.)', text_lower))
    if has_phone and has_address:
        score += 25
        indicators.append("Есть телефон и адрес (NAP)")
    elif has_phone or has_address:
        score += 10
    
    # Голосовые паттерны ("как найти", "где находится", "как добраться")
    voice_patterns = ['как найти', 'где находится', 'как добраться', 'расположен', 'адрес']
    vp_count = sum(1 for p in voice_patterns if p in text_lower)
    if vp_count >= 2:
        score += 15
        indicators.append(f"Голосовые паттерны навигации: {vp_count}")
    
    return {
        "score": min(90, score),
        "indicators": indicators,
        "fix": "Добавьте упоминания города, фразы 'рядом со мной', телефон и адрес" if score < 40 else "OK"
    }

# КРИТЕРИЙ 5: FEATURED SNIPPET READINESS (Готовность к цитированию ассистентами)
def check_featured_snippet(text, sentences, soup):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # Прямой ответ в начале (BLUF-структура)
    first_200 = ' '.join(text.split()[:200]).lower()
    has_direct_answer = any(x in first_200 for x in ['это ', 'является', 'включает', 'основные', 'представляет'])
    if has_direct_answer:
        score += 25
        indicators.append("Прямой ответ в начале (BLUF)")
    
    # Короткое определение (40-60 слов) — идеально для голосового цитирования
    definition_pattern = re.search(r'([^.]{40,80}(?:это|— это|является)[^.]{20,60})', text_lower)
    if definition_pattern:
        score += 25
        indicators.append("Есть компактное определение (40-60 слов)")
    
    # Нумерованные списки (ассистенты любят перечисления)
    numbered_lists = soup.find_all('ol')
    if len(numbered_lists) >= 1:
        score += 20
        indicators.append(f"Нумерованных списков: {len(numbered_lists)}")
    
    # Маркеры "пошаговости"
    step_markers = ['шаг', 'во-первых', 'во-вторых', 'затем', 'после этого', 'наконец']
    step_count = sum(1 for m in step_markers if m in text_lower)
    if step_count >= 3:
        score += 20
        indicators.append(f"Пошаговые маркеры: {step_count}")
    
    # Короткий итоговый абзац (ассистент зачитает его вслух)
    short_conclusion = any(len(s.split()) <= 25 and len(s) > 30 for s in sentences[-5:])
    if short_conclusion:
        score += 10
        indicators.append("Есть короткий итог в конце")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "fix": "Добавьте BLUF-структуру, компактное определение и нумерованные списки" if score < 40 else "OK"
    }

# ИТОГОВЫЙ ПРОГНОЗ: ГОЛОСОВОЙ ПОТЕНЦИАЛ
def predict_voice_potential(total_score):
    if total_score >= 80:
        tier = "PLATINUM — идеален для Alexa/Siri/Алиса"
        citation_chance = 85
    elif total_score >= 65:
        tier = "GOLD — высокая вероятность цитирования"
        citation_chance = 65
    elif total_score >= 50:
        tier = "SILVER — стандартная готовность"
        citation_chance = 40
    elif total_score >= 35:
        tier = "BRONZE — требует доработки"
        citation_chance = 20
    else:
        tier = "НЕ ГОТОВ для голосового поиска"
        citation_chance = 5
    
    return {
        "tier": tier,
        "citation_chance_percent": citation_chance,
        "total_score": total_score
    }

# ГЛАВНАЯ ФУНКЦИЯ
def run_ai_audit_v11():
    print("="*70)
    print("АГЕНТ VOICE SEARCH OPTIMIZATION v11: ГОТОВНОСТЬ К ГОЛОСОВОМУ ПОИСКУ")
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
        s1 = check_conversational_tone(parsed["text"], parsed["sentences"])
        s2 = check_qa_format(parsed["text"], parsed["sentences"])
        s3 = check_tts_readability(parsed["text"], parsed["sentences"])
        s4 = check_local_voice_search(parsed["text"], parsed["sentences"])
        s5 = check_featured_snippet(parsed["text"], parsed["sentences"], parsed["soup"])
        total = (s1["score"] + s2["score"] + s3["score"] + s4["score"] + s5["score"]) // 5
        prediction = predict_voice_potential(total)
        print(f"  1. Разговорный тон: {s1['score']}/90")
        print(f"  2. Формат Вопрос-Ответ: {s2['score']}/75")
        print(f"  3. Читаемость для TTS: {s3['score']}/75")
        print(f"  4. Локальный голосовой поиск: {s4['score']}/90")
        print(f"  5. Featured Snippet: {s5['score']}/100")
        print(f"  ─────────────────")
        print(f"  ОБЩИЙ VOICE SCORE: {total}/100")
        print(f"  ТИР: {prediction['tier']}")
        print(f"  Вероятность цитирования ассистентом: {prediction['citation_chance_percent']}%")
        results.append({
            "site": key,
            "url": url,
            "scores": {
                "conversational": s1,
                "qa_format": s2,
                "tts_readability": s3,
                "local_voice": s4,
                "featured_snippet": s5
            },
            "total_score": total,
            "prediction": prediction
        })
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Voice Search Optimization v11.0",
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
    print("СВОДНЫЙ ОТЧЁТ VOICE SEARCH OPTIMIZATION v11")
    print("="*70)
    print(f"Средний Voice Score: {report['summary']['avg_score']}/100")
    print(f"PLATINUM (идеален для Alexa/Siri/Алиса): {report['summary']['platinum_sites']} сайтов")
    print(f"GOLD (высокая вероятность цитирования): {report['summary']['gold_sites']} сайтов")
    print(f"НЕ ГОТОВ для голосового поиска: {report['summary']['unsuitable_sites']} сайтов")
    print(f"\nПолный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit_v11()
