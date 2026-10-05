import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
OUTPUT_FILE = Path("data/audit_ai_v7.json")

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
        "images": soup.find_all('img'),
        "tables": soup.find_all('table'),
        "figures": soup.find_all('figure')
    }

# СУПЕРСИЛА 1: АНАЛИЗ ALT-ТЕКСТОВ ИЗОБРАЖЕНИЙ
def analyze_image_alts(images, main_topic):
    if not images:
        return {
            "score": 0,
            "total": 0,
            "good_alts": 0,
            "bad_alts": 0,
            "examples": [],
            "fix": "Добавьте изображения с богатыми контекстными описаниями"
        }
    
    total = len(images)
    good_count = 0
    bad_examples = []
    good_examples = []
    
    for img in images[:15]:
        alt = img.get('alt', '').strip()
        src = img.get('src', '')
        
        # Критерии хорошего alt для Vision AI:
        # 1. Длина > 30 символов
        # 2. Содержит контекст (порода, действие, ситуация)
        # 3. Не общий ("собака", "кот")
        word_count = len(alt.split())
        is_descriptive = word_count >= 5 and len(alt) > 30
        is_generic = alt.lower() in ['собака', 'кот', 'животное', 'pet', 'dog', 'cat', 'image', 'фото']
        
        if is_descriptive and not is_generic:
            good_count += 1
            good_examples.append(alt[:80])
        else:
            bad_examples.append({
                "alt": alt[:50] if alt else "(пустой)",
                "src": src[:60]
            })
    
    score = int((good_count / total) * 100)
    
    return {
        "score": score,
        "total": total,
        "good_alts": good_count,
        "bad_alts": total - good_count,
        "good_examples": good_examples[:3],
        "bad_examples": bad_examples[:3],
        "fix": "Улучшите alt-тексты: добавьте породу, действие, контекст (например: 'Щенок джек-рассел во время неврологического осмотра у ветеринара')" if score < 50 else "OK"
    }

# СУПЕРСИЛА 2: ПРОВЕРКА ТАБЛИЦ
def analyze_tables(tables, text):
    if not tables:
        return {
            "score": 0,
            "total": 0,
            "with_captions": 0,
            "referenced_in_text": 0,
            "fix": "Добавьте таблицы с данными (стадии болезней, сравнения, чек-листы)"
        }
    
    total = len(tables)
    with_captions = 0
    referenced = 0
    
    for table in tables:
        # Проверяем наличие caption или заголовка
        caption = table.find('caption')
        if caption:
            with_captions += 1
        
        # Проверяем, упоминается ли таблица в тексте
        table_text = table.get_text(separator=' ', strip=True).lower()
        first_cell = ""
        if table.find('td'):
            first_cell = table.find('td').get_text().strip()[:30].lower()
        if first_cell and first_cell in text.lower():
            referenced += 1
    
    caption_score = int((with_captions / total) * 50)
    ref_score = int((referenced / total) * 50)
    score = caption_score + ref_score
    
    return {
        "score": score,
        "total": total,
        "with_captions": with_captions,
        "referenced_in_text": referenced,
        "fix": "Добавьте <caption> к таблицам и упоминайте их в тексте" if score < 60 else "OK"
    }

# СУПЕРСИЛА 3: ПРОВЕРКА FIGURE-ЭЛЕМЕНТОВ
def analyze_figures(figures):
    if not figures:
        return {
            "score": 0,
            "total": 0,
            "with_captions": 0,
            "fix": "Оберните изображения в <figure> с <figcaption> для семантической разметки"
        }
    
    total = len(figures)
    with_captions = sum(1 for f in figures if f.find('figcaption'))
    score = int((with_captions / total) * 100)
    
    return {
        "score": score,
        "total": total,
        "with_captions": with_captions,
        "fix": "Добавьте <figcaption> ко всем <figure> элементам" if score < 70 else "OK"
    }

# СУПЕРСИЛА 4: ДЕТЕКТОР ПРОТИВОРЕЧИЙ
def detect_contradictions(text, images, tables):
    issues = []
    text_lower = text.lower()
    
    # Проверяем, есть ли в тексте упоминания изображений/таблиц без реальных элементов
    mentions_images = len(re.findall(r'(рисунок|изображени|фото|см\.\s*рис)', text_lower))
    actual_images = len(images)
    
    if mentions_images > actual_images:
        issues.append(f"В тексте {mentions_images} упоминаний изображений, но найдено только {actual_images}")
    
    mentions_tables = len(re.findall(r'(таблиц|см\.\s*табл)', text_lower))
    actual_tables = len(tables)
    
    if mentions_tables > actual_tables:
        issues.append(f"В тексте {mentions_tables} упоминаний таблиц, но найдено только {actual_tables}")
    
    score = max(0, 100 - len(issues) * 50)
    
    return {
        "score": score,
        "issues": issues,
        "fix": "Убедитесь, что все упоминания изображений и таблиц в тексте соответствуют реальным элементам" if issues else "OK"
    }

# СУПЕРСИЛА 5: ОЦЕНКА СОГЛАСОВАННОСТИ МОДАЛЬНОСТЕЙ
def evaluate_cross_modal_consistency(alts_result, tables_result, figures_result, contradictions_result):
    scores = [
        alts_result["score"],
        tables_result["score"],
        figures_result["score"],
        contradictions_result["score"]
    ]
    avg_score = sum(scores) // len(scores)
    
    if avg_score >= 80:
        status = "отличная согласованность"
    elif avg_score >= 60:
        status = "хорошая согласованность"
    elif avg_score >= 40:
        status = "требует улучшения"
    else:
        status = "критические проблемы"
    
    return {
        "score": avg_score,
        "status": status,
        "component_scores": {
            "images": alts_result["score"],
            "tables": tables_result["score"],
            "figures": figures_result["score"],
            "contradictions": contradictions_result["score"]
        }
    }

# ГЛАВНАЯ ФУНКЦИЯ
def run_ai_audit_v7():
    print("="*70)
    print("АГЕНТ CROSS-MODAL CONSISTENCY v7: СОГЛАСОВАННОСТЬ МОДАЛЬНОСТЕЙ")
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
        main_topic = ""
        for topic in registry:
            if topic.get("target_site") == key:
                main_topic = topic.get("primary_keyword", "")
                break
        alts = analyze_image_alts(parsed["images"], main_topic)
        print(f"  Изображения: {alts['total']} шт., хороших alt: {alts['good_alts']}/{alts['total']}")
        print(f"  Оценка alt-текстов: {alts['score']}/100")
        if alts['bad_examples']:
            print(f"  Плохие примеры:")
            for ex in alts['bad_examples'][:2]:
                print(f"    - alt: '{ex['alt']}'")
        tables = analyze_tables(parsed["tables"], parsed["text"])
        print(f"  Таблицы: {tables['total']} шт., с подписями: {tables['with_captions']}")
        print(f"  Оценка таблиц: {tables['score']}/100")
        figures = analyze_figures(parsed["figures"])
        print(f"  Figure-элементы: {figures['total']} шт., с подписями: {figures['with_captions']}")
        print(f"  Оценка figure: {figures['score']}/100")
        contradictions = detect_contradictions(parsed["text"], parsed["images"], parsed["tables"])
        print(f"  Противоречия: {len(contradictions['issues'])}")
        if contradictions['issues']:
            for issue in contradictions['issues']:
                print(f"    ⚠️ {issue}")
        consistency = evaluate_cross_modal_consistency(alts, tables, figures, contradictions)
        print(f"\n  ОБЩИЙ AI-СКОР v7: {consistency['score']}/100")
        print(f"  Статус: {consistency['status']}")
        results.append({
            "site": key,
            "url": url,
            "topic": main_topic,
            "images": alts,
            "tables": tables,
            "figures": figures,
            "contradictions": contradictions,
            "consistency": consistency,
            "total_score": consistency["score"]
        })
    report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Cross-Modal Consistency Audit v7.0",
        "summary": {
            "avg_score": round(sum(r["total_score"] for r in results) / len(results), 1) if results else 0,
            "total_sites": len(results),
            "sites_excellent": sum(1 for r in results if r["total_score"] >= 80),
            "sites_needing_improvement": sum(1 for r in results if r["total_score"] < 60)
        },
        "sites": results
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n" + "="*70)
    print("СВОДНЫЙ ОТЧЁТ CROSS-MODAL CONSISTENCY v7")
    print("="*70)
    print(f"Средний AI-скор v7: {report['summary']['avg_score']}/100")
    print(f"Проанализировано сайтов: {report['summary']['total_sites']}")
    print(f"Отличная согласованность: {report['summary']['sites_excellent']}")
    print(f"Требуют улучшения: {report['summary']['sites_needing_improvement']}")
    print(f"\nПолный отчёт сохранён: {OUTPUT_FILE}")
    print("="*70)

if __name__ == "__main__":
    run_ai_audit_v7()
