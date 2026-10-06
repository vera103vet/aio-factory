import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
OUTPUT_FILE = Path("data/serp_device_analysis.json")

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def fetch_html(url):
    # Эмулируем мобильный User-Agent по умолчанию, так как Google использует Mobile-First Indexing
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G996U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36"
    }
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
        "first_100_words": ' '.join(text.split()[:100]).lower(),
        "links": soup.find_all('a', href=True),
        "meta": soup.find_all('meta'),
        "tables": soup.find_all('table'),
        "lists": soup.find_all(['ul', 'ol'])
    }

# СУПЕРСИЛА 1: MOBILE UX & EMERGENCY READINESS
def check_mobile_ux(parsed):
    score = 0
    indicators = []
    issues = []
    soup = parsed["soup"]
    
    # 1. Viewport meta tag (Критично для Mobile-First)
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    if viewport and 'width=device-width' in viewport.get('content', ''):
        score += 25
        indicators.append("Viewport настроен корректно")
    else:
        issues.append("Отсутствует или некорректен meta viewport")
    
    # 2. Кликабельный телефон (Критично для ветеринарии!)
    tel_links = [a for a in parsed["links"] if a.get('href', '').startswith('tel:')]
    if len(tel_links) >= 1:
        score += 25
        indicators.append(f"Найдены кликабельные телефоны: {len(tel_links)}")
    else:
        issues.append("Нет кликабельных ссылок tel: (пользователь не может позвонить в 1 клик)")
    
    # 3. Размер первого экрана (BLUF для мобильных)
    # Проверяем, есть ли прямой ответ или призыв к действию в первых 100 словах
    mobile_intent_markers = ['позвоните', 'запишитесь', 'срочно', 'симптомы', 'что делать', 'первая помощь']
    has_early_action = any(m in parsed["first_100_words"] for m in mobile_intent_markers)
    if has_early_action:
        score += 25
        indicators.append("Ранний ответ/действие (отлично для мобильных)")
    else:
        issues.append("Нет быстрого ответа или призыва к действию в начале (высокий bounce rate на мобильных)")
    
    # 4. Отсутствие тяжелых блокирующих элементов (простая эвристика)
    # Ищем скрипты или стили, которые часто используются для попапов
    popup_indicators = len(soup.find_all(string=re.compile('подпишитесь|закрыть|cookie', re.IGNORECASE)))
    if popup_indicators == 0:
        score += 25
        indicators.append("Нет явных признаков блокирующих попапов в коде")
    else:
        score += 10
        issues.append("Возможны блокирующие элементы (попапы), ухудшающие мобильный UX")

    return {
        "score": score,
        "indicators": indicators,
        "issues": issues,
        "status": "Отлично" if score >= 75 else "Требует доработки" if score >= 50 else "Критично"
    }

# СУПЕРСИЛА 2: DESKTOP DEPTH & ENGAGEMENT
def check_desktop_depth(parsed):
    score = 0
    indicators = []
    
    # 1. Наличие таблиц (удобно на десктопе, читается ИИ)
    if len(parsed["tables"]) >= 1:
        score += 30
        indicators.append(f"Есть структурированные таблицы: {len(parsed['tables'])}")
    else:
        indicators.append("Нет таблиц (десктопным пользователям не хватает структуры)")
    
    # 2. Наличие развернутых списков
    if len(parsed["lists"]) >= 2:
        score += 30
        indicators.append(f"Хорошая списочная структура: {len(parsed['lists'])}")
    elif len(parsed["lists"]) == 1:
        score += 15
    
    # 3. Глубина контента (для десктопа оптимально > 600 слов)
    if parsed["words"] >= 800:
        score += 40
        indicators.append(f"Глубокий контент: {parsed['words']} слов (идеально для десктопа)")
    elif parsed["words"] >= 500:
        score += 25
        indicators.append(f"Средняя глубина: {parsed['words']} слов")
    else:
        indicators.append(f"Поверхностный контент: {parsed['words']} слов (мало для десктопа)")

    return {
        "score": score,
        "indicators": indicators,
        "status": "Отлично" if score >= 70 else "Требует доработки" if score >= 40 else "Слабо"
    }

# ИТОГОВЫЙ DEVICE-SPLIT СКОРИНГ
def calculate_device_scores(mobile_result, desktop_result):
    mobile_score = mobile_result["score"]
    desktop_score = desktop_result["score"]
    
    # Общий скор с weighting: Mobile важнее (Mobile-First Indexing Google)
    total_score = int(mobile_score * 0.6 + desktop_score * 0.4)
    
    # Определение статуса готовности
    if total_score >= 80:
        readiness = "PLATINUM — полностью готов к Mobile-First и Desktop"
    elif total_score >= 65:
        readiness = "GOLD — хорошая готовность"
    elif total_score >= 50:
        readiness = "SILVER — базовая готовность"
    elif total_score >= 35:
        readiness = "BRONZE — требует доработки"
    else:
        readiness = "НЕ ГОТОВ — критические проблемы"
    
    # Прогноз поведения пользователей
    if mobile_score < 50:
        mobile_prediction = "Высокий bounce rate (>70%), потеря мобильных клиентов"
    elif mobile_score < 75:
        mobile_prediction = "Средний bounce rate (40-70%), часть клиентов уходит"
    else:
        mobile_prediction = "Низкий bounce rate (<40%), хорошая конверсия"
    
    if desktop_score < 40:
        desktop_prediction = "Пользователи не задерживаются, нет глубины"
    elif desktop_score < 70:
        desktop_prediction = "Среднее время на сайте, можно улучшить"
    else:
        desktop_prediction = "Высокое вовлечение, глубокое изучение"
    
    return {
        "mobile_score": mobile_score,
        "desktop_score": desktop_score,
        "total_score": total_score,
        "readiness": readiness,
        "mobile_prediction": mobile_prediction,
        "desktop_prediction": desktop_prediction
    }

# ГЛАВНАЯ ФУНКЦИЯ
def run_device_analysis():
    print("="*70)
    print("АГЕНТ SERP & DEVICE ANALYST: МОБИЛЬНАЯ vs ДЕСКТОПНАЯ ГОТОВНОСТЬ")
    print("="*70)
    sites = load_sites()
    print(f"Сайтов для анализа: {len(sites)}")
    print(f"Принцип: Mobile-First Indexing (Google/Яндекс 2026)")
    
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
        mobile = check_mobile_ux(parsed)
        desktop = check_desktop_depth(parsed)
        final = calculate_device_scores(mobile, desktop)
        
        print(f"\n  📱 МОБИЛЬНАЯ ГОТОВНОСТЬ: {mobile['score']}/100 [{mobile['status']}]")
        for ind in mobile["indicators"]:
            print(f"    ✅ {ind}")
        for iss in mobile["issues"]:
            print(f"    ️ {iss}")
        
        print(f"\n   ДЕСКТОПНАЯ ГОТОВНОСТЬ: {desktop['score']}/100 [{desktop['status']}]")
        for ind in desktop["indicators"]:
            print(f"    ✅ {ind}")
        
        print(f"\n  ─────────────────")
        print(f"  ОБЩИЙ DEVICE SCORE: {final['total_score']}/100")
        print(f"  СТАТУС: {final['readiness']}")
        print(f"  Прогноз мобильных: {final['mobile_prediction']}")
        print(f"  Прогноз десктоп: {final['desktop_prediction']}")
        
        results.append({
            "site": key,
            "url": url,
            "mobile": mobile,
            "desktop": desktop,
            "final": final
        })
    
    # Сводная статистика
    avg_total = round(sum(r["final"]["total_score"] for r in results) / len(results), 1) if results else 0
    avg_mobile = round(sum(r["mobile"]["score"] for r in results) / len(results), 1) if results else 0
    avg_desktop = round(sum(r["desktop"]["score"] for r in results) / len(results), 1) if results else 0
    critical_mobile = sum(1 for r in results if r["mobile"]["score"] < 50)
    critical_desktop = sum(1 for r in results if r["desktop"]["score"] < 40)
    
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "SERP & Device Analyst v1.0",
        "principle": "Mobile-First Indexing (Google/Яндекс)",
        "summary": {
            "avg_total_score": avg_total,
            "avg_mobile_score": avg_mobile,
            "avg_desktop_score": avg_desktop,
            "critical_mobile_sites": critical_mobile,
            "critical_desktop_sites": critical_desktop,
            "total_sites": len(results)
        },
        "sites": results
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print("СВОДНЫЙ ОТЧЁТ SERP & DEVICE ANALYST")
    print("="*70)
    print(f"Средний общий скор: {avg_total}/100")
    print(f"Средний мобильный скор: {avg_mobile}/100")
    print(f"Средний десктопный скор: {avg_desktop}/100")
    print(f"Критических мобильных проблем: {critical_mobile} сайтов")
    print(f"Критических десктопных проблем: {critical_desktop} сайтов")
    print(f"\nПолный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_device_analysis()

# СУПЕРСИЛА 3: PERFORMANCE & CORE WEB VITALS LITE
def check_performance(parsed, response_time_ms=None):
    score = 0
    indicators = []
    issues = []
    soup = parsed["soup"]
    
    # 1. HTTPS (базовая безопасность, фактор ранжирования)
    if parsed["url"].startswith("https://"):
        score += 30
        indicators.append("HTTPS активен (безопасное соединение)")
    else:
        issues.append("Сайт работает по HTTP — Google понижает в выдаче")
    
    # 2. Время ответа сервера (эмуляция TTFB)
    if response_time_ms is not None:
        if response_time_ms < 500:
            score += 30
            indicators.append(f"TTFB: {response_time_ms}мс (отлично)")
        elif response_time_ms < 1500:
            score += 20
            indicators.append(f"TTFB: {response_time_ms}мс (приемлемо)")
        elif response_time_ms < 3000:
            score += 10
            indicators.append(f"TTFB: {response_time_ms}мс (медленно)")
        else:
            issues.append(f"TTFB: {response_time_ms}мс (критично медленно!)")
    else:
        score += 15
        indicators.append("Время ответа не замерено")
    
    # 3. Количество скриптов и стилей (тяжесть страницы)
    scripts = len(soup.find_all('script'))
    styles = len(soup.find_all('link', attrs={'rel': 'stylesheet'}))
    total_resources = scripts + styles
    
    if total_resources <= 10:
        score += 20
        indicators.append(f"Лёгкая страница: {scripts} скриптов, {styles} стилей")
    elif total_resources <= 20:
        score += 10
        indicators.append(f"Средняя нагрузка: {scripts} скриптов, {styles} стилей")
    else:
        issues.append(f"Тяжёлая страница: {scripts} скриптов, {styles} стилей")
    
    # 4. Наличие favicon (влияет на CTR в мобильной выдаче)
    favicon = soup.find('link', attrs={'rel': re.compile(r'icon', re.IGNORECASE)})
    if favicon:
        score += 20
        indicators.append("Favicon найден (улучшает CTR в SERP)")
    else:
        issues.append("Favicon отсутствует (снижает CTR в мобильной выдаче)")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "issues": issues,
        "status": "Отлично" if score >= 75 else "Требует доработки" if score >= 50 else "Критично"
    }

# СУПЕРСИЛА 4: IMAGE & CLS CHECK (Cumulative Layout Shift)
def check_image_cls(parsed):
    score = 0
    indicators = []
    issues = []
    images = parsed["soup"].find_all('img')
    total_images = len(images)
    
    if total_images == 0:
        indicators.append("Изображения отсутствуют")
        return {"score": 50, "indicators": indicators, "issues": issues, "status": "Нейтрально"}
    
    # 1. Все ли изображения имеют alt (доступность + SEO)
    images_with_alt = sum(1 for img in images if img.get('alt', '').strip())
    alt_ratio = images_with_alt / total_images
    
    if alt_ratio >= 0.9:
        score += 35
        indicators.append(f"Alt-тексты: {images_with_alt}/{total_images} (отлично)")
    elif alt_ratio >= 0.5:
        score += 20
        indicators.append(f"Alt-тексты: {images_with_alt}/{total_images} (частично)")
    else:
        score += 5
        issues.append(f"Alt-тексты: только {images_with_alt}/{total_images} (критично!)")
    
    # 2. Все ли изображения имеют width и height (CLS-фактор Google)
    images_with_dimensions = sum(1 for img in images if img.get('width') and img.get('height'))
    dim_ratio = images_with_dimensions / total_images
    
    if dim_ratio >= 0.8:
        score += 35
        indicators.append(f"Размеры изображений: {images_with_dimensions}/{total_images} (CLS защищён)")
    elif dim_ratio >= 0.5:
        score += 20
        indicators.append(f"Размеры: {images_with_dimensions}/{total_images} (риск CLS)")
    else:
        score += 5
        issues.append(f"Размеры: только {images_with_dimensions}/{total_images} (высокий CLS-риск!)")
    
    # 3. Баланс изображений и текста
    words_per_image = parsed["words"] / total_images if total_images > 0 else 0
    if 50 <= words_per_image <= 300:
        score += 30
        indicators.append(f"Баланс текст/изображения: {int(words_per_image)} слов на изображение")
    else:
        indicators.append(f"Дисбаланс: {int(words_per_image)} слов на изображение")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "issues": issues,
        "total_images": total_images,
        "status": "Отлично" if score >= 75 else "Требует доработки" if score >= 50 else "Критично"
    }

# СУПЕРСИЛА 5: HEADING STRUCTURE AUDIT
def check_heading_structure(parsed):
    score = 0
    indicators = []
    issues = []
    soup = parsed["soup"]
    
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    h1_count = len(soup.find_all('h1'))
    h2_count = len(soup.find_all('h2'))
    
    # 1. Ровно один H1 на странице (критично для SEO)
    if h1_count == 1:
        score += 35
        indicators.append("H1: ровно один (идеально)")
    elif h1_count == 0:
        score += 0
        issues.append("H1 ОТСУТСТВУЕТ (критическая SEO-ошибка)")
    else:
        score += 10
        issues.append(f"H1: найдено {h1_count} (должен быть один)")
    
    # 2. Наличие H2 (структура контента)
    if h2_count >= 2:
        score += 25
        indicators.append(f"H2: {h2_count} заголовков (хорошая структура)")
    elif h2_count == 1:
        score += 15
        indicators.append("H2: только один (мало для структуры)")
    else:
        issues.append("H2 отсутствуют (нет структуры контента)")
    
    # 3. Правильная иерархия (нет пропусков H1→H3)
    heading_levels = [int(h.name[1]) for h in headings]
    has_skips = False
    for i in range(1, len(heading_levels)):
        if heading_levels[i] - heading_levels[i-1] > 1:
            has_skips = True
            break
    
    if not has_skips and len(heading_levels) > 0:
        score += 20
        indicators.append("Иерархия заголовков корректна (без пропусков)")
    elif len(heading_levels) == 0:
        issues.append("Заголовки полностью отсутствуют")
    else:
        score += 10
        issues.append("Нарушена иерархия заголовков (есть пропуски)")
    
    # 4. Общая насыщенность заголовками
    total_headings = len(headings)
    if total_headings >= 5:
        score += 20
        indicators.append(f"Всего заголовков: {total_headings} (хорошая навигация)")
    elif total_headings >= 2:
        score += 10
        indicators.append(f"Заголовков: {total_headings} (мало)")
    
    return {
        "score": min(100, score),
        "indicators": indicators,
        "issues": issues,
        "total_headings": total_headings,
        "h1_count": h1_count,
        "status": "Отлично" if score >= 75 else "Требует доработки" if score >= 50 else "Критично"
    }

# ОБНОВЛЁННЫЙ СКОРИНГ С УЧЁТОМ 5 ПРОВЕРОК
def calculate_final_scores(mobile, desktop, performance, image_cls, headings):
    # Взвешенная формула (Mobile-First приоритет)
    weights = {
        "mobile": 0.25,
        "desktop": 0.15,
        "performance": 0.25,
        "image_cls": 0.20,
        "headings": 0.15
    }
    
    total = int(
        mobile["score"] * weights["mobile"] +
        desktop["score"] * weights["desktop"] +
        performance["score"] * weights["performance"] +
        image_cls["score"] * weights["image_cls"] +
        headings["score"] * weights["headings"]
    )
    
    if total >= 80:
        readiness = "PLATINUM — полностью готов к Mobile-First и Desktop"
    elif total >= 65:
        readiness = "GOLD — высокая готовность"
    elif total >= 50:
        readiness = "SILVER — базовая готовность"
    elif total >= 35:
        readiness = "BRONZE — требует доработки"
    else:
        readiness = "НЕ ГОТОВ — критические проблемы"
    
    return {
        "mobile_score": mobile["score"],
        "desktop_score": desktop["score"],
        "performance_score": performance["score"],
        "image_cls_score": image_cls["score"],
        "headings_score": headings["score"],
        "total_score": total,
        "readiness": readiness
    }

# ОБНОВЛЁННАЯ ГЛАВНАЯ ФУНКЦИЯ (перезаписывает старую)
def run_device_analysis():
    import time
    print("="*70)
    print("АГЕНТ SERP & DEVICE ANALYST v2.0: ПОЛНЫЙ АНАЛИЗ УСТРОЙСТВ")
    print("="*70)
    sites = load_sites()
    print(f"Сайтов для анализа: {len(sites)}")
    print(f"Принцип: Mobile-First Indexing (Google/Яндекс 2026)")
    print(f"Проверок: 5 (Mobile UX, Desktop Depth, Performance, CLS, Headings)")
    
    results = []
    for key, cfg in sites.items():
        url = cfg.get('url')
        if not url:
            continue
        print(f"\n{'='*70}")
        print(f"Анализ: {key.upper()} ({url})")
        print(f"{'='*70}")
        
        # Замер времени ответа
        start_time = time.time()
        html = fetch_html(url)
        response_time_ms = int((time.time() - start_time) * 1000) if html else None
        
        if not html:
            print(f"  Ошибка загрузки {url}")
            continue
        
        parsed = parse_site(html, url)
        
        # 5 проверок
        mobile = check_mobile_ux(parsed)
        desktop = check_desktop_depth(parsed)
        performance = check_performance(parsed, response_time_ms)
        image_cls = check_image_cls(parsed)
        headings = check_heading_structure(parsed)
        
        # Итоговый скор
        final = calculate_final_scores(mobile, desktop, performance, image_cls, headings)
        
        print(f"\n  📱 МОБИЛЬНАЯ ГОТОВНОСТЬ: {mobile['score']}/100 [{mobile['status']}]")
        for ind in mobile["indicators"]:
            print(f"    ✅ {ind}")
        for iss in mobile["issues"]:
            print(f"    ️ {iss}")
        
        print(f"\n  💻 ДЕСКТОПНАЯ ГОТОВНОСТЬ: {desktop['score']}/100 [{desktop['status']}]")
        for ind in desktop["indicators"]:
            print(f"    ✅ {ind}")
        
        print(f"\n  ⚡ ПРОИЗВОДИТЕЛЬНОСТЬ: {performance['score']}/100 [{performance['status']}]")
        for ind in performance["indicators"]:
            print(f"    ✅ {ind}")
        for iss in performance["issues"]:
            print(f"    ⚠️ {iss}")
        
        print(f"\n  🖼️ ИЗОБРАЖЕНИЯ И CLS: {image_cls['score']}/100 [{image_cls['status']}]")
        for ind in image_cls["indicators"]:
            print(f"    ✅ {ind}")
        for iss in image_cls["issues"]:
            print(f"    ⚠️ {iss}")
        
        print(f"\n  📊 СТРУКТУРА ЗАГОЛОВКОВ: {headings['score']}/100 [{headings['status']}]")
        for ind in headings["indicators"]:
            print(f"    ✅ {ind}")
        for iss in headings["issues"]:
            print(f"    ⚠️ {iss}")
        
        print(f"\n  ─────────────────")
        print(f"   ОБЩИЙ DEVICE SCORE: {final['total_score']}/100")
        print(f"  СТАТУС: {final['readiness']}")
        
        results.append({
            "site": key,
            "url": url,
            "response_time_ms": response_time_ms,
            "mobile": mobile,
            "desktop": desktop,
            "performance": performance,
            "image_cls": image_cls,
            "headings": headings,
            "final": final
        })
    
    # Сводная статистика
    avg_total = round(sum(r["final"]["total_score"] for r in results) / len(results), 1) if results else 0
    avg_mobile = round(sum(r["mobile"]["score"] for r in results) / len(results), 1) if results else 0
    avg_desktop = round(sum(r["desktop"]["score"] for r in results) / len(results), 1) if results else 0
    avg_performance = round(sum(r["performance"]["score"] for r in results) / len(results), 1) if results else 0
    avg_image = round(sum(r["image_cls"]["score"] for r in results) / len(results), 1) if results else 0
    avg_headings = round(sum(r["headings"]["score"] for r in results) / len(results), 1) if results else 0
    
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "SERP & Device Analyst v2.0 (ENHANCED)",
        "principle": "Mobile-First Indexing (Google/Яндекс)",
        "checks": ["Mobile UX", "Desktop Depth", "Performance", "Image/CLS", "Headings"],
        "summary": {
            "avg_total_score": avg_total,
            "avg_mobile_score": avg_mobile,
            "avg_desktop_score": avg_desktop,
            "avg_performance_score": avg_performance,
            "avg_image_cls_score": avg_image,
            "avg_headings_score": avg_headings,
            "total_sites": len(results)
        },
        "sites": results
    }
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print("🏆 СВОДНЫЙ ОТЧЁТ SERP & DEVICE ANALYST v2.0")
    print("="*70)
    print(f"Средний общий скор: {avg_total}/100")
    print(f"  📱 Мобильная готовность: {avg_mobile}/100")
    print(f"  💻 Десктопная готовность: {avg_desktop}/100")
    print(f"  ⚡ Производительность: {avg_performance}/100")
    print(f"  🖼️ Изображения/CLS: {avg_image}/100")
    print(f"  📊 Заголовки: {avg_headings}/100")
    print(f"\nПолный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_device_analysis()
