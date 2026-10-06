import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/audit_ai_v13.json")

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
        "headings": soup.find_all(['h1', 'h2', 'h3']),
        "images": soup.find_all('img'),
        "links": soup.find_all('a', href=True)
    }

# КРИТЕРИЙ 1: EMPATHY SCORE (Уровень эмпатии)
def check_empathy(text, sentences):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Прямое обращение к владельцу питомца
    owner_markers = ['ваш питомец', 'ваш любимец', 'ваш друг', 'ваша собака', 'ваша кошка', 'ваш щенок', 'ваш котёнок']
    owner_count = sum(1 for m in owner_markers if m in text_lower)
    if owner_count >= 3:
        score += 25
        indicators.append(f"Обращение к владельцу: {owner_count}")
    elif owner_count >= 1:
        score += 10
    
    # 2. Признание эмоций владельца
    emotion_acknowledgment = ['понимаем', 'знаем', 'представляем', 'сопереживаем', 'разделяем', 'тревога', 'беспокойство', 'страх', 'волнение']
    emp_count = sum(1 for e in emotion_acknowledgment if e in text_lower)
    if emp_count >= 3:
        score += 25
        indicators.append(f"Признание эмоций: {emp_count}")
    elif emp_count >= 1:
        score += 10
    
    # 3. Утешающие фразы
    comfort_phrases = ['не паникуйте', 'всё будет хорошо', 'мы поможем', 'не волнуйтесь', 'всё под контролем', 'вы не одни']
    comfort_count = sum(1 for p in comfort_phrases if p in text_lower)
    if comfort_count >= 2:
        score += 20
        indicators.append(f"Утешающие фразы: {comfort_count}")
    elif comfort_count >= 1:
        score += 10
    
    # 4. Использование "мы" вместо безличных конструкций
    we_markers = ['мы ', 'наш ', 'наша ', 'наше ', 'нами ']
    we_count = sum(1 for m in we_markers if m in text_lower)
    if we_count >= 5:
        score += 15
        indicators.append(f"Использование 'мы': {we_count}")
    elif we_count >= 2:
        score += 5
    
    # 5. Избегание холодного академического тона
    cold_markers = ['является важным', 'следует отметить', 'необходимо подчеркнуть', 'играет важную роль']
    cold_count = sum(1 for m in cold_markers if m in text_lower)
    if cold_count <= 2:
        score += 15
        indicators.append("Тёплый тон (минимум академизма)")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "fix": "Добавьте обращение к владельцу, признание эмоций и утешающие фразы" if score < 40 else "OK"
    }

# КРИТЕРИЙ 2: STORYTELLING INDEX (Наличие историй)
def check_storytelling(text, sentences):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Конкретные кейсы/истории пациентов
    story_markers = ['пациент', 'случай', 'история', 'обратился', 'привезли', 'владельц', 'пришёл', 'пришла']
    story_count = sum(1 for m in story_markers if m in text_lower)
    if story_count >= 3:
        score += 30
        indicators.append(f"Истории пациентов: {story_count}")
    elif story_count >= 1:
        score += 15
    
    # 2. Конкретные имена/клички (персонализация)
    name_patterns = re.findall(r'(?:кличк|имя|зовут)\s+[А-ЯЁ][а-яё]+', text)
    if len(name_patterns) >= 1:
        score += 20
        indicators.append(f"Персонализация (имена): {len(name_patterns)}")
    
    # 3. Хронология событий (начало, развитие, исход)
    timeline_markers = ['сначала', 'затем', 'после', 'в итоге', 'результат', 'исход', 'через неделю', 'через месяц']
    timeline_count = sum(1 for m in timeline_markers if m in text_lower)
    if timeline_count >= 3:
        score += 20
        indicators.append(f"Хронология: {timeline_count} маркеров")
    elif timeline_count >= 1:
        score += 10
    
    # 4. Цитаты владельцев или врачей
    quote_patterns = re.findall(r'["«][^"»]{20,100}["»]', text)
    if len(quote_patterns) >= 1:
        score += 15
        indicators.append(f"Цитаты: {len(quote_patterns)}")
    
    # 5. Эмоциональные кульминации
    climax_markers = ['к счастью', 'к сожалению', 'внезапно', 'неожиданно', 'спасли', 'вылечили', 'поправились']
    climax_count = sum(1 for m in climax_markers if m in text_lower)
    if climax_count >= 2:
        score += 15
        indicators.append(f"Эмоциональные кульминации: {climax_count}")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "fix": "Добавьте истории пациентов с именами, хронологией и эмоциональными кульминациями" if score < 40 else "OK"
    }

# КРИТЕРИЙ 3: EMOTIONAL VOCABULARY RICHNESS (Богатство эмоциональной лексики)
def check_emotional_vocabulary(text):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # База эмоциональных слов по категориям
    emotion_categories = {
        "забота": ['забота', 'заботлив', 'ухаживать', 'внимание', 'тепло', 'любовь', 'нежность'],
        "тревога": ['тревога', 'беспокойство', 'волнение', 'страх', 'паника', 'нервничать'],
        "надежда": ['надежда', 'шанс', 'возможность', 'улучшение', 'прогноз', 'перспектива'],
        "радость": ['радость', 'счастье', 'улыбка', 'игра', 'активность', 'бодрость'],
        "грусть": ['грусть', 'печаль', 'тоска', 'апатия', 'вялость', 'потеря'],
        "решимость": ['решимость', 'борьба', 'сила', 'стойкость', 'мужество', 'помощь']
    }
    
    found_categories = []
    total_emotional_words = 0
    
    for category, words in emotion_categories.items():
        count = sum(1 for w in words if w in text_lower)
        if count >= 2:
            found_categories.append(category)
            total_emotional_words += count
    
    if len(found_categories) >= 4:
        score += 35
        indicators.append(f"Эмоциональные категории: {len(found_categories)} ({', '.join(found_categories[:3])})")
    elif len(found_categories) >= 2:
        score += 20
        indicators.append(f"Эмоциональные категории: {len(found_categories)}")
    
    # Разнообразие эмоциональных слов (уникальность)
    all_emotion_words = []
    for words in emotion_categories.values():
        all_emotion_words.extend([w for w in words if w in text_lower])
    unique_emotions = len(set(all_emotion_words))
    
    if unique_emotions >= 8:
        score += 25
        indicators.append(f"Уникальных эмоциональных слов: {unique_emotions}")
    elif unique_emotions >= 4:
        score += 15
        indicators.append(f"Уникальных эмоциональных слов: {unique_emotions}")
    
    # Избегание повторений
    if unique_emotions >= 6 and total_emotional_words >= 10:
        score += 15
        indicators.append("Хорошее разнообразие без повторений")
    
    return {
        "score": min(75, score),
        "indicators": indicators,
        "found_categories": found_categories,
        "unique_emotions": unique_emotions,
        "fix": "Обогатите текст эмоциональной лексикой из разных категорий (забота, тревога, надежда)" if score < 35 else "OK"
    }

# КРИТЕРИЙ 4: TRUST SIGNALS (Маркеры доверия)
def check_trust_signals(parsed):
    score = 0
    indicators = []
    text_lower = parsed["text"].lower()
    soup = parsed["soup"]
    
    # 1. Упоминание квалификации/опыта
    expertise_markers = ['опыт', 'стаж', 'сертификат', 'диплом', 'специалист', 'эксперт', 'квалификация', 'образование']
    exp_count = sum(1 for m in expertise_markers if m in text_lower)
    if exp_count >= 3:
        score += 25
        indicators.append(f"Маркеры экспертизы: {exp_count}")
    elif exp_count >= 1:
        score += 10
    
    # 2. Отзывы/рекомендации
    review_markers = ['отзыв', 'благодарн', 'рекомендуют', 'клиент', 'довольн']
    rev_count = sum(1 for m in review_markers if m in text_lower)
    if rev_count >= 2:
        score += 20
        indicators.append(f"Упоминания отзывов: {rev_count}")
    
    # 3. Гарантии/обещания
    guarantee_markers = ['гаранти', 'обещаем', 'результат', 'эффективн']
    guar_count = sum(1 for m in guarantee_markers if m in text_lower)
    if guar_count >= 2:
        score += 15
        indicators.append(f"Гарантии: {guar_count}")
    
    # 4. Социальные доказательства (числа, статистика)
    social_proof = re.findall(r'\d+\s*(лет|год|пациент|клиент|случай|операци)', text_lower)
    if len(social_proof) >= 2:
        score += 15
        indicators.append(f"Социальные доказательства: {len(social_proof)}")
    
    # 5. Визуальные маркеры доверия (изображения врачей, клиники)
    has_doctor_images = False
    for img in parsed["images"]:
        alt = img.get('alt', '').lower()
        if any(w in alt for w in ['врач', 'доктор', 'специалист', 'команда', 'клиника']):
            has_doctor_images = True
            break
    if has_doctor_images:
        score += 15
        indicators.append("Фото врачей/команды")
    
    # 6. Контактная информация
    has_contact = bool(re.search(r'\+?\d[\d\s\-\(\)]{7,}', parsed["text"]))
    if has_contact:
        score += 10
        indicators.append("Контактная информация")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "fix": "Добавьте упоминания опыта, отзывы, гарантии и фото специалистов" if score < 40 else "OK"
    }

# КРИТЕРИЙ 5: CALL-TO-EMOTION EFFECTIVENESS (Эффективность эмоциональных призывов)
def check_call_to_emotion(text, sentences):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Призывы к действию с эмоциональной окраской
    emotional_cta = ['позвоните сейчас', 'не откладывайте', 'запишитесь сегодня', 'помогите питомцу', 'спасите жизнь', 'уберегите', 'защитите']
    cta_count = sum(1 for c in emotional_cta if c in text_lower)
    if cta_count >= 2:
        score += 30
        indicators.append(f"Эмоциональные CTA: {cta_count}")
    elif cta_count >= 1:
        score += 15
    
    # 2. Создание срочности (без паники)
    urgency_markers = ['срочно', 'немедленно', 'как можно скорее', 'не медлите', 'важно сейчас']
    urg_count = sum(1 for m in urgency_markers if m in text_lower)
    if 1 <= urg_count <= 3:  # Баланс: не слишком много
        score += 20
        indicators.append(f"Здоровая срочность: {urg_count}")
    elif urg_count > 3:
        indicators.append("⚠️ Избыток срочности (может пугать)")
        score += 5
    
    # 3. Позитивное завершение (надежда в конце)
    last_sentences = sentences[-5:] if len(sentences) >= 5 else sentences
    hope_markers = ['здоров', 'счастлив', 'активен', 'рад', 'благодар', 'спасибо', 'успех']
    has_hope_ending = any(any(m in s.lower() for m in hope_markers) for s in last_sentences)
    if has_hope_ending:
        score += 20
        indicators.append("Позитивное завершение")
    
    # 4. Баланс эмоций (не только страх, но и надежда)
    fear_words = ['опасн', 'угроз', 'риск', 'смерт', 'гибель', 'тяжел']
    hope_words = ['надежд', 'шанс', 'успех', 'вылеч', 'помож', 'спас']
    fear_count = sum(1 for w in fear_words if w in text_lower)
    hope_count = sum(1 for w in hope_words if w in text_lower)
    
    if fear_count > 0 and hope_count > 0:
        ratio = hope_count / (fear_count + hope_count)
        if 0.3 <= ratio <= 0.7:  # Сбалансировано
            score += 20
            indicators.append(f"Баланс страх/надежда: {fear_count}/{hope_count}")
        else:
            indicators.append(f"Дисбаланс: страх={fear_count}, надежда={hope_count}")
            score += 10
    elif hope_count > 0:
        score += 10
        indicators.append("Только позитивный тон")
    
    # 5. Персонализированный финальный призыв
    personal_cta = ['ваш питомец заслуживает', 'подарите', 'позаботьтесь', 'индивидуальный подход']
    personal_count = sum(1 for p in personal_cta if p in text_lower)
    if personal_count >= 1:
        score += 10
        indicators.append("Персонализированный призыв")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "fix": "Добавьте эмоциональные CTA, баланс страха/надежды и позитивное завершение" if score < 40 else "OK"
    }

# ИТОГОВЫЙ ПРОГНОЗ: ЭМОЦИОНАЛЬНЫЙ ПОТЕНЦИАЛ
def predict_emotional_potential(total_score):
    if total_score >= 80:
        tier = "PLATINUM — максимальный эмоциональный резонанс"
        ai_preference = 90
        sharing_potential = "Вирусный"
    elif total_score >= 65:
        tier = "GOLD — высокий эмоциональный отклик"
        ai_preference = 70
        sharing_potential = "Высокий"
    elif total_score >= 50:
        tier = "SILVER — стандартный уровень"
        ai_preference = 50
        sharing_potential = "Средний"
    elif total_score >= 35:
        tier = "BRONZE — требует эмоционального усиления"
        ai_preference = 30
        sharing_potential = "Низкий"
    else:
        tier = "НЕ ВЫЗЫВАЕТ эмоционального отклика"
        ai_preference = 10
        sharing_potential = "Нулевой"
    
    return {
        "tier": tier,
        "ai_citation_preference_percent": ai_preference,
        "sharing_potential": sharing_potential,
        "total_score": total_score
    }

# ГЛАВНАЯ ФУНКЦИЯ
def run_ai_audit_v13():
    print("="*70)
    print("АГЕНТ EMOTIONAL RESONANCE v13: ЭМОЦИОНАЛЬНЫЙ РЕЗОНАНС")
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
        s1 = check_empathy(parsed["text"], parsed["sentences"])
        s2 = check_storytelling(parsed["text"], parsed["sentences"])
        s3 = check_emotional_vocabulary(parsed["text"])
        s4 = check_trust_signals(parsed)
        s5 = check_call_to_emotion(parsed["text"], parsed["sentences"])
        total = (s1["score"] + s2["score"] + s3["score"] + s4["score"] + s5["score"]) // 5
        prediction = predict_emotional_potential(total)
        print(f"  1. Эмпатия: {s1['score']}/100")
        print(f"  2. Сторителлинг: {s2['score']}/100")
        print(f"  3. Эмоциональная лексика: {s3['score']}/75")
        print(f"  4. Маркеры доверия: {s4['score']}/100")
        print(f"  5. Эмоциональные призывы: {s5['score']}/100")
        print(f"  ─────────────────")
        print(f"  ОБЩИЙ EMOTIONAL SCORE: {total}/100")
        print(f"  ТИР: {prediction['tier']}")
        print(f"  Предпочтение ИИ для цитирования: {prediction['ai_citation_preference_percent']}%")
        print(f"  Потенциал распространения: {prediction['sharing_potential']}")
        results.append({
            "site": key,
            "url": url,
            "scores": {
                "empathy": s1,
                "storytelling": s2,
                "vocabulary": s3,
                "trust": s4,
                "cta_emotion": s5
            },
            "total_score": total,
            "prediction": prediction
        })
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Emotional Resonance Score v13.0",
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
    print("СВОДНЫЙ ОТЧЁТ EMOTIONAL RESONANCE v13")
    print("="*70)
    print(f"Средний Emotional Score: {report['summary']['avg_score']}/100")
    print(f"PLATINUM (максимальный резонанс): {report['summary']['platinum_sites']} сайтов")
    print(f"GOLD (высокий отклик): {report['summary']['gold_sites']} сайтов")
    print(f"НЕ ВЫЗЫВАЕТ отклика: {report['summary']['unsuitable_sites']} сайтов")
    print(f"\nПолный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit_v13()
