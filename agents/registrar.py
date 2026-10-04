import json
from pathlib import Path

REGISTRY = Path("data/topic_registry.json")

def add_topic(topic, keyword, target_site, url):
    with open(REGISTRY, "r", encoding="utf-8") as f:
        registry = json.load(f)
    
    new_id = max([item["id"] for item in registry]) + 1 if registry else 1
    
    new_topic = {
        "id": new_id,
        "topic": topic,
        "primary_keyword": keyword,
        "target_site": target_site,
        "url": url,
        "status": "planned"
    }
    
    registry.append(new_topic)
    
    with open(REGISTRY, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    return new_topic

if __name__ == "__main__":
    topic = input("Тема: ")
    keyword = input("Ключевая фраза: ")
    target_site = input("Сайт (main/nevrolog/usyplenie/vetminsk): ")
    url = input("URL: ")
    
    result = add_topic(topic, keyword, target_site, url)
    print("\nТема добавлена в реестр:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
