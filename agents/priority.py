import json
import yaml
from pathlib import Path
from datetime import datetime

SITES_FILE = Path("config/sites.yaml")
REGISTRY = Path("data/topic_registry.json")
DEMAND_FILE = Path("data/search_demand.json")

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def load_registry():
    with open(REGISTRY, "r", encoding="utf-8") as f:
        return json.load(f)

def load_search_demand():
    """Загружает данные о поисковом спросе"""
    if not DEMAND_FILE.exists():
        return None
    
    with open(DEMAND_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze_seasonality(topic, keyword):
    """Оценивает сезонную актуальность темы"""
    current_month = datetime.now().month
    text = (topic + " " + keyword).lower()
    
    spring_keywords = ["клещ", "блох", "аллерг", "весенн", "вакцин", "прививк"]
    summer_keywords = ["отравлен", "жар", "укус", "насеком", "вод", "купан"]
    autumn_keywords = ["линьк", "простуд", "осенн", "иммунитет"]
    winter_keywords = ["обморож", "зимн", "праздник", "новогодн", "отравлен ед"]
    evergreen_keywords = ["хроническ", "диабет", "почек", "сердц", "онколог", "диет", "уход"]
    
    score = 0
    
    if current_month in [3, 4, 5]:
        if any(kw in text for kw in spring_keywords):
            score = 100
        elif any(kw in text for kw in evergreen_keywords):
            score = 70
    elif current_month in [6, 7, 8]:
        if any(kw in text for kw in summer_keywords):
            score = 100
        elif any(kw in text for kw in evergreen_keywords):
            score = 70
    elif current_month in [9, 10, 11]:
        if any(kw in text for kw in autumn_keywords):
            score = 100
        elif any(kw in text for kw in evergreen_keywords):
            score = 70
    elif current_month in [12, 1, 2]:
        if any(kw in text for kw in winter_keywords):
            score = 100
        elif any(kw in text for kw in evergreen_keywords):
            score = 70
    else:
        score = 50
    
    return score

def analyze_commercial_value(topic, keyword):
    """Оценивает коммерческую ценность темы"""
    text = (topic + " " + keyword).lower()
    
    high_value = ["хирург", "операци", "стационар", "реанимаци", "диагностик", "мрт", "кт", "узи"]
    medium_value = ["терапи", "лечен", "вакцин", "прививк", "осмотр", "консультаци"]
    low_value = ["уход", "питан", "диет", "профилактик", "симптом"]
    
    if any(kw in text for kw in high_value):
        return 100
    elif any(kw in text for kw in medium_value):
        return 70
    elif any(kw in text for kw in low_value):
        return 40
    else:
        return 50

def analyze_urgency(topic, keyword):
    """Оценивает срочность темы"""
    text = (topic + " " + keyword).lower()
    
    urgent_keywords = ["экстрен", "срочн", "неотложн", "остр", "травм", "отравлен", "кровотеч", "судорог", "удуш", "перегород"]
    
    if any(kw in text for kw in urgent_keywords):
        return 100
    
    moderate_urgency = ["бол", "воспален", "инфекц", "вирусн", "бактериальн"]
    if any(kw in text for kw in moderate_urgency):
        return 70
    
    return 30

def analyze_strategic_importance(topic, keyword, site_role):
    """Оценивает стратегическую важность для бренда"""
    text = (topic + " " + keyword).lower()
    
    main_site_keywords = ["ветеринар на дом", "вызов ветеринара", "минск", "103vet", "круглосуточн"]
    expert_keywords = ["хроническ", "онколог", "невролог", "кардиолог", "эндокринолог", "дерматолог"]
    
    if site_role == "main":
        if any(kw in text for kw in main_site_keywords):
            return 100
        elif any(kw in text for kw in expert_keywords):
            return 70
        else:
            return 50
    else:
        if any(kw in text for kw in expert_keywords):
            return 100
        else:
            return 60

def analyze_search_demand(keyword, demand_data):
    """Анализирует реальный поисковый спрос"""
    if not demand_data or "topics" not in demand_data:
        return 50  # Базовый балл если нет данных
    
    # Ищем тему по ключевому слову
    for topic in demand_data["topics"]:
        if topic["keyword"].lower() == keyword.lower():
            search_data = topic.get("search_data", {})
            
            # Считаем общий спрос (Google + Yandex)
            google_searches = search_data.get("google_monthly_searches", 0)
            yandex_searches = search_data.get("yandex_monthly_searches", 0)
            total_searches = google_searches + yandex_searches
            
            # Нормализуем до 100 баллов (максимум 50000 запросов)
            demand_score = min(100, (total_searches / 50000) * 100)
            
            # Учитываем тренд
            trend = search_data.get("trend_6_months", "unknown")
            trend_multiplier = {"growing": 1.2, "stable": 1.0, "declining": 0.8, "unknown": 1.0}
            demand_score *= trend_multiplier.get(trend, 1.0)
            
            # Учитываем конкуренцию (низкая конкуренция = выше приоритет)
            competition = search_data.get("competition_level", "unknown")
            competition_multiplier = {"low": 1.3, "medium": 1.0, "high": 0.7, "unknown": 1.0}
            demand_score *= competition_multiplier.get(competition, 1.0)
            
            return min(100, demand_score)
    
    return 50  # Если тема не найдена в данных

def calculate_priority(topic_data, sites, demand_data):
    """Вычисляет итоговый приоритетный балл с учётом поискового спроса"""
    topic = topic_data["topic"]
    keyword = topic_data["primary_keyword"]
    target_site = topic_data["target_site"]
    status = topic_data["status"]
    
    if status == "published":
        base_score = 0
    else:
        base_score = 20
    
    site_config = sites.get(target_site, {})
    site_role = site_config.get("role", "satellite")
    site_priority = site_config.get("priority", 2)
    
    # Оцениваем по всем критериям
    seasonality = analyze_seasonality(topic, keyword)
    commercial = analyze_commercial_value(topic, keyword)
    urgency = analyze_urgency(topic, keyword)
    strategic = analyze_strategic_importance(topic, keyword, site_role)
    search_demand = analyze_search_demand(keyword, demand_data)
    
    # НОВЫЕ ВЕСА (поисковый спрос — самый важный!)
    weights = {
        "search_demand": 0.35,
        "seasonality": 0.20,
        "commercial": 0.20,
        "urgency": 0.10,
        "strategic": 0.15
    }
    
    # Вычисляем взвешенный балл
    weighted_score = (
        search_demand * weights["search_demand"] +
        seasonality * weights["seasonality"] +
        commercial * weights["commercial"] +
        urgency * weights["urgency"] +
        strategic * weights["strategic"]
    )
    
    # Корректируем по приоритету сайта
    site_multiplier = 1.2 if site_priority == 1 else 1.0
    
    final_score = (base_score + weighted_score) * site_multiplier
    final_score = min(100, final_score)
    
    return {
        "id": topic_data["id"],
        "topic": topic,
        "keyword": keyword,
        "target_site": target_site,
        "site_role": site_role,
        "status": status,
        "priority_score": round(final_score, 1),
        "breakdown": {
            "search_demand": round(search_demand, 1),
            "seasonality": seasonality,
            "commercial": commercial,
            "urgency": urgency,
            "strategic": strategic
        }
    }

def generate_priority_report(results, demand_data):
    """Генерирует отчёт с рекомендациями"""
    
    sorted_results = sorted(results, key=lambda x: x["priority_score"], reverse=True)
    
    print("\n" + "="*70)
    print("ОТЧЁТ О ПРИОРИТЕТИЗАЦИИ ТЕМ (v2 с поисковым спросом)")
    print("="*70)
    print(f"Дата: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Всего тем проанализировано: {len(sorted_results)}")
    
    high_priority = [r for r in sorted_results if r["priority_score"] >= 70 and r["status"] != "published"]
    medium_priority = [r for r in sorted_results if 50 <= r["priority_score"] < 70 and r["status"] != "published"]
    low_priority = [r for r in sorted_results if r["priority_score"] < 50 and r["status"] != "published"]
    published = [r for r in sorted_results if r["status"] == "published"]
    
    print(f"\n🔥 ВЫСОКИЙ ПРИОРИТЕТ (≥70 баллов): {len(high_priority)} тем")
    print("-" * 70)
    for i, item in enumerate(high_priority[:10], 1):
        print(f"{i}. [{item['priority_score']}] {item['topic']}")
        print(f"   Сайт: {item['target_site']} ({item['site_role']})")
        print(f"   Ключ: {item['keyword']}")
        print(f"   Поисковый спрос: {item['breakdown']['search_demand']} | Сезонность: {item['breakdown']['seasonality']} | Коммерция: {item['breakdown']['commercial']} | Срочность: {item['breakdown']['urgency']} | Стратегия: {item['breakdown']['strategic']}")
        print()
    
    if medium_priority:
        print(f"\n️ СРЕДНИЙ ПРИОРИТЕТ (50-69 баллов): {len(medium_priority)} тем")
        print("-" * 70)
        for i, item in enumerate(medium_priority[:5], 1):
            print(f"{i}. [{item['priority_score']}] {item['topic']}")
            print(f"   Сайт: {item['target_site']}")
            print(f"   Поисковый спрос: {item['breakdown']['search_demand']}")
            print()
    
    if low_priority:
        print(f"\n📋 НИЗКИЙ ПРИОРИТЕТ (<50 баллов): {len(low_priority)} тем")
        print("-" * 70)
        for i, item in enumerate(low_priority[:5], 1):
            print(f"{i}. [{item['priority_score']}] {item['topic']}")
            print(f"   Сайт: {item['target_site']}")
            print()
    
    if published:
        print(f"\n✅ ОПУБЛИКОВАНО: {len(published)} тем")
        print("-" * 70)
        for item in published[:5]:
            print(f"  - {item['topic']} ({item['target_site']})")
    
    print("\n" + "="*70)
    print("СТРАТЕГИЧЕСКИЕ РЕКОМЕНДАЦИИ")
    print("="*70)
    
    if high_priority:
        print(f"\n1. 🎯 СРОЧНО: Начните с тем высокого приоритета")
        print(f"   Рекомендуется создать {min(3, len(high_priority))} статей в ближайшие 2 недели")
    
    current_month = datetime.now().month
    if current_month in [3, 4, 5]:
        print(f"\n2. 🗓️ СЕЗОННОСТЬ: Сейчас весна — фокус на клещи, аллергию, вакцинацию")
    elif current_month in [6, 7, 8]:
        print(f"\n2. 🗓️ СЕЗОННОСТЬ: Сейчас лето — фокус на отравления, укусы, тепловые удары")
    elif current_month in [9, 10, 11]:
        print(f"\n2. 🗓️ СЕЗОННОСТЬ: Сейчас осень — фокус на простуды, линьку, иммунитет")
    elif current_month in [12, 1, 2]:
        print(f"\n2. 🗓️ СЕЗОННОСТЬ: Сейчас зима — фокус на обморожения, новогодние отравления")
    
    print(f"\n3.  КОММЕРЦИЯ: Приоритет темам с высокой коммерческой ценностью")
    print(f"   (хирургия, диагностика, стационар)")
    
    print(f"\n4. 🔍 ПОИСКОВЫЙ СПРОС: Фокус на темы с высоким реальным спросом")
    print(f"   (данные из Google + Yandex)")
    
    print(f"\n5. 🏛️ СТРАТЕГИЯ: Укрепляйте основной сайт (103vet.by) ключевыми темами")
    print(f"   Спутники должны поддерживать основной сайт перелинковкой")

if __name__ == "__main__":
    print("="*70)
    print("АГЕНТ-ПРИОРИТИЗАТОР v2: РАНЖИРОВАНИЕ С УЧЁТОМ ПОИСКОВОГО СПРОСА")
    print("="*70)
    
    sites = load_sites()
    registry = load_registry()
    demand_data = load_search_demand()
    
    print(f"\nЗагружено сайтов: {len(sites)}")
    print(f"Загружено тем в реестре: {len(registry)}")
    
    if demand_data:
        print(f"📊 Данные о поисковом спросе: {len(demand_data.get('topics', []))} тем")
    else:
        print("⚠️  Файл search_demand.json не найден — используется базовая логика")
    
    results = []
    for topic_data in registry:
        priority_data = calculate_priority(topic_data, sites, demand_data)
        results.append(priority_data)
    
    generate_priority_report(results, demand_data)
    
    output_file = Path("data/priority_report.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Результаты сохранены в: {output_file}")
