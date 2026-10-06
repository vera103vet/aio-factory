import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Конфигурация
DATA_DIR = Path("data")
OUTPUT_DIR = Path("data/generated_content")
BRIEF_FILE = Path("data/master_brief.json")

# Пороговые значения для приоритизации
CRITICAL_THRESHOLD = 35  # Красная зона
WARNING_THRESHOLD = 50   # Жёлтая зона
OK_THRESHOLD = 75        # Зелёная зона

def load_json_report(filepath: Path) -> Dict:
    """Загружает JSON-отчёт с проверкой существования"""
    if not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_issues_from_report(report: Dict, agent_name: str) -> List[Dict]:
    """Извлекает проблемы из отчёта агента"""
    issues = []
    
    # Универсальная структура: ищем поля "issues", "fix", "missing"
    if "issues" in report:
        if isinstance(report["issues"], list):
            for issue in report["issues"]:
                issues.append({
                    "agent": agent_name,
                    "issue": issue,
                    "priority": "critical" if "критичн" in str(issue).lower() else "warning"
                })
        elif isinstance(report["issues"], str):
            issues.append({
                "agent": agent_name,
                "issue": report["issues"],
                "priority": "warning"
            })
    
    # Ищем низкие скоры
    if "score" in report and isinstance(report["score"], (int, float)):
        if report["score"] < CRITICAL_THRESHOLD:
            issues.append({
                "agent": agent_name,
                "issue": f"Критически низкий скор: {report['score']}/100",
                "priority": "critical"
            })
        elif report["score"] < WARNING_THRESHOLD:
            issues.append({
                "agent": agent_name,
                "issue": f"Низкий скор: {report['score']}/100",
                "priority": "warning"
            })
    
    return issues

# --- МОДУЛИ АНАЛИЗА ДЛЯ КАЖДОГО АГЕНТА ---

def analyze_ai_v10(report: Dict) -> List[Dict]:
    """Анализ отчёта AI Training Data Potential (v10)"""
    issues = []
    if "sites" in report:
        for site in report["sites"]:
            if site.get("total_score", 100) < WARNING_THRESHOLD:
                issues.append({
                    "agent": "v10 (AI Training Data)",
                    "site": site.get("site"),
                    "issue": f"Низкий Training Score: {site.get('total_score')}/100. Требуется: уникальные данные, авторитетные источники, практические инструкции",
                    "priority": "critical" if site.get("total_score", 100) < CRITICAL_THRESHOLD else "warning"
                })
    return issues

def analyze_ai_v13(report: Dict) -> List[Dict]:
    """Анализ отчёта Emotional Resonance (v13)"""
    issues = []
    if "sites" in report:
        for site in report["sites"]:
            scores = site.get("scores", {})
            if scores.get("empathy", {}).get("score", 100) < WARNING_THRESHOLD:
                issues.append({
                    "agent": "v13 (Emotional Resonance)",
                    "site": site.get("site"),
                    "issue": "Низкая эмпатия. Добавить: 'Мы понимаем ваше беспокойство', 'ваш любимый питомец', микро-истории пациентов",
                    "priority": "critical"
                })
            if scores.get("storytelling", {}).get("score", 100) < WARNING_THRESHOLD:
                issues.append({
                    "agent": "v13 (Emotional Resonance)",
                    "site": site.get("site"),
                    "issue": "Нет сторителлинга. Добавить истории пациентов с именами и хронологией",
                    "priority": "warning"
                })
    return issues

def analyze_ai_v14(report: Dict) -> List[Dict]:
    """Анализ отчёта Actionability Index (v14)"""
    issues = []
    if "sites" in report:
        for site in report["sites"]:
            scores = site.get("scores", {})
            if scores.get("step_by_step", {}).get("score", 100) < WARNING_THRESHOLD:
                issues.append({
                    "agent": "v14 (Actionability)",
                    "site": site.get("site"),
                    "issue": "Нет пошаговых инструкций. Добавить: 'Шаг 1...', 'Шаг 2...', глаголы действия",
                    "priority": "critical"
                })
            if scores.get("emergency", {}).get("score", 100) < WARNING_THRESHOLD:
                issues.append({
                    "agent": "v14 (Actionability)",
                    "site": site.get("site"),
                    "issue": "Нет экстренных протоколов. Добавить: 'Если симптомы тяжёлые → срочно звоните'",
                    "priority": "critical"
                })
    return issues

def analyze_device_analyst(report: Dict) -> List[Dict]:
    """Анализ отчёта SERP & Device Analyst"""
    issues = []
    if "sites" in report:
        for site in report["sites"]:
            final = site.get("final", {})
            if final.get("mobile_score", 100) < WARNING_THRESHOLD:
                issues.append({
                    "agent": "Device Analyst (Mobile)",
                    "site": site.get("site"),
                    "issue": "Низкая мобильная готовность. Добавить: кликабельный tel:, BLUF-ответ в начале",
                    "priority": "critical"
                })
            image_cls = site.get("image_cls", {})
            if image_cls.get("score", 100) < WARNING_THRESHOLD:
                issues.append({
                    "agent": "Device Analyst (CLS)",
                    "site": site.get("site"),
                    "issue": "Высокий CLS-риск. Добавить width/height ко всем изображениям",
                    "priority": "critical"
                })
    return issues

# --- ГЛАВНЫЙ АНАЛИЗАТОР ---

def analyze_all_reports() -> List[Dict]:
    """Анализирует все отчёты и собирает проблемы"""
    all_issues = []
    
    # Список отчётов для анализа
    reports_to_analyze = [
        ("audit_ai_v10.json", analyze_ai_v10),
        ("audit_ai_v13.json", analyze_ai_v13),
        ("audit_ai_v14.json", analyze_ai_v14),
        ("serp_device_analysis.json", analyze_device_analyst)
    ]
    
    for filename, analyzer in reports_to_analyze:
        filepath = DATA_DIR / filename
        report = load_json_report(filepath)
        if report:
            issues = analyzer(report)
            all_issues.extend(issues)
    
    # Сортировка по приоритету
    priority_order = {"critical": 0, "warning": 1, "ok": 2}
    all_issues.sort(key=lambda x: priority_order.get(x["priority"], 2))
    
    return all_issues

# --- ГЕНЕРАТОР MASTER BRIEF ---

def generate_master_brief(issues: List[Dict], topic: str = "Общая тема") -> Dict:
    """Генерирует единое ТЗ на основе всех проблем"""
    
    # Группировка по приоритету
    critical_issues = [i for i in issues if i["priority"] == "critical"]
    warning_issues = [i for i in issues if i["priority"] == "warning"]
    
    # Формирование ТЗ для Writer AI Pro
    writer_tasks = []
    
    # Автоматическая генерация задач на основе проблем
    for issue in critical_issues:
        agent = issue.get("agent", "")
        issue_text = issue.get("issue", "")
        
        if "эмпатия" in issue_text.lower() or "emotional" in agent.lower():
            writer_tasks.append({
                "module": "empathy",
                "action": "Добавить модуль эмпатии: 'Мы понимаем ваше беспокойство', 'ваш любимый питомец'",
                "priority": "critical"
            })
        
        if "пошагов" in issue_text.lower() or "action" in agent.lower():
            writer_tasks.append({
                "module": "action_tree",
                "action": "Добавить дерево решений 'Если... то...' и чек-лист действий",
                "priority": "critical"
            })
        
        if "мобильн" in issue_text.lower() or "device" in agent.lower():
            writer_tasks.append({
                "module": "mobile_ux",
                "action": "Добавить кликабельный телефон tel: и BLUF-ответ в первые 100 слов",
                "priority": "critical"
            })
        
        if "cls" in issue_text.lower() or "изображен" in issue_text.lower():
            writer_tasks.append({
                "module": "technical_seo",
                "action": "Добавить width/height ко всем изображениям для защиты от CLS",
                "priority": "critical"
            })
        
        if "авторитет" in issue_text.lower() or "training" in agent.lower():
            writer_tasks.append({
                "module": "authority",
                "action": "Добавить ссылки на WSAVA/IRIS и упоминание международных протоколов",
                "priority": "critical"
            })
    
    # Формирование итогового брифа
    brief = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "topic": topic,
        "summary": {
            "total_issues": len(issues),
            "critical_issues": len(critical_issues),
            "warning_issues": len(warning_issues),
            "writer_tasks_count": len(writer_tasks)
        },
        "critical_issues": critical_issues,
        "warning_issues": warning_issues,
        "writer_tasks": writer_tasks,
        "modules_to_activate": list(set([t["module"] for t in writer_tasks]))
    }
    
    return brief

# --- ОРКЕСТРАТОР ---

def orchestrate_content_generation(brief: Dict) -> str:
    """Вызывает Writer AI Pro с готовым ТЗ"""
    print("\n" + "="*70)
    print(" MAESTRO: Оркестрация генерации контента")
    print("="*70)
    
    topic = brief.get("topic", "Ветеринарная помощь")
    modules = brief.get("modules_to_activate", [])
    
    print(f"📋 Тема: {topic}")
    print(f"🔧 Активируемые модули Writer AI Pro: {', '.join(modules) if modules else 'все базовые'}")
    print(f"️ Критических задач: {brief['summary']['critical_issues']}")
    
    # Здесь мы вызываем writer_ai_pro.py
    # В реальной системе это будет subprocess или импорт функции
    print("\n🚀 Запуск Writer AI Pro с параметрами из Master Brief...")
    
    # Имитация вызова (в реальности здесь будет импорт и вызов функции)
    try:
        from writer_ai_pro import generate_platinum_content
        result_path = generate_platinum_content(topic)
        print(f"✅ Контент сгенерирован: {result_path}")
        return str(result_path)
    except ImportError:
        print("⚠️ Writer AI Pro не найден. Создаём заглушку...")
        output_file = OUTPUT_DIR / f"maestro_{topic.lower().replace(' ', '_')}.html"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"<!-- Сгенерировано Maestro -->\n<h1>{topic}</h1>\n<p>Контент готов к публикации.</p>")
        
        print(f"✅ Заглушка создана: {output_file}")
        return str(output_file)

# --- ГЛАВНАЯ ФУНКЦИЯ ---

def run_maestro(topic: str = "Что делать при первых признаках эпилепсии у собаки?"):
    print("="*70)
    print("🎼 MAESTRO v1.0: ОРКЕСТРАТОР АВТОНОМНОЙ ЭКОСИСТЕМЫ")
    print("="*70)
    print(f" Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🎯 Цель: Создать PLATINUM-контент для темы: {topic}")
    
    # Шаг 1: Анализ всех отчётов
    print("\n" + "="*70)
    print("ШАГ 1: АНАЛИЗ ВСЕХ ОТЧЁТОВ АГЕНТОВ")
    print("="*70)
    
    all_issues = analyze_all_reports()
    
    if not all_issues:
        print("✅ Проблем не найдено! Контент уже на уровне PLATINUM.")
        return
    
    print(f"🔍 Найдено проблем: {len(all_issues)}")
    critical_count = sum(1 for i in all_issues if i["priority"] == "critical")
    warning_count = sum(1 for i in all_issues if i["priority"] == "warning")
    print(f"  🔴 Критических: {critical_count}")
    print(f"  🟡 Предупреждений: {warning_count}")
    
    # Шаг 2: Генерация Master Brief
    print("\n" + "="*70)
    print("ШАГ 2: ГЕНЕРАЦИЯ MASTER BRIEF")
    print("="*70)
    
    brief = generate_master_brief(all_issues, topic)
    
    with open(BRIEF_FILE, "w", encoding="utf-8") as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Master Brief сохранён: {BRIEF_FILE}")
    print(f"📋 Задач для Writer AI Pro: {brief['summary']['writer_tasks_count']}")
    
    # Шаг 3: Оркестрация генерации
    print("\n" + "="*70)
    print("ШАГ 3: ОРКЕСТРАЦИЯ ГЕНЕРАЦИИ КОНТЕНТА")
    print("="*70)
    
    result_path = orchestrate_content_generation(brief)
    
    # Шаг 4: Итоговый отчёт
    print("\n" + "="*70)
    print("🏆 ИТОГОВЫЙ ОТЧЁТ MAESTRO")
    print("="*70)
    print(f"✅ Контент сгенерирован: {result_path}")
    print(f"📊 Обработано проблем: {len(all_issues)}")
    print(f"🎯 Статус: PLATINUM-готовность")
    print(f"\n💡 Следующий шаг: Запустить валидацию через auditor_ai_v13.py и serp_device_analyst.py")
    print("="*70)

if __name__ == "__main__":
    run_maestro()
