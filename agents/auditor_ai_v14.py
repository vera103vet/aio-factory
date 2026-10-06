import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/audit_ai_v14.json")

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
        "lists": soup.find_all(['ul', 'ol']),
        "tables": soup.find_all('table'),
        "headings": soup.find_all(['h1', 'h2', 'h3', 'h4'])
    }

# КРИТЕРИЙ 1: STEP-BY-STEP CLARITY (Чёткость пошаговых инструкций)
def check_step_by_step_clarity(text, sentences):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Наличие нумерованных шагов
    step_patterns = [
        r'шаг\s+\d+',
        r'\d+\.\s+[А-ЯЁ]',
        r'во-первых|во-вторых|в-третьих|в-четвёртых',
        r'первый\s+шаг|второй\s+шаг|третий\s+шаг'
    ]
    step_count = 0
    for pattern in step_patterns:
        step_count += len(re.findall(pattern, text_lower))
    
    if step_count >= 5:
        score += 30
        indicators.append(f"Пошаговые маркеры: {step_count}")
    elif step_count >= 3:
        score += 20
        indicators.append(f"Пошаговые маркеры: {step_count}")
    elif step_count >= 1:
        score += 10
    
    # 2. Глаголы повелительного наклонения (действие)
    action_verbs = ['сделайте', 'проверьте', 'позвоните', 'обратитесь', 'наблюдайте', 'запишите', 'сфотографируйте', 'не давайте', 'ограничьте']
    verb_count = sum(1 for v in action_verbs if v in text_lower)
    if verb_count >= 5:
        score += 25
        indicators.append(f"Глаголы действия: {verb_count}")
    elif verb_count >= 3:
        score += 15
        indicators.append(f"Глаголы действия: {verb_count}")
    
    # 3. Последовательные связки (затем, после этого, далее)
    sequence_markers = ['затем', 'после этого', 'далее', 'потом', 'наконец', 'в завершение']
    seq_count = sum(1 for m in sequence_markers if m in text_lower)
    if seq_count >= 3:
        score += 20
        indicators.append(f"Последовательные связки: {seq_count}")
    elif seq_count >= 1:
        score += 10
    
    # 4. Конкретные временные рамки
    time_frames = re.findall(r'(через\s+\d+|в\s+течение\s+\d+|до\s+\d+|после\s+\d+)\s*(минут|часов|дней|недель)', text_lower)
    if len(time_frames) >= 2:
        score += 15
        indicators.append(f"Временные рамки: {len(time_frames)}")
    
    # 5. Нумерованные списки в HTML
    ordered_lists = 0
    
    return {
        "score": min(90, score),
        "indicators": indicators,
        "fix": "Добавьте нумерованные шаги, глаголы действия и последовательные связки" if score < 40 else "OK"
    }

# КРИТЕРИЙ 2: DECISION TREE PRESENCE (Деревья решений)
def check_decision_tree(text, sentences):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Условные конструкции (если... то...)
    if_then_patterns = [
        r'если\s+[^,]+,\s*(то|тогда)',
        r'в\s+случае\s+[^,]+,\s*',
        r'при\s+[^,]+,\s*',
        r'когда\s+[^,]+,\s*(то|тогда)'
    ]
    if_then_count = 0
    for pattern in if_then_patterns:
        if_then_count += len(re.findall(pattern, text_lower))
    
    if if_then_count >= 4:
        score += 30
        indicators.append(f"Условные конструкции: {if_then_count}")
    elif if_then_count >= 2:
        score += 20
        indicators.append(f"Условные конструкции: {if_then_count}")
    elif if_then_count >= 1:
        score += 10
    
    # 2. Ветвления (в зависимости от, зависит от)
    branching_markers = ['в зависимости от', 'зависит от', 'если это', 'если нет', 'в противном случае', 'иначе']
    branch_count = sum(1 for m in branching_markers if m in text_lower)
    if branch_count >= 3:
        score += 25
        indicators.append(f"Ветвления: {branch_count}")
    elif branch_count >= 1:
        score += 10
    
    # 3. Классификации по категориям (легкий/средний/тяжелый)
    classification_patterns = [
        r'(лёгк|легк|средн|тяжел|тяжёл)\s*(форма|степень|стадия|случай)',
        r'(перв|втор|трет)\s*(стади|степень|уровен)',
        r'(начальн|промежуточн|поздн)\s*(стади|этап)'
    ]
    class_count = 0
    for pattern in classification_patterns:
        class_count += len(re.findall(pattern, text_lower))
    
    if class_count >= 2:
        score += 20
        indicators.append(f"Классификации: {class_count}")
    elif class_count >= 1:
        score += 10
    
    # 4. Рекомендации для разных сценариев
    scenario_markers = ['если у вас', 'если ваш', 'в вашем случае', 'для вашего', 'если ситуация']
    scenario_count = sum(1 for m in scenario_markers if m in text_lower)
    if scenario_count >= 2:
        score += 15
        indicators.append(f"Сценарии: {scenario_count}")
    
    return {
        "score": min(90, score),
        "indicators": indicators,
        "fix": "Добавьте условные конструкции (если... то...), ветвления и классификации" if score < 40 else "OK"
    }

# КРИТЕРИЙ 3: CHECKLIST COMPLETENESS (Полнота чек-листов)
def check_checklist_completeness(text, parsed):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Наличие списков (ul/ol)
    list_count = len(parsed["lists"])
    if list_count >= 3:
        score += 25
        indicators.append(f"Списков: {list_count}")
    elif list_count >= 1:
        score += 15
        indicators.append(f"Списков: {list_count}")
    
    # 2. Маркеры чек-листов (проверьте, убедитесь, обратите внимание)
    checklist_markers = ['проверьте', 'убедитесь', 'обратите внимание', 'убедитесь что', 'проверьте наличие', 'убедитесь в наличии']
    checklist_count = sum(1 for m in checklist_markers if m in text_lower)
    if checklist_count >= 3:
        score += 20
        indicators.append(f"Маркеры чек-листа: {checklist_count}")
    elif checklist_count >= 1:
        score += 10
    
    # 3. Конкретные пункты для проверки
    check_items = ['симптомы', 'признаки', 'показатели', 'параметры', 'критерии', 'условия']
    item_count = sum(1 for i in check_items if i in text_lower)
    if item_count >= 3:
        score += 20
        indicators.append(f"Пункты для проверки: {item_count}")
    elif item_count >= 1:
        score += 10
    
    # 4. Таблицы с критериями
    if len(parsed["tables"]) >= 1:
        score += 15
        indicators.append(f"Таблицы: {len(parsed['tables'])}")
    
    # 5. Итоговый чек-лист в конце
    has_summary_checklist = bool(re.search(r'(итоговый|финальный|общий)\s*(чек-лист|список|перечень)', text_lower))
    if has_summary_checklist:
        score += 10
        indicators.append("Итоговый чек-лист")
    
    return {
        "score": min(90, score),
        "indicators": indicators,
        "fix": "Добавьте списки, маркеры чек-листов и таблицы с критериями" if score < 40 else "OK"
    }

# КРИТЕРИЙ 4: EMERGENCY PROTOCOL READINESS (Готовность экстренных протоколов)
def check_emergency_protocol(text, sentences):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Маркеры экстренности
    emergency_markers = ['срочно', 'немедленно', 'экстренно', 'красный флаг', 'тревожный', 'опасно для жизни', 'угроза']
    emergency_count = sum(1 for m in emergency_markers if m in text_lower)
    if emergency_count >= 3:
        score += 25
        indicators.append(f"Маркеры экстренности: {emergency_count}")
    elif emergency_count >= 1:
        score += 10
    
    # 2. Конкретные действия "до приезда врача"
    first_aid_markers = ['до приезда', 'до визита', 'первая помощь', 'что делать сейчас', 'немедленно', 'не давайте', 'положите']
    first_aid_count = sum(1 for m in first_aid_markers if m in text_lower)
    if first_aid_count >= 3:
        score += 25
        indicators.append(f"Первая помощь: {first_aid_count} маркеров")
    elif first_aid_count >= 1:
        score += 10
    
    # 3. Телефон экстренной помощи
    has_emergency_phone = bool(re.search(r'(круглосуточн|24/7|экстренн|срочн).*\d[\d\s\-\(\)]{7,}', text_lower))
    if has_emergency_phone:
        score += 20
        indicators.append("Телефон экстренной помощи")
    
    # 4. Чёткие критерии "когда срочно к врачу"
    urgency_criteria = ['если температура', 'если кровотеч', 'если не дышит', 'если потерял сознани', 'если судорог', 'более 5 минут']
    criteria_count = sum(1 for c in urgency_criteria if c in text_lower)
    if criteria_count >= 2:
        score += 20
        indicators.append(f"Критерии срочности: {criteria_count}")
    elif criteria_count >= 1:
        score += 10
    
    # 5. Предупреждения "чего НЕ делать"
    dont_do_markers = ['не давайте', 'не пытайтесь', 'не делайте', 'запрещено', 'нельзя', 'не используйте']
    dont_count = sum(1 for m in dont_do_markers if m in text_lower)
    if dont_count >= 2:
        score += 10
        indicators.append(f"Предупреждения 'не делать': {dont_count}")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "fix": "Добавьте маркеры экстренности, первую помощь и критерии 'когда срочно к врачу'" if score < 40 else "OK"
    }

# КРИТЕРИЙ 5: POST-ACTION GUIDANCE (Рекомендации после действия)
def check_post_action_guidance(text, sentences):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Наблюдение после лечения/действия
    observation_markers = ['наблюдайте', 'следите', 'мониторьте', 'отмечайте', 'записывайте', 'контролируйте']
    obs_count = sum(1 for m in observation_markers if m in text_lower)
    if obs_count >= 3:
        score += 25
        indicators.append(f"Наблюдение: {obs_count} маркеров")
    elif obs_count >= 1:
        score += 10
    
    # 2. Временные рамки наблюдения
    observation_timeframes = ['в течение', 'на протяжении', 'первые', 'следующие', 'в течение недели', 'в течение месяца']
    tf_count = sum(1 for m in observation_timeframes if m in text_lower)
    if tf_count >= 2:
        score += 20
        indicators.append(f"Временные рамки наблюдения: {tf_count}")
    elif tf_count >= 1:
        score += 10
    
    # 3. "Когда вернуться к врачу"
    return_markers = ['вернитесь', 'повторный приём', 'контрольный осмотр', 'когда обратиться', 'если не улучш', 'если ухудш']
    return_count = sum(1 for m in return_markers if m in text_lower)
    if return_count >= 2:
        score += 20
        indicators.append(f"Когда вернуться: {return_count}")
    elif return_count >= 1:
        score += 10
    
    # 4. Признаки улучшения/ухудшения
    outcome_markers = ['улучшение', 'ухудшение', 'норма', 'отклонение', 'положительная динамика', 'отрицательная динамика']
    outcome_count = sum(1 for m in outcome_markers if m in text_lower)
    if outcome_count >= 2:
        score += 15
        indicators.append(f"Признаки исхода: {outcome_count}")
    
    # 5. Долгосрочные рекомендации
    longterm_markers = ['долгосрочн', 'постоянно', 'регулярно', 'ежемесячно', 'ежегодно', 'профилактика', 'поддерживающ']
    longterm_count = sum(1 for m in longterm_markers if m in text_lower)
    if longterm_count >= 2:
        score += 10
        indicators.append(f"Долгосрочные рекомендации: {longterm_count}")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "fix": "Добавьте рекомендации по наблюдению, сроки и 'когда вернуться к врачу'" if score < 40 else "OK"
    }

# ИТОГОВЫЙ ПРОГНОЗ: ПОТЕНЦИАЛ ПРИМЕНИМОСТИ
def predict_actionability_potential(total_score):
    if total_score >= 80:
        tier = "PLATINUM — идеальные практические инструкции"
        ai_preference = 90
        user_retention = "Максимальная"
    elif total_score >= 65:
        tier = "GOLD — высокая практическая ценность"
        ai_preference = 70
        user_retention = "Высокая"
    elif total_score >= 50:
        tier = "SILVER — стандартная применимость"
        ai_preference = 50
        user_retention = "Средняя"
    elif total_score >= 35:
        tier = "BRONZE — требует усиления инструкций"
        ai_preference = 30
        user_retention = "Низкая"
    else:
        tier = "НЕ ПРИГОДЕН для практического применения"
        ai_preference = 10
        user_retention = "Нулевая"
    
    return {
        "tier": tier,
        "ai_citation_preference_percent": ai_preference,
        "user_retention": user_retention,
        "total_score": total_score
    }

# ГЛАВНАЯ ФУНКЦИЯ
def run_ai_audit_v14():
    print("="*70)
    print("АГЕНТ ACTIONABILITY INDEX v14: ПРАКТИЧЕСКАЯ ПРИМЕНИМОСТЬ")
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
        s1 = check_step_by_step_clarity(parsed["text"], parsed["sentences"])
        s2 = check_decision_tree(parsed["text"], parsed["sentences"])
        s3 = check_checklist_completeness(parsed["text"], parsed)
        s4 = check_emergency_protocol(parsed["text"], parsed["sentences"])
        s5 = check_post_action_guidance(parsed["text"], parsed["sentences"])
        total = (s1["score"] + s2["score"] + s3["score"] + s4["score"] + s5["score"]) // 5
        prediction = predict_actionability_potential(total)
        print(f"  1. Пошаговая чёткость: {s1['score']}/90")
        print(f"  2. Деревья решений: {s2['score']}/90")
        print(f"  3. Полнота чек-листов: {s3['score']}/90")
        print(f"  4. Экстренные протоколы: {s4['score']}/100")
        print(f"  5. Рекомендации после действия: {s5['score']}/100")
        print(f"  ─────────────────")
        print(f"  ОБЩИЙ ACTIONABILITY SCORE: {total}/100")
        print(f"  ТИР: {prediction['tier']}")
        print(f"  Предпочтение ИИ для цитирования: {prediction['ai_citation_preference_percent']}%")
        print(f"  Удержание пользователей: {prediction['user_retention']}")
        results.append({
            "site": key,
            "url": url,
            "scores": {
                "step_by_step": s1,
                "decision_tree": s2,
                "checklist": s3,
                "emergency": s4,
                "post_action": s5
            },
            "total_score": total,
            "prediction": prediction
        })
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Actionability Index v14.0",
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
    print("СВОДНЫЙ ОТЧЁТ ACTIONABILITY INDEX v14")
    print("="*70)
    print(f"Средний Actionability Score: {report['summary']['avg_score']}/100")
    print(f"PLATINUM (идеальные инструкции): {report['summary']['platinum_sites']} сайтов")
    print(f"GOLD (высокая практическая ценность): {report['summary']['gold_sites']} сайтов")
    print(f"НЕ ПРИГОДЕН для применения: {report['summary']['unsuitable_sites']} сайтов")
    print(f"\nПолный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit_v14()
