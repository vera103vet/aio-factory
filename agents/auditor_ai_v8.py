import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/audit_ai_v8.json")

QUESTION_BANK = {
    "эпилепс": [
        "Какие первые признаки эпилепсии у собаки?",
        "Можно ли вылечить эпилепсию у собаки?",
        "Что делать при приступе эпилепсии у собаки?",
        "Какие препараты применяют при эпилепсии?",
        "Сколько длится приступ эпилепсии?",
        "Опасна ли эпилепсия для жизни собаки?",
        "Как диагностируют эпилепсию у собак?",
        "Какие побочные эффекты у лекарств от эпилепсии?"
    ],
    "почек": [
        "Какие симптомы хронической болезни почек у кошек?",
        "Какая диета при ХБП у кошек?",
        "Можно ли вылечить ХБП у кошки?",
        "Какие стадии ХБП по классификации IRIS?",
        "Какой прогноз при ХБП у кошек?",
        "Как часто нужно сдавать анализы при ХБП?",
        "Какие препараты назначают при ХБП?",
        "Сколько живут кошки с ХБП?"
    ],
    "онколог": [
        "Какие признаки онкологии у собак?",
        "Можно ли вылечить рак у собаки?",
        "Какие виды химиотерапии применяют у животных?",
        "Какие побочные эффекты у химиотерапии?",
        "Как диагностируют рак у животных?",
        "Какой прогноз при онкологии у собак?"
    ],
    "кардиолог": [
        "Какие симптомы сердечной недостаточности у собак?",
        "Как диагностируют болезни сердца у животных?",
        "Какие препараты применяют при аритмии?",
        "Можно ли вылечить аритмию у собаки?",
        "Какой прогноз при сердечной недостаточности?"
    ],
    "ветеринар": [
        "Как вызвать ветеринара на дом в Минске?",
        "Сколько стоит вызов ветеринара на дом?",
        "Какие услуги оказывает ветеринар на дому?",
        "Как подготовиться к визиту ветеринара?",
        "Какие документы нужны для вызова ветеринара?"
    ]
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
        "sentences": [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 15]
    }

def get_relevant_questions(topic_keyword):
    topic_lower = topic_keyword.lower() if topic_keyword else ""
    relevant = []
    for key, questions in QUESTION_BANK.items():
        if key in topic_lower:
            relevant = questions
            break
    if not relevant:
        relevant = QUESTION_BANK.get("ветеринар", [])
    return relevant

def check_answer_coverage(text, sentences, questions):
    answered = []
    unanswered = []
    for question in questions:
        stop_words = {'какие', 'что', 'как', 'где', 'когда', 'почему', 'можно', 'ли', 'у', 'для', 'и', 'в', 'на', 'с', 'по', 'к', 'из', 'от'}
        keywords = [w.lower() for w in re.findall(r'\b[а-яёa-z]{4,}\b', question.lower()) if w.lower() not in stop_words]
        if not keywords:
            continue
        found_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            matches = sum(1 for kw in keywords if kw in sentence_lower)
            if matches >= len(keywords) * 0.6:
                found_sentences.append(sentence[:100])
        if found_sentences:
            answered.append({
                "question": question,
                "answer_snippet": found_sentences[0],
                "confidence": len(found_sentences)
            })
        else:
            unanswered.append(question)
    coverage = len(answered) / len(questions) * 100 if questions else 0
    return {
        "score": int(coverage),
        "total_questions": len(questions),
        "answered": len(answered),
        "unanswered": len(unanswered),
        "answered_details": answered[:5],
        "unanswered_questions": unanswered
    }

def analyze_answer_quality(answered_details):
    if not answered_details:
        return {"score": 0, "avg_length": 0, "has_numbers": False, "has_lists": False}
    total_score = 0
    total_length = 0
    has_numbers = False
    has_lists = False
    for ans in answered_details:
        snippet = ans.get("answer_snippet", "")
        length = len(snippet.split())
        total_length += length
        if 15 <= length <= 80:
            total_score += 30
        elif length > 80:
            total_score += 15
        if re.search(r'\d+', snippet):
            has_numbers = True
            total_score += 20
        if re.search(r'[;:,]', snippet) or 'и ' in snippet:
            has_lists = True
            total_score += 20
        quality_markers = ['включает', 'состоит', 'признаки', 'симптомы', 'является']
        if any(m in snippet.lower() for m in quality_markers):
            total_score += 30
    avg_score = total_score // len(answered_details) if answered_details else 0
    return {
        "score": min(100, avg_score),
        "avg_length": total_length // len(answered_details) if answered_details else 0,
        "has_numbers": has_numbers,
        "has_lists": has_lists
    }

def prioritize_gaps(unanswered_questions, topic_keyword):
    if not unanswered_questions:
        return []
    prioritized = []
    for q in unanswered_questions:
        q_lower = q.lower()
        priority = "medium"
        reason = "дополнительный вопрос"
        if any(w in q_lower for w in ['симптом', 'признак', 'лечени', 'перв', 'срочн', 'опасн']):
            priority = "high"
            reason = "критический вопрос для YMYL"
        if any(w in q_lower for w in ['стоит', 'цена', 'вызов', 'сколько']):
            priority = "high"
            reason = "коммерческий вопрос"
        if any(w in q_lower for w in ['диагноз', 'анализ', 'обслед']):
            priority = "medium"
            reason = "диагностический вопрос"
        prioritized.append({
            "question": q,
            "priority": priority,
            "reason": reason
        })
    prioritized.sort(key=lambda x: 0 if x["priority"] == "high" else 1)
    return prioritized

def predict_future_questions(topic_keyword):
    topic_lower = topic_keyword.lower() if topic_keyword else ""
    future_questions = []
    trend_patterns = {
        "эпилепс": [
            "Новые препараты от эпилепсии у собак 2027",
            "Генная терапия эпилепсии у животных",
            "ИИ-диагностика эпилепсии у собак"
        ],
        "почек": [
            "Новые протоколы IRIS 2027 для ХБП",
            "Ранняя диагностика ХБП по биомаркерам",
            "Персонализированная диета при ХБП"
        ],
        "онколог": [
            "Иммунотерапия рака у собак 2027",
            "Жидкая биопсия для онкологии животных",
            "Таргетная терапия опухолей у кошек"
        ],
        "кардиолог": [
            "Новые методы ЭХО-кардиографии 2027",
            "Генетические маркеры сердечных болезней",
            "Телемедицина в кардиологии животных"
        ],
        "ветеринар": [
            "AI-диагностика в ветеринарии 2027",
            "Телемедицина: вызов ветеринара онлайн",
            "Новые стандарты ветеринарной помощи"
        ]
    }
    for key, questions in trend_patterns.items():
        if key in topic_lower:
            future_questions = questions
            break
    if not future_questions:
        future_questions = trend_patterns.get("ветеринар", [])
    return future_questions

def run_ai_audit_v8():
    print("="*70)
    print("АГЕНТ USER INTENT PREDICTION v8: ПОКРЫТИЕ НАМЕРЕНИЙ")
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
        topic_keyword = ""
        for topic in registry:
            if topic.get("target_site") == key:
                topic_keyword = topic.get("primary_keyword", "")
                break
        if not topic_keyword:
            print(f"  Тема не найдена в реестре, используем 'ветеринар'")
            topic_keyword = "ветеринар на дом минск"
        print(f"  Тема: {topic_keyword}")
        questions = get_relevant_questions(topic_keyword)
        print(f"  Сгенерировано вопросов: {len(questions)}")
        coverage = check_answer_coverage(parsed["text"], parsed["sentences"], questions)
        print(f"  Intent Coverage Score: {coverage['score']}%")
        print(f"  Отвечено вопросов: {coverage['answered']}/{coverage['total_questions']}")
        quality = analyze_answer_quality(coverage["answered_details"])
        print(f"  Качество ответов: {quality['score']}/100")
        print(f"  Средняя длина ответа: {quality['avg_length']} слов")
        print(f"  Есть цифры: {'да' if quality['has_numbers'] else 'нет'}")
        gaps = prioritize_gaps(coverage["unanswered_questions"], topic_keyword)
        print(f"  Пробелов: {len(gaps)}")
        high_priority = [g for g in gaps if g["priority"] == "high"]
        if high_priority:
            print(f"  🔴 Высокий приоритет ({len(high_priority)}):")
            for g in high_priority[:3]:
                print(f"    - {g['question']} ({g['reason']})")
        future = predict_future_questions(topic_keyword)
        print(f"  Прогноз будущих вопросов: {len(future)}")
        for f in future[:2]:
            print(f"    🔮 {f}")
        total_score = (coverage["score"] + quality["score"]) // 2
        print(f"\n  ОБЩИЙ AI-СКОР v8: {total_score}/100")
        results.append({
            "site": key,
            "url": url,
            "topic": topic_keyword,
            "total_questions": len(questions),
            "coverage": coverage,
            "quality": quality,
            "gaps": gaps,
            "future_questions": future,
            "total_score": total_score
        })
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "User Intent Prediction v8.0",
        "summary": {
            "avg_score": round(sum(r["total_score"] for r in results) / len(results), 1) if results else 0,
            "total_sites": len(results),
            "total_gaps": sum(len(r["gaps"]) for r in results),
            "high_priority_gaps": sum(1 for r in results for g in r["gaps"] if g["priority"] == "high")
        },
        "sites": results
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n" + "="*70)
    print("СВОДНЫЙ ОТЧЁТ USER INTENT PREDICTION v8")
    print("="*70)
    print(f"Средний AI-скор v8: {report['summary']['avg_score']}/100")
    print(f"Проанализировано сайтов: {report['summary']['total_sites']}")
    print(f"Всего пробелов: {report['summary']['total_gaps']}")
    print(f"Высокий приоритет: {report['summary']['high_priority_gaps']}")
    print(f"\nПолный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit_v8()
