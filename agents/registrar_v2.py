import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import uuid

SITES_FILE = Path("config/sites.yaml")
REGISTRY_FILE = Path("data/topic_registry.json")
STRATEGY_FILE = Path("data/strategy_report.json")
DATA_DIR = Path("data")

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]

def load_registry():
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("topics", [])
    return []

def save_registry(topics):
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump({"topics": topics}, f, ensure_ascii=False, indent=2)

def load_strategy():
    if STRATEGY_FILE.exists():
        with open(STRATEGY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_json_report(filename):
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# === МОДУЛЬ ТЕМАТИЧЕСКОГО СООТВЕТСТВИЯ ===

SITE_THEMES = {
    "main": ["терапия", "диагностика", "профилактика", "вакцинация", "осмотр", "консультация", "общая"],
    "nevrolog": ["неврология", "эпилепсия", "судороги", "нервная", "мозг", "позвоночник", "паралич", "инсульт", "приступ"],
    "usyplenie": ["усыпление", "эвтаназия", "конец жизни", "паллиатив", "хронические", "онкология", "неизлечимые", "терминал"],
    "vetminsk": ["минск", "хирургия", "травмы", "переломы", "операции", "скорая", "экстренная"]
}

TOPIC_CATEGORIES = {
    "neurology": ["эпилепсия", "судорог", "приступ", "нервн", "мозг", "позвоночн", "паралич", "инсульт"],
    "emergency": ["перелом", "травм", "скорая", "экстрен", "срочно", "первая помощь", "отравлен"],
    "end_of_life": ["усыпление", "эвтаназия", "конец жизни", "паллиатив", "неизлечим", "терминальн", "онколог", "рак"],
    "general": ["симптом", "диагноз", "лечен", "болезн", "профилактик", "вакцин", "осмотр", "диабет"],
    "nutrition": ["корм", "питан", "диет", "рацион", "щенок", "котён"],
    "surgery": ["операци", "хирург", "наркоз", "шов"]
}

def get_topic_categories(topic_name):
    topic_lower = topic_name.lower()
    matched = []
    for category, keywords in TOPIC_CATEGORIES.items():
        if any(kw in topic_lower for kw in keywords):
            matched.append(category)
    return matched

def find_best_site_for_topic(topic_name, sites):
    topic_categories = get_topic_categories(topic_name)
    topic_lower = topic_name.lower()
    
    # Этические ограничения
    nutrition_keywords = ["корм", "питан", "диет", "рацион", "вакцин", "профилактик", "щенок", "котён"]
    if any(kw in topic_lower for kw in nutrition_keywords):
        if "usyplenie" in sites:
            pass  # просто не будем выбирать этот сайт
    
    site_scores = {}
    for site_key in sites.keys():
        site_themes = SITE_THEMES.get(site_key, [])
        site_themes_str = " ".join(site_themes)
        score = 0
        
        if "neurology" in topic_categories and ("неврология" in site_themes_str or "эпилепсия" in site_themes_str or "судороги" in site_themes_str or "приступ" in site_themes_str):
            score += 30
        if "emergency" in topic_categories and ("хирургия" in site_themes_str or "травмы" in site_themes_str):
            score += 25
        if "end_of_life" in topic_categories and ("усыпление" in site_themes_str or "паллиатив" in site_themes_str):
            score += 30
        if "general" in topic_categories and ("терапия" in site_themes_str or "диагностика" in site_themes_str):
            score += 20
        if "nutrition" in topic_categories and ("терапия" in site_themes_str or "профилактика" in site_themes_str):
            score += 15
        if "surgery" in topic_categories and "хирургия" in site_themes_str:
            score += 25
        
        # Этический штраф: питание/профилактика на сайте усыпления
        if site_key == "usyplenie" and any(kw in topic_lower for kw in nutrition_keywords):
            score = -100
        
        site_scores[site_key] = score
    
    if not site_scores or max(site_scores.values()) <= 0:
        return "main", 0, "Тема не соответствует специализации, выбран main"
    
    best_site = max(site_scores, key=site_scores.get)
    best_score = site_scores[best_site]
    
    if best_score < 15:
        return "main", best_score, "Низкое соответствие, рекомендуется main"
    
    return best_site, best_score, "Соответствие подтверждено"

# === МОДУЛИ ОБОГАЩЕНИЯ ===

def enrich_with_emotional_targets(topic_name):
    topic_lower = topic_name.lower()
    high_emotion = ["эпилепсия", "диабет", "рак", "онколог", "приступ", "судорог", "срочно", "экстрен", "отравлен", "перелом", "травм", "смерт", "опасн", "инсульт", "первые признаки", "симптомы"]
    medium_emotion = ["болезн", "лечен", "симптом", "диагноз", "уход", "питомец"]
    
    high_count = sum(1 for kw in high_emotion if kw in topic_lower)
    medium_count = sum(1 for kw in medium_emotion if kw in topic_lower)
    
    if high_count >= 2:
        return {"target_emotional_tier": "PLATINUM", "required_empathy_markers": ["Мы понимаем ваше беспокойство", "ваш любимый питомец", "вы не одни"], "storytelling_required": True, "min_empathy_score": 80}
    elif high_count >= 1 or medium_count >= 2:
        return {"target_emotional_tier": "GOLD", "required_empathy_markers": ["ваш питомец", "понимаем"], "storytelling_required": True, "min_empathy_score": 65}
    else:
        return {"target_emotional_tier": "SILVER", "required_empathy_markers": ["питомец"], "storytelling_required": False, "min_empathy_score": 50}

def enrich_with_actionability_targets(topic_name):
    topic_lower = topic_name.lower()
    action_kw = ["что делать", "как помочь", "первая помощь", "алгоритм", "чек-лист", "инструкц", "помочь", "лечен"]
    emergency_kw = ["срочно", "экстрен", "перелом", "отравлен", "приступ"]
    
    action_count = sum(1 for kw in action_kw if kw in topic_lower)
    emergency_count = sum(1 for kw in emergency_kw if kw in topic_lower)
    
    required = []
    if emergency_count >= 1:
        required.extend(["emergency_protocol", "decision_tree", "tel_link"])
    if action_count >= 2:
        required.extend(["checklist", "step_by_step", "decision_tree"])
    elif action_count >= 1:
        required.extend(["checklist", "decision_tree"])
    
    return {"required_actionability_elements": required, "min_actionability_score": 70 if len(required) >= 3 else 50, "emergency_priority": emergency_count >= 1}

def enrich_with_authority_sources(topic_name):
    topic_lower = topic_name.lower()
    medical = ["эпилепсия", "диабет", "болезн", "лечен", "симптом", "диагноз", "препарат"]
    emergency = ["перелом", "отравлен", "травм", "срочно", "экстрен"]
    
    sources = []
    if any(kw in topic_lower for kw in medical):
        sources.extend(["WSAVA", "IRIS", "evidence-based"])
    if any(kw in topic_lower for kw in emergency):
        sources.extend(["emergency_protocol", "first_aid_guidelines"])
    
    return {"authority_sources": sources, "min_authority_score": 60 if len(sources) >= 2 else 40, "requires_disclaimer": True}

def enrich_with_device_priority(topic_name):
    topic_lower = topic_name.lower()
    mobile_kw = ["срочно", "экстрен", "вызов", "телефон", "помощь", "симптом", "перелом", "отравлен", "приступ", "что делать", "как помочь", "первая помощь"]
    
    mobile_score = sum(1 for kw in mobile_kw if kw in topic_lower)
    
    if mobile_score >= 2:
        return {"device_priority": "MOBILE_FIRST", "requires_tel_link": True, "requires_bluf": True, "min_mobile_score": 75}
    elif mobile_score >= 1:
        return {"device_priority": "BALANCED", "requires_tel_link": True, "requires_bluf": True, "min_mobile_score": 60}
    else:
        return {"device_priority": "DESKTOP_FOCUSED", "requires_tel_link": False, "requires_bluf": False, "min_mobile_score": 50}

def enrich_with_ai_readiness_targets(topic_name):
    return {"ai_readiness_target": 75, "requires_schema": True, "requires_faq": True, "requires_bluf": True, "min_voice_search_score": 60}

# === ДОБАВЛЕНИЕ ТЕМЫ ===

def add_topic(topic_name, site=None, url=""):
    topics = load_registry()
    
    for existing in topics:
        if existing.get("name", "").lower() == topic_name.lower():
            return {"error": "Тема уже существует: " + topic_name}
    
    topic_id = str(uuid.uuid4())[:8]
    
    if site is None:
        sites = load_sites()
        best_site, score, message = find_best_site_for_topic(topic_name, sites)
        site = best_site
        print("  Автоматически выбран сайт: " + site + " (соответствие: " + str(score) + ")")
        print("  Причина: " + message)
    
    enrichment = {
        "emotional": enrich_with_emotional_targets(topic_name),
        "actionability": enrich_with_actionability_targets(topic_name),
        "authority": enrich_with_authority_sources(topic_name),
        "device": enrich_with_device_priority(topic_name),
        "ai_readiness": enrich_with_ai_readiness_targets(topic_name)
    }
    
    new_topic = {
        "id": topic_id,
        "name": topic_name,
        "site": site,
        "url": url,
        "status": "planned",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "targets": enrichment,
        "actual_scores": {"emotional": None, "actionability": None, "authority": None, "device": None, "ai_readiness": None},
        "quality_gates_passed": False,
        "published_url": None
    }
    
    topics.append(new_topic)
    save_registry(topics)
    
    print("  Тема добавлена: " + topic_name)
    print("  ID: " + topic_id)
    print("  Сайт: " + site)
    print("  Целевой уровень эмпатии: " + enrichment["emotional"]["target_emotional_tier"])
    print("  Требуемые элементы действий: " + str(enrichment["actionability"]["required_actionability_elements"]))
    print("  Приоритет устройств: " + enrichment["device"]["device_priority"])
    print("  Источники авторитетности: " + str(enrichment["authority"]["authority_sources"]))
    
    return new_topic

# === ПРОВЕРКА QUALITY GATES ===

def check_quality_gates(topic_name):
    topics = load_registry()
    topic = None
    for t in topics:
        if t.get("name", "").lower() == topic_name.lower():
            topic = t
            break
    
    if not topic:
        return {"error": "Тема не найдена: " + topic_name}
    
    targets = topic.get("targets", {})
    actual = topic.get("actual_scores", {})
    
    gates = []
    all_passed = True
    
    min_empathy = targets.get("emotional", {}).get("min_empathy_score", 50)
    actual_empathy = actual.get("emotional")
    if actual_empathy is None:
        gates.append({"check": "emotional", "status": "PENDING", "message": "Ещё не проверено"})
        all_passed = False
    elif actual_empathy >= min_empathy:
        gates.append({"check": "emotional", "status": "PASSED", "message": str(actual_empathy) + " >= " + str(min_empathy)})
    else:
        gates.append({"check": "emotional", "status": "FAILED", "message": str(actual_empathy) + " < " + str(min_empathy)})
        all_passed = False
    
    min_action = targets.get("actionability", {}).get("min_actionability_score", 50)
    actual_action = actual.get("actionability")
    if actual_action is None:
        gates.append({"check": "actionability", "status": "PENDING", "message": "Ещё не проверено"})
        all_passed = False
    elif actual_action >= min_action:
        gates.append({"check": "actionability", "status": "PASSED", "message": str(actual_action) + " >= " + str(min_action)})
    else:
        gates.append({"check": "actionability", "status": "FAILED", "message": str(actual_action) + " < " + str(min_action)})
        all_passed = False
    
    min_ai = targets.get("ai_readiness", {}).get("ai_readiness_target", 75)
    actual_ai = actual.get("ai_readiness")
    if actual_ai is None:
        gates.append({"check": "ai_readiness", "status": "PENDING", "message": "Ещё не проверено"})
        all_passed = False
    elif actual_ai >= min_ai:
        gates.append({"check": "ai_readiness", "status": "PASSED", "message": str(actual_ai) + " >= " + str(min_ai)})
    else:
        gates.append({"check": "ai_readiness", "status": "FAILED", "message": str(actual_ai) + " < " + str(min_ai)})
        all_passed = False
    
    topic["quality_gates_passed"] = all_passed
    topic["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_registry(topics)
    
    return {"topic": topic_name, "all_gates_passed": all_passed, "gates": gates, "can_publish": all_passed}

# === СПИСОК ТЕМ ===

def list_topics(status_filter=None):
    topics = load_registry()
    if status_filter:
        topics = [t for t in topics if t.get("status") == status_filter]
    topics = [t for t in topics if t.get("name") is not None]
    return topics

# === ГЛАВНАЯ ФУНКЦИЯ ===

def run_registrar_v2():
    import sys
    print("="*70)
    print(" REGISTRAR v2: RICH METADATA HUB")
    print("="*70)
    print(" Дата: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    args = sys.argv[1:] if len(sys.argv) > 1 else ["demo"]
    command = args[0] if args else "demo"
    
    if command == "add" and len(args) >= 2:
        topic_name = args[1]
        site = args[2] if len(args) > 2 else None
        url = args[3] if len(args) > 3 else ""
        add_topic(topic_name, site, url)
    
    elif command == "check" and len(args) >= 2:
        topic_name = args[1]
        result = check_quality_gates(topic_name)
        if "error" in result:
            print("ERROR: " + result["error"])
        else:
            print("Проверка quality gates: " + result["topic"])
            print("Все гейты пройдены: " + ("ДА" if result["all_gates_passed"] else "НЕТ"))
            print("Можно публиковать: " + ("ДА" if result["can_publish"] else "НЕТ"))
            for gate in result["gates"]:
                icon = {"PASSED": "[+]", "FAILED": "[!]", "PENDING": "[?]"}.get(gate["status"], "[?]")
                print("  " + icon + " " + gate["check"] + ": " + gate["message"])
    
    elif command == "list":
        status = args[1] if len(args) > 1 else None
        topics = list_topics(status)
        print("Тем в реестре: " + str(len(topics)))
        for t in topics:
            status_icon = {"planned": "[P]", "in_progress": "[W]", "published": "[V]"}.get(t.get("status"), "[?]")
            print("  " + status_icon + " " + str(t.get("name")) + " [" + str(t.get("site")) + "] - " + str(t.get("status")))
    
    elif command == "demo":
        print("\n ДЕМО-РЕЖИМ: добавляем тестовые темы (сайт выбирается автоматически)")
        print("="*70)
        
        demo_topics = [
            "Что делать при первых признаках эпилепсии у собаки?",
            "Как помочь кошке при отравлении?",
            "Первая помощь при переломе лапы у собаки",
            "Симптомы и лечение диабета у кошек",
            "Как выбрать корм для щенка?",
            "Паллиативная помощь при онкологии у пожилой собаки"
        ]
        
        for topic in demo_topics:
            print("\nДобавляем: " + topic)
            result = add_topic(topic)
            if "error" in result:
                print("  ОШИБКА: " + result["error"])
        
        print("\n" + "="*70)
        print(" ИТОГОВЫЙ СПИСОК ТЕМ")
        print("="*70)
        topics = list_topics()
        for t in topics:
            tier = t.get("targets", {}).get("emotional", {}).get("target_emotional_tier", "N/A")
            device = t.get("targets", {}).get("device", {}).get("device_priority", "N/A")
            print("  - " + str(t.get("name")))
            print("    Сайт: " + str(t.get("site")) + " | Эмпатия: " + str(tier) + " | Устройства: " + str(device))
        
        print("\nРеестр сохранён: " + str(REGISTRY_FILE))
        print("="*70)
    
    else:
        print("Использование:")
        print("  python registrar_v2.py add 'Тема' [site] [url]")
        print("  python registrar_v2.py check 'Тема'")
        print("  python registrar_v2.py list [status]")
        print("  python registrar_v2.py demo")

if __name__ == "__main__":
    run_registrar_v2()
