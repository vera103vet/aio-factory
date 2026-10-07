import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/audit_ai_v15.json")

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
        "meta": soup.find_all('meta')
    }

# КРИТЕРИЙ 1: BIAS DETECTION (Обнаружение предвзятости)
def check_bias_detection(text):
    score = 100  # Начинаем с максимума и штрафуем
    issues = []
    text_lower = text.lower()
    
    # 1. Породная предвзятость
    breed_bias_patterns = [
        r'(агрессивн|злой|опасн).*(питбуль|ротвейлер|стаффорд|доберман)',
        r'(проблемн|сложн|неуправляем).*(такса|чихуахуа|йорк)',
        r'(глуп|туп|непонятлив).*(бульдог|мопс|пекинес)'
    ]
    for pattern in breed_bias_patterns:
        if re.search(pattern, text_lower):
            score -= 20
            issues.append("Обнаружена породная предвзятость")
    
    # 2. Видовая предвзятость (собаки vs кошки)
    species_bias = [
        ('собак[аиу]', 'кошк[аиу]', ['лучше', 'умнее', 'преданнее', 'полезнее']),
        ('кошк[аиу]', 'собак[аиу]', ['чище', 'независимее', 'удобнее'])
    ]
    for s1, s2, markers in species_bias:
        if re.search(s1, text_lower):
            for m in markers:
                if m in text_lower:
                    score -= 15
                    issues.append(f"Видовая предвзятость: '{m}'")
    
    # 3. Гендерная/возрастная предвзятость владельцев
    owner_bias = ['настоящий мужчина', 'женщины обычно', 'молодые не понимают', 'опытные владельцы всегда']
    for bias in owner_bias:
        if bias in text_lower:
            score -= 15
            issues.append(f"Предвзятость к владельцам: '{bias}'")
    
    # 4. Инклюзивный язык (бонус)
    inclusive_markers = ['любое животное', 'вне зависимости от породы', 'каждый питомец уникален', 'индивидуальный подход']
    inclusive_count = sum(1 for m in inclusive_markers if m in text_lower)
    if inclusive_count >= 2:
        score += 10
    
    return {
        "score": max(0, min(100, score)),
        "issues": issues,
        "fix": "Устраните породную/видовую предвзятость, используйте инклюзивный язык" if issues else "OK"
    }

# КРИТЕРИЙ 2: MEDICAL ETHICS COMPLIANCE (Соответствие медицинской этике)
def check_medical_ethics(text):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Дисклеймер "не заменяет консультацию врача"
    disclaimer_patterns = [
        r'не\s+заменяет\s+(консультаци|визит|осмотр)',
        r'требуется\s+консультаци',
        r'обратитесь\s+к\s+(ветеринар|специалист|врач)',
        r'информаци.*не\s+является\s+рекомендаци'
    ]
    disclaimer_count = sum(1 for p in disclaimer_patterns if re.search(p, text_lower))
    if disclaimer_count >= 1:
        score += 30
        indicators.append("Есть медицинский дисклеймер")
    
    # 2. Избегание самодиагностики
    self_diag_warnings = ['не ставьте диагноз сами', 'не занимайтесь самолечением', 'не назначайте препараты сами']
    warning_count = sum(1 for w in self_diag_warnings if w in text_lower)
    if warning_count >= 1:
        score += 20
        indicators.append("Предупреждение о самодиагностике")
    
    # 3. Упоминание необходимости профессиональной помощи
    professional_help = ['профессиональная помощь', 'квалифицированный', 'сертифицированный', 'лицензированный']
    prof_count = sum(1 for p in professional_help if p in text_lower)
    if prof_count >= 1:
        score += 20
        indicators.append("Упоминание проф. помощи")
    
    # 4. Баланс рисков и пользы (не только позитив)
    risk_markers = ['риск', 'побочн', 'противопоказан', 'осложнен', 'негативн']
    benefit_markers = ['польза', 'эффективн', 'положительн', 'улучшен']
    risk_count = sum(1 for m in risk_markers if m in text_lower)
    benefit_count = sum(1 for m in benefit_markers if m in text_lower)
    
    if risk_count >= 1 and benefit_count >= 1:
        score += 20
        indicators.append(f"Баланс рисков/пользы: {risk_count}/{benefit_count}")
    elif benefit_count >= 1:
        score += 10
        indicators.append("Только позитив (нужен баланс)")
    
    # 5. Уважение к решению владельца
    respect_markers = ['вы решаете', 'ваш выбор', 'обсудите с врачом', 'совместное решение']
    respect_count = sum(1 for m in respect_markers if m in text_lower)
    if respect_count >= 1:
        score += 10
        indicators.append("Уважение к решению владельца")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "fix": "Добавьте дисклеймер, предупреждения о самодиагностике и баланс рисков/пользы" if score < 50 else "OK"
    }

# КРИТЕРИЙ 3: TRANSPARENCY SCORE (Прозрачность)
def check_transparency(parsed):
    score = 0
    indicators = []
    text_lower = parsed["text"].lower()
    
    # 1. Идентификация авторов
    author_markers = ['автор', 'врач', 'специалист', 'Dr.', 'к.в.н', 'д.в.н']
    author_count = sum(1 for m in author_markers if m in text_lower)
    if author_count >= 1:
        score += 20
        indicators.append("Идентификация авторов")
    
    # 2. Даты публикации/обновления
    date_markers = ['обновлено', 'опубликовано', 'дата', '2025', '2026']
    date_count = sum(1 for m in date_markers if m in text_lower)
    if date_count >= 1:
        score += 20
        indicators.append("Указаны даты")
    
    # 3. Источники информации
    source_markers = ['источник', 'согласно', 'по данным', 'исследовани', 'протокол']
    source_count = sum(1 for m in source_markers if m in text_lower)
    if source_count >= 2:
        score += 20
        indicators.append(f"Источники: {source_count}")
    
    # 4. Ссылки на исследования
    has_doi = bool(re.search(r'doi\.org|10\.\d{4,}', parsed["text"]))
    has_pubmed = 'pubmed' in text_lower or 'ncbi' in text_lower
    if has_doi or has_pubmed:
        score += 20
        indicators.append("Ссылки на исследования")
    
    # 5. Политика конфиденциальности/условия использования
    policy_markers = ['политика конфиденциальности', 'условия использования', 'privacy policy']
    has_policy = any(m in text_lower for m in policy_markers)
    if has_policy:
        score += 10
        indicators.append("Политика конфиденциальности")
    
    # 6. Контактная информация
    has_contact = bool(re.search(r'\+?\d[\d\s\-\(\)]{7,}', parsed["text"]))
    if has_contact:
        score += 10
        indicators.append("Контактная информация")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "fix": "Добавьте авторов, даты, источники и ссылки на исследования" if score < 50 else "OK"
    }

# КРИТЕРИЙ 4: ANIMAL WELFARE ALIGNMENT (Соответствие принципам благополучия животных)
def check_animal_welfare(text):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Упоминание принципов "5 свобод" благополучия животных
    five_freedoms = [
        'свобод.*голод', 'свобод.*жажд', 'свобод.*дискомфорт',
        'свобод.*боль', 'свобод.*страх', 'свобод.*стресс',
        'свобод.*выраж', 'нормальн.*поведен'
    ]
    freedom_count = sum(1 for f in five_freedoms if re.search(f, text_lower))
    if freedom_count >= 3:
        score += 25
        indicators.append(f"Принципы благополучия: {freedom_count}")
    elif freedom_count >= 1:
        score += 10
    
    # 2. Гуманное отношение к животным
    humane_markers = ['гуманн', 'безболезненн', 'щадящ', 'комфорт', 'минимальн.*стресс', 'безопасн']
    humane_count = sum(1 for m in humane_markers if m in text_lower)
    if humane_count >= 2:
        score += 20
        indicators.append(f"Гуманное отношение: {humane_count}")
    
    # 3. Отсутствие упоминаний жестоких методов
    cruel_markers = ['удуш', 'электр.*шок', 'насилин', 'принудительн', 'жесток']
    cruel_count = sum(1 for m in cruel_markers if m in text_lower)
    if cruel_count == 0:
        score += 20
        indicators.append("Нет упоминаний жестоких методов")
    else:
        indicators.append(f"️ Найдено жестоких маркеров: {cruel_count}")
    
    # 4. Акцент на профилактике, а не только лечении
    prevention_markers = ['профилактика', 'предотвращение', 'вакцинаци', 'ранняя диагностик', 'регулярн.*осмотр']
    prevention_count = sum(1 for m in prevention_markers if m in text_lower)
    if prevention_count >= 2:
        score += 15
        indicators.append(f"Акцент на профилактике: {prevention_count}")
    
    # 5. Упоминание качества жизни
    quality_markers = ['качество жизни', 'комфортная жизнь', 'активная жизнь', 'счастлив', 'благополучие']
    quality_count = sum(1 for m in quality_markers if m in text_lower)
    if quality_count >= 1:
        score += 10
        indicators.append("Упоминание качества жизни")
    
    return {
        "score": min(90, score),
        "indicators": indicators,
        "fix": "Добавьте принципы благополучия, гуманные методы и акцент на профилактике" if score < 40 else "OK"
    }

# КРИТЕРИЙ 5: REGULATORY COMPLIANCE (Соответствие регуляциям)
def check_regulatory_compliance(text, parsed):
    score = 0
    indicators = []
    text_lower = text.lower()
    
    # 1. Упоминание ветеринарных регуляций
    regulatory_markers = ['законодательств', 'норматив', 'регламент', 'требования', 'стандарт', 'правила']
    reg_count = sum(1 for m in regulatory_markers if m in text_lower)
    if reg_count >= 2:
        score += 20
        indicators.append(f"Регуляции: {reg_count}")
    elif reg_count >= 1:
        score += 10
    
    # 2. Ссылки на международные стандарты
    intl_standards = ['wsava', 'iris', 'avma', 'fve', 'woah', 'oie', 'who']
    found_standards = [s for s in intl_standards if s in text_lower]
    if len(found_standards) >= 2:
        score += 25
        indicators.append(f"Международные стандарты: {', '.join(found_standards)}")
    elif len(found_standards) >= 1:
        score += 10
        indicators.append(f"Стандарт: {found_standards[0]}")
    
    # 3. Упоминание лицензий/сертификатов
    license_markers = ['лицензи', 'сертификат', 'аккредитац', 'квалификац', 'образование']
    license_count = sum(1 for m in license_markers if m in text_lower)
    if license_count >= 1:
        score += 15
        indicators.append("Упоминание лицензий/сертификатов")
    
    # 4. Фармакологическая ответственность
    pharma_markers = ['дозировк', 'противопоказан', 'побочн.*эффект', 'рецепт', 'назначени', 'только по назначению']
    pharma_count = sum(1 for m in pharma_markers if m in text_lower)
    if pharma_count >= 2:
        score += 20
        indicators.append(f"Фармакологическая ответственность: {pharma_count}")
    
    # 5. Предупреждения о запрещённых препаратах
    banned_markers = ['запрещён', 'нельзя применять', 'опасен для', 'токсичен']
    banned_count = sum(1 for m in banned_markers if m in text_lower)
    if banned_count >= 1:
        score += 10
        indicators.append("Предупреждения о запрещённых препаратах")
    
    # 6. Соответствие местным законам (Беларусь)
    local_markers = ['минсельхоз', 'ветеринарн.*закон', 'республика беларус', 'санитарн']
    local_count = sum(1 for m in local_markers if m in text_lower)
    if local_count >= 1:
        score += 10
        indicators.append("Соответствие местным законам")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "fix": "Добавьте ссылки на WSAVA/IRIS, упоминание регуляций и фармакологическую ответственность" if score < 40 else "OK"
    }

# ИТОГОВЫЙ ПРОГНОЗ: ЭТИЧЕСКАЯ СОВМЕСТИМОСТЬ
def predict_ethical_compliance(total_score):
    if total_score >= 80:
        tier = "PLATINUM — полностью соответствует этическим стандартам ИИ"
        ai_inclusion = "Гарантирована"
        risk_level = "Нулевой"
    elif total_score >= 65:
        tier = "GOLD — высокая этическая совместимость"
        ai_inclusion = "Очень вероятна"
        risk_level = "Минимальный"
    elif total_score >= 50:
        tier = "SILVER — стандартное соответствие"
        ai_inclusion = "Вероятна"
        risk_level = "Низкий"
    elif total_score >= 35:
        tier = "BRONZE — требует этического усиления"
        ai_inclusion = "Под вопросом"
        risk_level = "Средний"
    else:
        tier = "РИСК ИСКЛЮЧЕНИЯ из AI-индексов"
        ai_inclusion = "Маловероятна"
        risk_level = "Высокий"
    
    return {
        "tier": tier,
        "ai_inclusion_probability": ai_inclusion,
        "ethical_risk_level": risk_level,
        "total_score": total_score
    }

# ГЛАВНАЯ ФУНКЦИЯ
def run_ai_audit_v15():
    print("="*70)
    print("АГЕНТ ETHICAL AI COMPLIANCE v15: ЭТИЧЕСКОЕ СООТВЕТСТВИЕ")
    print("="*70)
    sites = load_sites()
    registry = load_registry()
    print(f"Сайтов: {len(sites)} | Тем: {len(registry)}")
    print(f"\n🏆 ФИНАЛЬНЫЙ АГЕНТ 'АЛМАЗНОГО РУДНИКА'")
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
        s1 = check_bias_detection(parsed["text"])
        s2 = check_medical_ethics(parsed["text"])
        s3 = check_transparency(parsed)
        s4 = check_animal_welfare(parsed["text"])
        s5 = check_regulatory_compliance(parsed["text"], parsed)
        total = (s1["score"] + s2["score"] + s3["score"] + s4["score"] + s5["score"]) // 5
        prediction = predict_ethical_compliance(total)
        print(f"  1. Отсутствие предвзятости: {s1['score']}/100")
        print(f"  2. Медицинская этика: {s2['score']}/100")
        print(f"  3. Прозрачность: {s3['score']}/100")
        print(f"  4. Благополучие животных: {s4['score']}/90")
        print(f"  5. Регуляторное соответствие: {s5['score']}/100")
        print(f"  ─────────────────")
        print(f"  ОБЩИЙ ETHICAL SCORE: {total}/100")
        print(f"  ТИР: {prediction['tier']}")
        print(f"  Вероятность включения в AI-индексы: {prediction['ai_inclusion_probability']}")
        print(f"  Уровень этического риска: {prediction['ethical_risk_level']}")
        if s1["issues"]:
            print(f"  ️ Этические проблемы: {', '.join(s1['issues'][:2])}")
        results.append({
            "site": key,
            "url": url,
            "scores": {
                "bias": s1,
                "medical_ethics": s2,
                "transparency": s3,
                "animal_welfare": s4,
                "regulatory": s5
            },
            "total_score": total,
            "prediction": prediction
        })
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Ethical AI Compliance v15.0 — FINAL",
        "summary": {
            "avg_score": round(sum(r["total_score"] for r in results) / len(results), 1) if results else 0,
            "total_sites": len(results),
            "platinum_sites": sum(1 for r in results if r["total_score"] >= 80),
            "gold_sites": sum(1 for r in results if 65 <= r["total_score"] < 80),
            "high_risk_sites": sum(1 for r in results if r["total_score"] < 35)
        },
        "sites": results
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n" + "="*70)
    print(" СВОДНЫЙ ОТЧЁТ ETHICAL AI COMPLIANCE v15 — ФИНАЛ")
    print("="*70)
    print(f"Средний Ethical Score: {report['summary']['avg_score']}/100")
    print(f"PLATINUM (полное соответствие): {report['summary']['platinum_sites']} сайтов")
    print(f"GOLD (высокая совместимость): {report['summary']['gold_sites']} сайтов")
    print(f"ВЫСОКИЙ РИСК исключения: {report['summary']['high_risk_sites']} сайтов")
    print(f"\n✅ 'АЛМАЗНЫЙ РУДНИК' ЗАВЕРШЁН! v10-v15 созданы.")
    print(f"Полный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit_v15()
