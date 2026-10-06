import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Конфигурация
SITES_FILE = Path("config/sites.yaml")
REGISTRY_FILE = Path("data/topic_registry.json")
DATA_DIR = Path("data")

# Пороговые значения
HIGH_POTENTIAL_THRESHOLD = 55
MEDIUM_POTENTIAL_THRESHOLD = 40

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def load_registry():
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"topics": []}

def load_json_report(filename: str) -> Dict:
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# --- МОДУЛИ АНАЛИЗА ПОТЕНЦИАЛА ТЕМ ---

def analyze_competitive_gap(report: Dict, topic: str) -> float:
    """Анализирует конкурентный разрыв по теме (из auditor_ai_v9)"""
    if "sites" not in report:
        return 50.0  # Нейтральный скор, если данных нет
    
    # Ищем средний AI-скор конкурентов
    total_score = 0
    count = 0
    for site in report.get("sites", []):
        if topic.lower() in site.get("topic", "").lower() or topic.lower() in site.get("url", "").lower():
            total_score += site.get("ai_score", 50)
            count += 1
    
    if count == 0:
        return 50.0
    
    avg_competitor_score = total_score / count
    # Чем ниже скор конкурентов, тем выше наш потенциал
    return max(0, 100 - avg_competitor_score)

def analyze_intent_coverage(report: Dict, topic: str) -> float:
    """Анализирует покрытие интента (из auditor_ai_v8)"""
    if "sites" not in report:
        return 50.0
    
    for site in report.get("sites", []):
        if topic.lower() in site.get("topic", "").lower():
            coverage = site.get("intent_coverage", 50)
            # Чем ниже покрытие, тем больше возможностей
            return max(0, 100 - coverage)
    
    return 50.0

def analyze_emotional_potential(report: Dict, topic: str) -> float:
    """Анализирует эмоциональный потенциал темы (из auditor_ai_v13)"""
    # Эмоциональные темы: болезни, экстренные случаи, уход за питомцами
    emotional_keywords = ['эпилепсия', 'приступ', 'судорог', 'срочно', 'экстрен', 'болезн', 'уход', 'питомец', 'собака', 'кошка', 'перелом', 'отравлен', 'травм', 'смерт', 'опасн', 'помощь', 'спас', 'лечен', 'симптом', 'диагноз']
    
    topic_lower = topic.lower()
    emotional_score = sum(1 for kw in emotional_keywords if kw in topic_lower)
    
    # Нормализуем до 0-100
    return min(100, emotional_score * 20)

def analyze_actionability_demand(report: Dict, topic: str) -> float:
    """Анализирует спрос на практические инструкции (из auditor_ai_v14)"""
    # Темы, требующие действий: "что делать", "как помочь", "первая помощь"
    action_keywords = ['что делать', 'как помочь', 'первая помощь', 'алгоритм', 'чек-лист', 'инструкц', 'помочь', 'лечен', 'симптом', 'признак']
    
    topic_lower = topic.lower()
    action_score = sum(1 for kw in action_keywords if kw in topic_lower)
    
    return min(100, action_score * 25)

def analyze_device_priority(report: Dict, topic: str) -> float:
    """Анализирует приоритет мобильных устройств (из serp_device_analyst)"""
    # Если тема связана с экстренными случаями — мобильный приоритет высокий
    mobile_keywords = ['срочно', 'экстрен', 'вызов', 'телефон', 'помощь', 'симптом', 'перелом', 'отравлен', 'приступ', 'судорог', 'как помочь', 'что делать']
    
    topic_lower = topic.lower()
    mobile_score = sum(1 for kw in mobile_keywords if kw in topic_lower)
    
    return min(100, mobile_score * 20 + 30)  # Базовый скор 30 + бонус за мобильность

# --- ГЛАВНЫЙ АНАЛИЗАТОР ---

def evaluate_topic_potential(topic: str, site: str) -> Dict:
    """Оценивает потенциал темы по всем измерениям"""
    
    # Загружаем отчёты аудиторов
    v9_report = load_json_report("audit_ai_v9.json")
    v8_report = load_json_report("audit_ai_v8.json")
    v13_report = load_json_report("audit_ai_v13.json")
    v14_report = load_json_report("audit_ai_v14.json")
    device_report = load_json_report("serp_device_analysis.json")
    
    # Считаем скоры по каждому измерению
    scores = {
        "competitive_gap": analyze_competitive_gap(v9_report, topic),
        "intent_coverage": analyze_intent_coverage(v8_report, topic),
        "emotional_potential": analyze_emotional_potential(v13_report, topic),
        "actionability_demand": analyze_actionability_demand(v14_report, topic),
        "device_priority": analyze_device_priority(device_report, topic)
    }
    
    # Взвешенный итоговый скор
    weights = {
        "competitive_gap": 0.30,      # 30% — конкурентный разрыв
        "intent_coverage": 0.25,      # 25% — покрытие интента
        "emotional_potential": 0.20,  # 20% — эмоциональный потенциал
        "actionability_demand": 0.15, # 15% — спрос на действия
        "device_priority": 0.10       # 10% — мобильный приоритет
    }
    
    total_score = sum(scores[k] * weights[k] for k in scores)
    
    # Определение приоритета
    if total_score >= HIGH_POTENTIAL_THRESHOLD:
        priority = "HIGH"
        recommendation = "Срочно создавать контент"
    elif total_score >= MEDIUM_POTENTIAL_THRESHOLD:
        priority = "MEDIUM"
        recommendation = "Создавать в ближайшем спринте"
    else:
        priority = "LOW"
        recommendation = "Отложить или делегировать"
    
    return {
        "topic": topic,
        "site": site,
        "scores": scores,
        "total_score": round(total_score, 1),
        "priority": priority,
        "recommendation": recommendation
    }

# --- ПРОВЕРКА КАННИБАЛИЗАЦИИ ---

def check_cannibalization(topic: str, site: str, registry) -> Tuple[bool, str]:
    """Проверяет, не занята ли тема другим сайтом (защита от каннибализации)"""
    # registry может быть списком или словарём
    if isinstance(registry, list):
        topics = registry
    elif isinstance(registry, dict):
        topics = registry.get("topics", [])
    else:
        topics = []
    
    for existing_topic in topics:
        if existing_topic.get("status") != "published":
            continue
        
        existing_site = existing_topic.get("site", "")
        existing_name = existing_topic.get("name", "").lower()
        
        # Если тема уже занята другим сайтом
        if existing_site != site and topic.lower() in existing_name:
            return False, f"Каннибализация: тема уже занята сайтом {existing_site}"
    
    return True, "Каннибализация не обнаружена"

# --- ГЕНЕРАЦИЯ СТРАТЕГИИ ---

def generate_strategy(topics: List[str], sites: Dict) -> List[Dict]:
    """Генерирует стратегию создания контента на основе анализа потенциалов"""
    strategy = []
    
    for topic in topics:
        # Оцениваем потенциал для каждого сайта
        site_scores = []
        for site_key, site_config in sites.items():
            evaluation = evaluate_topic_potential(topic, site_key)
            site_scores.append(evaluation)
        
        # Выбираем лучший сайт для темы
        best_site = max(site_scores, key=lambda x: x["total_score"])
        
        # Проверяем каннибализацию
        registry = load_registry()
        cannibalization_ok, cannibalization_msg = check_cannibalization(topic, best_site["site"], registry)
        
        # Формируем рекомендацию
        recommendation = {
            "topic": topic,
            "recommended_site": best_site["site"],
            "total_score": best_site["total_score"],
            "priority": best_site["priority"],
            "cannibalization_check": cannibalization_ok,
            "cannibalization_message": cannibalization_msg,
            "site_scores": {s["site"]: s["total_score"] for s in site_scores},
            "action": best_site["recommendation"] if cannibalization_ok else "Пропустить (каннибализация)"
        }
        
        strategy.append(recommendation)
    
    # Сортируем по приоритету и скорy
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    strategy.sort(key=lambda x: (priority_order.get(x["priority"], 3), -x["total_score"]))
    
    return strategy

# --- ГЛАВНАЯ ФУНКЦИЯ ---

def run_strategist_v2(topics: List[str] = None):
    """Главная функция запуска стратега"""
    print("="*70)
    print("🧠 STRATEGIST v2: СТРАТЕГ НОВОГО ПОКОЛЕНИЯ")
    print("="*70)
    print(f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🎯 Анализ потенциала тем на основе данных 21 агента")
    
    # Загружаем сайты
    sites = load_sites()
    print(f"📊 Сайтов в экосистеме: {len(sites)}")
    
    # Если темы не переданы, используем примеры
    if topics is None:
        topics = [
            "Что делать при первых признаках эпилепсии у собаки?",
            "Как помочь кошке при отравлении?",
            "Первая помощь при переломе лапы у собаки",
            "Симптомы и лечение диабета у кошек",
            "Как выбрать корм для щенка?"
        ]
    
    print(f"📝 Тем для анализа: {len(topics)}")
    
    # Генерируем стратегию
    print("\n" + "="*70)
    print("ШАГ 1: АНАЛИЗ ПОТЕНЦИАЛА ТЕМ")
    print("="*70)
    
    strategy = generate_strategy(topics, sites)
    
    # Выводим результаты
    print("\n" + "="*70)
    print("ШАГ 2: СТРАТЕГИЯ СОЗДАНИЯ КОНТЕНТА")
    print("="*70)
    
    high_priority = [s for s in strategy if s["priority"] == "HIGH"]
    medium_priority = [s for s in strategy if s["priority"] == "MEDIUM"]
    low_priority = [s for s in strategy if s["priority"] == "LOW"]
    
    print(f"\n🔴 HIGH приоритет (срочно): {len(high_priority)} тем")
    for item in high_priority:
        print(f"  📌 {item['topic']}")
        print(f"     Сайт: {item['recommended_site']} | Скор: {item['total_score']}")
        print(f"     Действие: {item['action']}")
        if not item["cannibalization_check"]:
            print(f"     ⚠️ {item['cannibalization_message']}")
    
    print(f"\n MEDIUM приоритет (ближайший спринт): {len(medium_priority)} тем")
    for item in medium_priority:
        print(f"  📌 {item['topic']}")
        print(f"     Сайт: {item['recommended_site']} | Скор: {item['total_score']}")
    
    print(f"\n🟢 LOW приоритет (отложить): {len(low_priority)} тем")
    for item in low_priority:
        print(f"  📌 {item['topic']}")
        print(f"     Сайт: {item['recommended_site']} | Скор: {item['total_score']}")
    
    # Сохраняем стратегию
    strategy_report = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": "Strategist v2.0",
        "total_topics": len(strategy),
        "high_priority": len(high_priority),
        "medium_priority": len(medium_priority),
        "low_priority": len(low_priority),
        "strategy": strategy
    }
    
    strategy_file = Path("data/strategy_report.json")
    with open(strategy_file, "w", encoding="utf-8") as f:
        json.dump(strategy_report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print("🏆 ИТОГОВЫЙ ОТЧЁТ STRATEGIST v2")
    print("="*70)
    print(f"📊 Всего тем проанализировано: {len(strategy)}")
    print(f"🔴 HIGH приоритет: {len(high_priority)}")
    print(f"🟡 MEDIUM приоритет: {len(medium_priority)}")
    print(f"🟢 LOW приоритет: {len(low_priority)}")
    print(f"\n📁 Стратегия сохранена: {strategy_file}")
    print("="*70)

if __name__ == "__main__":
    run_strategist_v2()
