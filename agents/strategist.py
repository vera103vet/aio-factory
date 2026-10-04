import json
from pathlib import Path

REGISTRY = Path("data/topic_registry.json")

def check_cannibalization(keyword):
    with open(REGISTRY, "r", encoding="utf-8") as f:
        registry = json.load(f)
    
    keyword_lower = keyword.lower()
    for item in registry:
        if item["primary_keyword"].lower() in keyword_lower or keyword_lower in item["primary_keyword"].lower():
            return {
                "conflict": True,
                "existing_topic": item["topic"],
                "assigned_to": item["target_site"],
                "url": item["url"]
            }
    return {"conflict": False, "message": "Тема свободна"}

if __name__ == "__main__":
    test_keyword = input("Введите ключевую фразу для проверки: ")
    result = check_cannibalization(test_keyword)
    print("\nРезультат проверки:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
