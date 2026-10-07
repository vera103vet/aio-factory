import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime

REGISTRY_FILE = Path("data/topic_registry.json")
SITE_MAP_DIR = Path("data/site_maps")

# Шаблоны структуры сайтов по категориям
SITE_TEMPLATES = {
    "palliative": {
        "name": "Достойный уход",
        "description": "Паллиативная помощь и эвтаназия животных",
        "domain": "usyplenie.103vet.by",
        "structure": {
            "level_1": [
                {"name": "Главная", "url": "/", "type": "landing", "priority": 1}
            ],
            "level_2": [
                {"name": "Поддержка собак", "url": "/how-to/podderzhka-sobak/", "type": "hub", "priority": 2},
                {"name": "Поддержка кошек", "url": "/how-to/podderzhka-koshek/", "type": "hub", "priority": 2},
                {"name": "Качество жизни", "url": "/guide/kak-oczenit-kachestvo-zhizni/", "type": "guide", "priority": 2},
                {"name": "Помощь владельцу", "url": "/guide/psixologicheskaya-pomoshch/", "type": "guide", "priority": 2}
            ],
            "level_3_dogs": [
                {"name": "Онкология терминальной стадии у собак", "url": "/how-to/podderzhka-sobak/onkologiya/", "type": "how-to", "priority": 3},
                {"name": "Отказ органов у собак", "url": "/how-to/podderzhka-sobak/otkaz-organov/", "type": "how-to", "priority": 3},
                {"name": "Контроль боли у собак", "url": "/how-to/podderzhka-sobak/kontrol-boli/", "type": "how-to", "priority": 3},
                {"name": "Параличи и обездвиженность", "url": "/how-to/podderzhka-sobak/paralichi/", "type": "how-to", "priority": 3},
                {"name": "Паллиативный уход за собакой", "url": "/how-to/podderzhka-sobak/palliativnyj-uhod/", "type": "how-to", "priority": 3},
                {"name": "Тревожные симптомы у собаки", "url": "/how-to/podderzhka-sobak/simptomy/", "type": "how-to", "priority": 3}
            ],
            "level_3_cats": [
                {"name": "ХБП 4 стадии у кошек", "url": "/how-to/podderzhka-koshek/hbp/", "type": "how-to", "priority": 3},
                {"name": "Гипертиреоз у кошек", "url": "/how-to/podderzhka-koshek/gipertireoz/", "type": "how-to", "priority": 3},
                {"name": "Деменция у кошек", "url": "/how-to/podderzhka-koshek/demenciya/", "type": "how-to", "priority": 3},
                {"name": "Артрит у кошек", "url": "/how-to/podderzhka-koshek/artrit/", "type": "how-to", "priority": 3},
                {"name": "Паллиативный уход за кошкой", "url": "/how-to/podderzhka-koshek/palliativnyj-uhod/", "type": "how-to", "priority": 3},
                {"name": "Тревожные симптомы у кошки", "url": "/how-to/podderzhka-koshek/simptomy/", "type": "how-to", "priority": 3}
            ],
            "level_3_quality": [
                {"name": "Тест качества жизни", "url": "/guide/kak-oczenit-kachestvo-zhizni/test/", "type": "interactive", "priority": 3},
                {"name": "Шкала HHHHHMM", "url": "/guide/kak-oczenit-kachestvo-zhizni/shkala-hhhhhmm/", "type": "guide", "priority": 3},
                {"name": "Дневник наблюдений", "url": "/guide/kak-oczenit-kachestvo-zhizni/dnevnik/", "type": "guide", "priority": 3},
                {"name": "Когда время пришло", "url": "/guide/kak-oczenit-kachestvo-zhizni/kogda-vremya-prishlo/", "type": "guide", "priority": 3},
                {"name": "Протоколы AAHA", "url": "/guide/kak-oczenit-kachestvo-zhizni/protokoly/", "type": "article", "priority": 3}
            ],
            "level_3_owner": [
                {"name": "Как пережить горе", "url": "/guide/psixologicheskaya-pomoshch/gore/", "type": "guide", "priority": 3},
                {"name": "Как объяснить детям", "url": "/guide/psixologicheskaya-pomoshch/deti/", "type": "guide", "priority": 3},
                {"name": "Организация прощания", "url": "/guide/psixologicheskaya-pomoshch/proshchanie/", "type": "guide", "priority": 3},
                {"name": "Память и мемориалы", "url": "/guide/psixologicheskaya-pomoshch/pamyat/", "type": "guide", "priority": 3},
                {"name": "Группы поддержки", "url": "/guide/psixologicheskaya-pomoshch/gruppy-podderzhki/", "type": "guide", "priority": 3}
            ],
            "blog": [
                {"name": "Как понять, что собака страдает", "url": "/blog/kak-ponyat-chto-sobaka-stradaet/", "type": "blog", "priority": 4},
                {"name": "Что делать после эвтаназии", "url": "/blog/chto-delat-posle-eutanazii/", "type": "blog", "priority": 4},
                {"name": "Кремация или похороны", "url": "/blog/kremaciya-ili-pohorony/", "type": "blog", "priority": 4},
                {"name": "Как выбрать ветеринара для эвтаназии", "url": "/blog/kak-vybrat-veterinara/", "type": "blog", "priority": 4},
                {"name": "Признаки боли у животных", "url": "/blog/priznaki-boli-u-zhivotnyh/", "type": "blog", "priority": 4},
                {"name": "Паллиативный уход на дому", "url": "/blog/palliativnyj-uhod-na-domu/", "type": "blog", "priority": 4},
                {"name": "Как поддержать друга, потерявшего питомца", "url": "/blog/kak-podderzhat-druga/", "type": "blog", "priority": 4},
                {"name": "Эвтаназия: мифы и реальность", "url": "/blog/eutanaziya-mify-i-realnost/", "type": "blog", "priority": 4},
                {"name": "Когда паллиативный уход не помогает", "url": "/blog/kogda-palliativnyj-uhod-ne-pomogaet/", "type": "blog", "priority": 4},
                {"name": "Истории владельцев: прощание с любимцем", "url": "/blog/istorii-vladelcev/", "type": "blog", "priority": 4}
            ],
            "service": [
                {"name": "О проекте", "url": "/about/", "type": "service", "priority": 5},
                {"name": "Контакты", "url": "/contacts/", "type": "service", "priority": 5},
                {"name": "Частые вопросы", "url": "/faq/", "type": "service", "priority": 5},
                {"name": "Политика конфиденциальности", "url": "/privacy/", "type": "service", "priority": 5},
                {"name": "Условия использования", "url": "/terms/", "type": "service", "priority": 5}
            ]
        }
    },
    "neurology": {
        "name": "Неврология животных",
        "description": "Эпилепсия, судороги, неврологические заболевания",
        "domain": "nevro.103vet.by",
        "structure": {
            "level_1": [
                {"name": "Главная", "url": "/", "type": "landing", "priority": 1}
            ],
            "level_2": [
                {"name": "Эпилепсия", "url": "/guide/epilepsiya/", "type": "guide", "priority": 2},
                {"name": "Судороги", "url": "/guide/sudorogi/", "type": "guide", "priority": 2},
                {"name": "Диагностика", "url": "/guide/diagnostika/", "type": "guide", "priority": 2},
                {"name": "Лечение", "url": "/guide/lechenie/", "type": "guide", "priority": 2}
            ],
            "level_3_epilepsy": [
                {"name": "Первые признаки эпилепсии", "url": "/guide/epilepsiya/pervye-priznaki/", "type": "how-to", "priority": 3},
                {"name": "Что делать при приступе", "url": "/guide/epilepsiya/chto-delat-pri-pristupe/", "type": "how-to", "priority": 3},
                {"name": "Дневник приступов", "url": "/guide/epilepsiya/dnevnik-pristupov/", "type": "guide", "priority": 3},
                {"name": "Противосудорожные препараты", "url": "/guide/epilepsiya/preparaty/", "type": "article", "priority": 3},
                {"name": "Эпилепсия у собак", "url": "/guide/epilepsiya/u-sobak/", "type": "article", "priority": 3},
                {"name": "Эпилепсия у кошек", "url": "/guide/epilepsiya/u-koshek/", "type": "article", "priority": 3}
            ],
            "level_3_seizures": [
                {"name": "Виды судорог", "url": "/guide/sudorogi/vidy/", "type": "article", "priority": 3},
                {"name": "Судороги у щенков", "url": "/guide/sudorogi/u-shchenkov/", "type": "article", "priority": 3},
                {"name": "Судороги у котят", "url": "/guide/sudorogi/u-kotyat/", "type": "article", "priority": 3},
                {"name": "Отравление и судороги", "url": "/guide/sudorogi/otravlenie/", "type": "article", "priority": 3},
                {"name": "Тепловой удар", "url": "/guide/sudorogi/teplovoj-udar/", "type": "article", "priority": 3}
            ],
            "blog": [
                {"name": "Мифы об эпилепсии", "url": "/blog/mify-ob-epilepsii/", "type": "blog", "priority": 4},
                {"name": "Жизнь с эпилептиком", "url": "/blog/zhizn-s-epileptikom/", "type": "blog", "priority": 4},
                {"name": "Новые методы лечения", "url": "/blog/novye-metody-lecheniya/", "type": "blog", "priority": 4},
                {"name": "Истории выздоровления", "url": "/blog/istorii-vyzdorovleniya/", "type": "blog", "priority": 4},
                {"name": "Как снять приступ на видео", "url": "/blog/kak-snyat-pristup/", "type": "blog", "priority": 4}
            ],
            "service": [
                {"name": "О проекте", "url": "/about/", "type": "service", "priority": 5},
                {"name": "Контакты", "url": "/contacts/", "type": "service", "priority": 5},
                {"name": "FAQ", "url": "/faq/", "type": "service", "priority": 5}
            ]
        }
    }
}

def generate_site_map(template_key: str) -> Dict:
    """Генерирует полную карту сайта из шаблона"""
    template = SITE_TEMPLATES.get(template_key)
    if not template:
        print(f"Шаблон '{template_key}' не найден. Доступные: {list(SITE_TEMPLATES.keys())}")
        return None
    
    site_map = {
        "site_name": template["name"],
        "description": template["description"],
        "domain": template["domain"],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_pages": 0,
        "pages": []
    }
    
    # Собираем все страницы из структуры
    structure = template["structure"]
    
    for level_key, pages in structure.items():
        for page in pages:
            site_map["pages"].append({
                "name": page["name"],
                "url": page["url"],
                "type": page["type"],
                "priority": page["priority"],
                "section": level_key,
                "status": "pending"
            })
    
    site_map["total_pages"] = len(site_map["pages"])
    
    # Сортируем по приоритету
    site_map["pages"].sort(key=lambda x: (x["priority"], x["url"]))
    
    return site_map

def save_site_map(site_map: Dict, template_key: str):
    """Сохраняет карту сайта в JSON"""
    SITE_MAP_DIR.mkdir(parents=True, exist_ok=True)
    filepath = SITE_MAP_DIR / f"{template_key}_site_map.json"
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(site_map, f, ensure_ascii=False, indent=2)
    
    print(f"Карта сайта сохранена: {filepath}")
    return filepath

def print_site_summary(site_map: Dict):
    """Выводит сводку по карте сайта"""
    print("\n" + "="*70)
    print("SITE ARCHITECT: КАРТА САЙТА СГЕНЕРИРОВАНА")
    print("="*70)
    print(f"Сайт: {site_map['site_name']}")
    print(f"Домен: {site_map['domain']}")
    print(f"Всего страниц: {site_map['total_pages']}")
    print("-"*70)
    
    # Группируем по секциям
    sections = {}
    for page in site_map["pages"]:
        section = page["section"]
        if section not in sections:
            sections[section] = []
        sections[section].append(page)
    
    for section, pages in sections.items():
        print(f"\n{section.upper()} ({len(pages)} страниц):")
        for page in pages:
            priority_icon = {1: "🏠", 2: "📂", 3: "📄", 4: "", 5: "⚙️"}.get(page["priority"], "📄")
            print(f"  {priority_icon} {page['url']} — {page['name']}")
    
    print("\n" + "="*70)

def main():
    print("="*70)
    print("SITE ARCHITECT v1.0: ГЕНЕРАЦИЯ КАРТЫ САЙТА")
    print("="*70)
    print("Дата: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print()
    
    # Генерируем карту для "Достойный уход"
    template_key = "palliative"
    print(f"Генерируем карту сайта для шаблона: {template_key}\n")
    
    site_map = generate_site_map(template_key)
    
    if site_map:
        print_site_summary(site_map)
        filepath = save_site_map(site_map, template_key)
        print(f"\n✅ Карта сайта готова к передаче в Maestro v2!")
        print(f"Следующий шаг: python agents/maestro_v2.py --site-map={filepath}")
    
    print("="*70)

if __name__ == "__main__":
    main()
